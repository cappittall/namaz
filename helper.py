import logging
import math
import time
import cv2
import pygame
import numpy as np

from tools.constant_settings import * 

from mediapipe.framework.formats import landmark_pb2
from mediapipe import solutions
import mediapipe as mp
import threading
from concurrent.futures import ThreadPoolExecutor
thread_pool = ThreadPoolExecutor(max_workers=10)

        
# Kade treshold
pygame.init()

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
    if not all([is_reliable_landmark(landmarks[l]) for l in [21, 22, 23, 24, 25, 26, 27, 28 ]]):
        return False
    
    st_dev1 = are_aligned_vertically(landmarks[27], landmarks[25], landmarks[23])
    st_dev2 = are_aligned_vertically(landmarks[28], landmarks[26], landmarks[24])
    st_dev = (st_dev1 + st_dev2) / 2.0 
    
    is_standing_l = landmarks[23].y < landmarks[25].y < landmarks[27].y
    is_standing_r = landmarks[24].y < landmarks[26].y < landmarks[28].y
    
    if st_dev <= thresholds_xs and is_standing_l and is_standing_r:
        return True
    
    return False


def is_niyet(image, landmarks, gender="k"):
    
    # calculate hands are under bell
    left_hand_under_bell = landmarks[19].y > landmarks[23].y
    right_hand_under_bell = landmarks[20].y > landmarks[24].y
    
    return left_hand_under_bell and right_hand_under_bell

def is_tekbir(image, landmarks, gender="k"):
   
    # Check if landmarks are reliable. Done above: [21, 22, 23, 24, 25, 26, 27, 28] 
    if not all([is_reliable_landmark(landmarks[l]) for l in [7, 8, 11, 12 ]]):
        return False
    
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
    
    is_distance_to_tekbir = distance_left < thresholds_s and  distance_right < thresholds_s
    is_distance_between_hands = distance_between_hands > thresholds_m
    is_left_right_not_crosed = landmarks[20].x  <  landmarks[19].x
    
    _is_tekbir = is_distance_to_tekbir and is_distance_between_hands and is_left_right_not_crosed
    
    inspections['Tekbir'] = _is_tekbir
    inspections['x'] = is_left_right_not_crosed 
    inspections['d_lt'] = str(distance_left)[:5] ## left to target
    inspections['d_rt'] = str(distance_right)[:5] ## right to target 
    inspections['d_lr'] = str(distance_between_hands)[:5] ## left to right 

    if _is_tekbir:
        print('Tekbir ',  inspections )
        # threading.Thread(target=write_inspection_on_image, args=(image, inspections, ) ).start()
        thread_pool.submit(write_inspection_on_image, image, inspections)
        return True

    return False

def is_kiyam(image, landmarks, gender='k' ):    
    
    # Check if landmarks are reliable. Done above = [21, 22, 23, 24, 25, 26, 27, 28] 
    if not all([is_reliable_landmark(landmarks[l]) for l in [11, 12, 19, 20]]):
        return False
             
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
        print('Kıyam ',  inspections )
        # threading.Thread(target=write_inspection_on_image, args=(image, inspections, ) ).start()
        thread_pool.submit(write_inspection_on_image, image, inspections)
        
        return True
    
    return False

def is_ruku(image, landmarks, gender="k"):
    inspections = {}
    
    # Check if landmarks are reliable. Done above = [23, 24, 25, 26, 27, 28] 
    if not all([is_reliable_landmark(landmarks[l]) for l in [11, 12, 15, 16]]):
        return False

    # mid points of sholder and hips
    mid_spine_y = (landmarks[11].y + landmarks[12].y) / 2   
    
    # check mouth below solderline
    distance_noise_spine = landmarks[0].y - mid_spine_y

    # calculate hands are under bell
    is_hands_under_bell = landmarks[15].y > landmarks[23].y and landmarks[16].y > landmarks[24].y
    is_distance_noise_spine = landmarks[0].y >= mid_spine_y
            
    # Check alignment of spine, hips, knees, and ankles to ensure a bowing posture    
    inspections['noso_to_spine'] = is_distance_noise_spine
    inspections['hans_U'] = is_hands_under_bell
    inspections['dt_nose_spn'] = str(distance_noise_spine)[:5]
       
    if is_distance_noise_spine and is_hands_under_bell:
        print('Ruku ',  inspections )
        # threading.Thread(target=write_inspection_on_image, args=(image, inspections, ) ).start()
        thread_pool.submit(write_inspection_on_image, image, inspections)
        return True
    
    return False

def is_secde(image, landmarks, gender="k"):
    inspections = {}
    # Check if landmarks are reliable
    if not all([is_reliable_landmark(landmarks[l]) for l in [0,15,16, 23, 24, 25,26, 27,28 ] ]):
        return False
    
    nose_y = landmarks[0].y
    left_wrist_y = landmarks[15].y
    right_wrist_y = landmarks[16].y
    left_knee_y = landmarks[25].y
    right_knee_y = landmarks[26].y
    left_ankle_y = landmarks[27].y
    right_ankle_y = landmarks[28].y
    
    left_hip_y = landmarks[23].y
    right_hip_y = landmarks[24].y
    
    left_check = left_hip_y <= nose_y and left_hip_y <= left_wrist_y \
        and left_hip_y <= left_knee_y and left_hip_y <= left_ankle_y 
        
    right_check = right_hip_y<= nose_y and right_hip_y <= right_wrist_y \
        and right_hip_y <= right_knee_y and right_hip_y <= right_ankle_y  
        
    final_check = left_check or right_check
    
    inspections['Secde'] = final_check
    inspections['hips, '] = str(left_hip_y)[:5] 
    inspections['Nose'] = str(nose_y)[:5] 
    inspections['el'] = str(left_wrist_y)[:5] 
    inspections['Diz'] = str(left_knee_y)[:5] 
    inspections['Ayak'] = str(left_ankle_y)[:5] 
    
    print('Secde ',  inspections )
    if final_check:
        print('Secde ',  inspections )
        # threading.Thread(target=write_inspection_on_image, args=(image, inspections, ) ).start()
        thread_pool.submit(write_inspection_on_image, image, inspections)
        
        return True
    
    return False

def is_kade(image, landmarks, gender="k"):
    
    inspections = {}
    # Check if landmarks are reliable
    if not all([is_reliable_landmark(landmarks[l]) for l in [0,15,16, 23, 24, 25,26, 27,28 ] ]):
        return False
    
    left_hip_to_ankle = calculate_distance(landmarks[23], landmarks[27]) 
    right_hip_to_ankle = calculate_distance(landmarks[24], landmarks[28])
    
    left_hand_to_knee = calculate_distance(landmarks[19], landmarks[25])
    right_hand_to_knee = calculate_distance(landmarks[20], landmarks[26])
        
    
    # Check hips, sholders and ears are vertical
    is_vertical = landmarks[0].y < landmarks[12].y < landmarks[24].y < landmarks[28].y
    is_hips_to_ankles = left_hip_to_ankle < thresholds_s and right_hip_to_ankle < thresholds_s
    is_hands_on_knees =  left_hand_to_knee < thresholds_s and right_hand_to_knee < thresholds_s
                            
    is_kade_pos = is_vertical and is_hips_to_ankles and is_hands_on_knees
    
    
    inspections['Kade'] = is_kade_pos
    inspections['hipL'] = str(left_hip_to_ankle)[:5] # Hips Ankles 
    inspections['hipR'] = str(right_hip_to_ankle)[:5] # Hips Ankles 
    inspections['HandL'] = str(left_hand_to_knee)[:5] # Left hand on knee
    inspections['HandR']= str(right_hand_to_knee)[:5] # Right hand on knee
    inspections['kr']= is_vertical # Vertical
    
    print('Kade ',  inspections )
    if is_kade_pos:
        # threading.Thread(target=write_inspection_on_image, args=(image, inspections, ) ).start()
        thread_pool.submit(write_inspection_on_image, image, inspections)
        return True
    
    return False
    

def check_position(image, landmarks, gender):
        
    if is_strait(landmarks):
        
        if is_tekbir(image, landmarks, gender):
            return PrayerPositions.TEKBIR
        
        elif is_kiyam(image, landmarks, gender):
            return PrayerPositions.KIYAM
        
        elif is_ruku(image, landmarks, gender):
            return PrayerPositions.RUKU
    
        elif is_niyet(image, landmarks, gender):
            return PrayerPositions.NIYET
        
        else: 
            return None
        
    else:

        if is_secde(image, landmarks, gender):
            return PrayerPositions.SECDE
        elif is_kade(image, landmarks, gender):
            return PrayerPositions.KADE
        else:
            return None
        
