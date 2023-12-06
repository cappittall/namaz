import os
import logging
import math
import time
import cv2
import numpy as np
from .constant_settings import * 

from mediapipe.framework.formats import landmark_pb2
from mediapipe import solutions
import mediapipe as mp
import threading
# Labels corresponding to the output of your model, assumed to be in order
labels = ['kade', 'kiyam', 'ruku', 'secde']

DEBUG=True

def clear_directory(folder_path):
    try:
        for filename in os.listdir(folder_path):
            file_path = os.path.join(folder_path, filename)
            try:
                if os.path.isfile(file_path):
                    os.unlink(file_path)
                elif os.path.isdir(file_path):
                    os.rmdir(file_path)
            except Exception as e:
                print(f"Failed to delete {file_path}. Reason: {e}")
    except Exception as e:
        print(f"Failed to delete Reason: {e}")
def draw_landmarks_on_image(rgb_image, detection_result ):
        
    pose_landmarks_list = detection_result.pose_landmarks
    annotated_image = np.copy(rgb_image)

    # Loop through the detected poses to visualize.
    for idx in range(len(pose_landmarks_list)):
        pose_landmarks = pose_landmarks_list[idx]

        # Draw the pose landmarks.
        pose_landmarks_proto = landmark_pb2.NormalizedLandmarkList()
        pose_landmarks_proto.landmark.extend([
            landmark_pb2.NormalizedLandmark(x=landmark.x, y=landmark.y, z=landmark.z) for landmark in pose_landmarks
        ])
        solutions.drawing_utils.draw_landmarks(
            annotated_image,
            pose_landmarks_proto,
            solutions.pose.POSE_CONNECTIONS,
            solutions.drawing_styles.get_default_pose_landmarks_style())
    return annotated_image


def get_landmarks_infrance(img, landmarker):
    # COnvert to model image format.
    mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=img)
    try: 
        # try detection if not return as face not recognized
        landmarks = landmarker.detect(mp_image)  
    except Exception as e:
        logging.error('Error in get_landmarks_infrance: %s', e)
        return None
    return landmarks

def get_bounding_box(landmarks, img):
    margin_ratio_x = 0.5
    margin_ratio_y = 0.5
    
    x_coords = [landmark.x for landmark in landmarks]
    y_coords = [landmark.y for landmark in landmarks]
    
    x_min, x_max, y_min, y_max = min(x_coords), max(x_coords), min(y_coords), max(y_coords)

    
    h,w,_ = img.shape 
    x_min, y_min, x_max, y_max = int(x_min * w), int(y_min * h),int(x_max * w), int(y_max* h)
                                                
    margin_x = int((x_max - x_min) * margin_ratio_x)
    margin_y = int((y_max - y_min) * margin_ratio_y)
    # Make sure the margins do not exceed the image dimensions
    x_min = max(0, x_min - margin_x)
    y_min = max(0, y_min - margin_y)
    x_max = min(w, x_max + margin_x)
    y_max = min(h, y_max + margin_y)
            
    return (x_min, y_min, x_max, y_max)

def get_class_of_position_fp32(image, interpreter, input_details, output_details):
    # This part remains the same
    input_size = tuple(input_details[0]['shape'][1:3])
    
    img_array = np.array(image)

    # Resize and normalize image if needed
    img_array = cv2.resize(img_array, input_size)
    img_array = img_array.astype(np.float32) / 255.0

    # Add a batch dimension
    img_array = np.expand_dims(img_array, axis=0)

    # Set input tensor
    interpreter.set_tensor(input_details[0]['index'], img_array)

    # Invoke model
    interpreter.invoke()

    # Get output tensor
    output_data = interpreter.get_tensor(output_details[0]['index'])
    confidence = np.max(output_data)   

    # Determine label
    label = labels[np.argmax(output_data)]
    
    return label, confidence


def get_class_of_position_int8(image, interpreter, input_details, output_details):   
    # This part remains the same
    input_size = tuple(input_details[0]['shape'][1:3])
    
    img_array = np.array(image)
    
    img_array = cv2.resize(img_array, input_size)
    

    scale, zero_point = input_details[0]['quantization']
    img_array = np.uint8(img_array / scale + zero_point)
    img_array = np.expand_dims(img_array, axis=0)

    # Set input tensor
    interpreter.set_tensor(input_details[0]['index'], img_array)

    # Invoke model
    interpreter.invoke()

    # Get output tensor
    output_data = interpreter.get_tensor(output_details[0]['index'])    

    # Dequantize the output data
    output_scale, output_zero_point = output_details[0]['quantization']
    output_data = (output_data - output_zero_point) * output_scale

    confidence = np.max(output_data)    
    # Determine label
    label = labels[np.argmax(output_data)]
        
    return label, confidence

    
def are_aligned_vertically(*args):
    x_coordinates = [point.x for point in args]
    std_dev = np.std(x_coordinates)
    return std_dev

def are_aligned_horizontally(*args):
    y_coordinates = [point.y for point in args]
    std_dev = np.std(y_coordinates)
    return std_dev

def write_inspection_on_image(image, args): 
    try:
        text_arr = [f'{key} : {val}' for key, val in args.items()]
        text = ', '.join(text_arr)
        cv2.putText(image, text, (10,10), cv2.FONT_HERSHEY_PLAIN, 1, (0, 0, 255), 1)
        cv2.imwrite(f'data/inspect/f{int(time.monotonic() * 1000)}.jpg', image)
    except Exception as e:
        logging.error('Error in write_inspection_on_image: %s', e)
    
# Add this class at the top of your helper.py
class Point:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        
# Calculate distance between two landmarks
def calculate_distance(landmark1, landmark2):
    return math.sqrt((landmark1.x - landmark2.x)**2 + (landmark1.y - landmark2.y)**2)

def is_reliable_landmark(landmark, min_visibility=0.20 ):
    return landmark.visibility >= min_visibility

def is_strait(landmarks):
    if not all([is_reliable_landmark(landmarks[l]) for l in [23, 24, 25, 26, 27, 28 ]]):
        return None
    
    st_dev1 = are_aligned_vertically(landmarks[27], landmarks[25], landmarks[23])
    st_dev2 = are_aligned_vertically(landmarks[28], landmarks[26], landmarks[24])
    st_dev = (st_dev1 + st_dev2) / 2.0 
    
    is_standing_l =  landmarks[23].y < landmarks[25].y < landmarks[27].y
    is_standing_r =  landmarks[24].y < landmarks[26].y < landmarks[28].y
    
    if st_dev <= thresholds_xs and is_standing_l and is_standing_r:
        return True
    
    return False


def is_niyet(image, landmarks, gender="k"):
    # check the landmarks reliable  checked already [23, 24, 25, 26, 27, 28 ]
    if not all([is_reliable_landmark(landmarks[l]) for l in [19,20]]):
        return None
    
    # calculate hands are under bell
    left_hand_under_bell = landmarks[19].y > landmarks[23].y
    right_hand_under_bell = landmarks[20].y > landmarks[24].y
    
    return left_hand_under_bell and right_hand_under_bell

def is_tekbir(image, landmarks, gender="k"):
   
    # Check if landmarks are reliable. checked already [23, 24, 25, 26, 27, 28 ] 
    if not all([is_reliable_landmark(landmarks[l]) for l in [7, 8, 11, 12, 19, 20, 21, 22]]):
        return None
    
    inspections = {}
    if gender=="k":
        # distane hands to sholders for women
        distance_left = calculate_distance(landmarks[21], landmarks[11]) 
        distance_right = calculate_distance(landmarks[22], landmarks[12])  
    else: 
        # distance hands to ears for mens
        distance_left = calculate_distance(landmarks[21], landmarks[7])  
        distance_right = calculate_distance(landmarks[22], landmarks[8]) 
        
        # distance left wrist to referance position (for women chest area, for men stomach)
    distance_between_hands = calculate_distance(landmarks[21], landmarks[22])
    
    is_distance_to_tekbir = distance_left < thresholds_xl and  distance_right < thresholds_xl
    is_distance_between_hands = distance_between_hands > thresholds_m
    is_left_right_not_crosed = landmarks[20].x  <  landmarks[19].x
    
    _is_tekbir = is_distance_to_tekbir and is_distance_between_hands and is_left_right_not_crosed
    
    inspections['Tekbir'] = _is_tekbir
    inspections['x'] = is_left_right_not_crosed 
    inspections['d_lt'] = str(distance_left)[:5] ## left to target
    inspections['d_rt'] = str(distance_right)[:5] ## right to target 
    inspections['d_lr'] = str(distance_between_hands)[:5] ## left to right 

    if _is_tekbir:
        # print('Tekbir ',  inspections )
        # threading.Thread(target=write_inspection_on_image, args=(image, inspections, ) ).start()
        # thread_pool.submit(write_inspection_on_image, image, inspections)
        return True

    return False

def is_kiyam(image, landmarks, gender='k' ):    
    
    # Check if landmarks are reliable. checked already [23, 24, 25, 26, 27, 28 ] 
    if not all([is_reliable_landmark(landmarks[l]) for l in [11, 12, 19, 20, 21, 22]]):
        return None
             
    inspections = {}
    # Estimate chest and stomach Y positions 
    chest_position_y = (landmarks[11].y + landmarks[12].y) / 2  
    stomach_position_y = (landmarks[23].y + landmarks[24].y) / 2 
    differece_y = stomach_position_y - chest_position_y
    
    if gender == "k":
        # ref posizion near chest for woman
        ref_position = Point((landmarks[11].x + landmarks[12].x) / 2 , 
                             chest_position_y +  differece_y /3)
    else:
        # ref position over stomach for mens.
        ref_position = Point((landmarks[23].x + landmarks[24].x) / 2, 
                             stomach_position_y - differece_y/3 ) 
    
    # distance left wrist to referance position (for women chest area, for men stomach)
    distance_between_hands = calculate_distance(landmarks[19], landmarks[20]) 
    distance_to_ref_position = calculate_distance(landmarks[20], ref_position )
        
    is_distance_between_hands = distance_between_hands <= thresholds_m
    is_distance_to_ref_position = distance_to_ref_position  <= thresholds_m
    
    
    # check hands are over bell:
    hands_over_bell = landmarks[21].y < landmarks[23].y  and landmarks[22].y < landmarks[24].y

    _is_kiyam = is_distance_between_hands and is_distance_to_ref_position \
                and  hands_over_bell 

    inspections['Kiyam'] = _is_kiyam
    inspections['d_hands'] = str(distance_between_hands)[:5]
    inspections['d_ref'] = str(distance_to_ref_position)[:5]
    
    if _is_kiyam:
        # print('Kıyam ',  inspections )
        # threading.Thread(target=write_inspection_on_image, args=(image, inspections, ) ).start()
        # thread_pool.submit(write_inspection_on_image, image, inspections)
        
        return True
    
    return False

def is_ruku(image, landmarks, gender="k"):
    inspections = {}
    
    # Check if landmarks are reliable. checked already [23, 24, 25, 26, 27, 28 ] 
    if not all([is_reliable_landmark(landmarks[l]) for l in [0, 11, 12, 15, 16]]):
        return None

    # mid points of sholder and hips
    mid_spine_y = (landmarks[11].y + landmarks[12].y) / 2   
    
    # check mouth below sholderline
    distance_noise_spine = landmarks[0].y - mid_spine_y

    # calculate hands are under bell
    is_hands_under_bell = landmarks[15].y > landmarks[23].y and landmarks[16].y > landmarks[24].y
    is_distance_noise_spine = landmarks[0].y >= mid_spine_y - thresholds_s
            
    # Check alignment of spine, hips, knees, and ankles to ensure a bowing posture
    inspections['Ruku'] = is_distance_noise_spine
    inspections['dist'] = distance_noise_spine
    inspections['hans_U'] = is_hands_under_bell
    inspections['dtns'] = str(distance_noise_spine)[:5]
       
    if is_distance_noise_spine and is_hands_under_bell:
        # print('Ruku ',  inspections )
        # threading.Thread(target=write_inspection_on_image, args=(image, inspections, ) ).start()
        # thread_pool.submit(write_inspection_on_image, image, inspections)
        return True
    
    return False


def is_kade(image, landmarks, gender="k"):
    
    inspections = {}
    # Check if landmarks are reliable
    if not all([is_reliable_landmark(landmarks[l]) for l in [0,11, 12, 15,16, 19,20, 23, 24, 25, 26, 27, 28 ] ]):
        return None
    
    nose_y = landmarks[0].y
    wrists_y = (landmarks[15].y + landmarks[16].y) /2
    knees_y = (landmarks[25].y + landmarks[26].y) /2

    ankles_y = (landmarks[27].y + landmarks[28].y) /2
    sholders_y = (landmarks[11].y + landmarks[12].y) /2
 
    
    hips_y = (landmarks[23].y +landmarks[24].y ) /2 
    
    left_hips_to_ankle = calculate_distance(landmarks[23], landmarks[27]) 
    right_hip_to_ankle = calculate_distance(landmarks[24], landmarks[28])
    hips_to_ankles = (left_hips_to_ankle + right_hip_to_ankle) / 2 
    
    left_hand_to_knee = calculate_distance(landmarks[19], landmarks[25])
    right_hand_to_knee = calculate_distance(landmarks[20], landmarks[26])
        
    
    # Check hips, sholders and ears are vertical
    is_vertical = nose_y < sholders_y < hips_y < ankles_y
                    
                    
    # check ankles are close to hips
    is_hips_to_ankles = hips_to_ankles < thresholds_l 
    
    # check hands are on knees
    is_hands_on_knees =  left_hand_to_knee < thresholds_l and right_hand_to_knee < thresholds_l
                            
    is_kade_pos = is_vertical and is_hips_to_ankles and is_hands_on_knees
    
    
    inspections['Kade'] = is_kade_pos
    inspections['hps_anks'] = str(hips_to_ankles)[:5] # Hips Ankles 
    inspections['HandL'] = str(left_hand_to_knee)[:5] # Left hand on knee
    inspections['HandR']= str(right_hand_to_knee)[:5] # Right hand on knee
    inspections['kr']= is_vertical # Vertical
    
    
    if is_kade_pos:
        # print('Kade ',  inspections )
        # threading.Thread(target=write_inspection_on_image, args=(image, inspections, ) ).start()
        # thread_pool.submit(write_inspection_on_image, image, inspections)
        return True
    
    return False

def is_secde(image, landmarks, gender="k"):
    inspections = {}
    # Check if landmarks are reliable 
    if not all([is_reliable_landmark(landmarks[l]) for l in [0,15,16, 23, 24, 25,26, 27,28 ] ]):
        return None
    
    nose_y = landmarks[0].y
    wrists_y = (landmarks[15].y + landmarks[16].y) / 2
    wrists_x = (landmarks[15].x + landmarks[16].x) / 2
    knees_y = (landmarks[25].y + landmarks[26].y) / 2
    ankles_y = (landmarks[27].y + landmarks[28].y) / 2
    sholders_y = (landmarks[11].y + landmarks[12].y) / 2
    hips_y = (landmarks[23].y +landmarks[24].y ) / 2 

   
    # whether if left & right ear close to hand and  is below sholders 
    
    l_ear_to_left_hand = calculate_distance(landmarks[7], landmarks[19] )
    r_ear_to_right_hand = calculate_distance(landmarks[8], landmarks[20] )
    ears_to_hands = (l_ear_to_left_hand + r_ear_to_right_hand) / 2
    
    final_check = sholders_y >= hips_y or ears_to_hands <= thresholds_l
    
    inspections['Secde'] = final_check
    inspections['hips, '] = str(hips_y)[:5] 
    inspections['Nose'] = str(nose_y)[:5] 
    inspections['el'] = str(wrists_y)[:5] 
    inspections['Diz'] = str(knees_y)[:5] 
    inspections['Ayak'] = str(ankles_y)[:5] 
        
    # print('Secde ',  inspections )

    if final_check:
        threading.Thread(target=write_inspection_on_image, args=(image, inspections, ) ).start()
        # thread_pool.submit(write_inspection_on_image, image, inspections)
        return True
    return False  

def check_position(image, landmarks, gender):
        
    if is_strait(landmarks):
        
        if is_tekbir(image, landmarks, gender):
            return PrayerPositions.TEKBIR, True
        
        elif is_kiyam(image, landmarks, gender):
            return PrayerPositions.KIYAM, True
        
        elif is_ruku(image, landmarks, gender):
            return PrayerPositions.RUKU, True
    
        elif is_niyet(image, landmarks, gender):
            return PrayerPositions.NIYET, True
        else: 
            return None, True
        
    else:
        if is_kade(image, landmarks, gender):
            return PrayerPositions.KADE, False
        
        elif is_secde(image, landmarks, gender):
            return PrayerPositions.SECDE, False

        else:
            return None, False
        

def preprocess_image(image_path, target_size=(224, 224)):
    # Read the image from the path
    image = cv2.imread(image_path)
    
    # Resize the image
    image = cv2.resize(image, target_size)
    
    # Convert BGR image to RGB
    image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    
    # Normalize the image pixels
    image = image / 255.0
    
    return image

def check_cameras(max_range=11):
    available_cams = []
    for i in range(max_range):
        cap = cv2.VideoCapture(i)
        if cap.isOpened():
            available_cams.append(i)
        cap.release()
    print(f'Uygun kamera num: {available_cams}')
    return available_cams

def compare_positions(position1, position2):
    kiyam_poss = (PrayerPositions.KIYAM, PrayerPositions.KIYAM2, PrayerPositions.KIYAM3 )
    kade_poss = (PrayerPositions.KADE, PrayerPositions.KADE2, PrayerPositions.KADE3, PrayerPositions.KADE_S)
    niyet_poss = (PrayerPositions.NIYET, PrayerPositions.NIYET_S)
    
    if position1 == position2:
        return True
    if position1 in kiyam_poss and  position2 in kiyam_poss:
        return True
    if position1 in kade_poss and position2 in kade_poss:
        return True
    if position1 in niyet_poss and position2 in niyet_poss:
        return True
    return False


def load_squences(prayer_time):
    sequences = {
        'Sabah': (sabah_namazi_2, sabah_dualari, sabah_manazi_soundline),
        'Öğle': (oglen_namazi_4, oglen_dualari, sabah_manazi_soundline), 
        'İkindi': (ikindi_namazi_4, ikindi_dualari, sabah_manazi_soundline),
        'Akşam': (aksam_namazi_3, aksam_dualari, sabah_manazi_soundline),
        'Yatsı': (yatsi_namazi_4, yatsi_dualari, sabah_manazi_soundline)
    }

    current_sequence, current_prayer_sounds, timeline = sequences.get(
                                prayer_time, (None, None, None))
    
    return current_sequence, current_prayer_sounds, timeline

