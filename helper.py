import math
import pygame
import numpy as np

from tools.constant_settings import * 

from mediapipe.framework.formats import landmark_pb2
from mediapipe import solutions
import mediapipe as mp
 


        
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
    except:
        return None
    return landmarks

# Choose the threshold based on gender
def get_threshold(gender, pose):
    if gender == "k":
        return thresholds_women[pose]
    else:
        return thresholds_men[pose]
    
def are_aligned_vertically(gender, *args):
    y_coordinates = [point.y for point in args]
    std_dev = np.std(y_coordinates)
    return std_dev < get_threshold(gender, 'alignment_threshold')

# Add this class at the top of your helper.py
class Point:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        
# Calculate distance between two landmarks
def calculate_distance(landmark1, landmark2):
    return math.sqrt((landmark1.x - landmark2.x)**2 + (landmark1.y - landmark2.y)**2)

def is_tekbir(landmarks_res, gender="k"):
    landmarks = landmarks_res[0]
    # Calculate distance between right thumb and right ear
    distance_right = calculate_distance(landmarks[22], landmarks[8])
    
    # Calculate distance between left thumb and left ear
    distance_left = calculate_distance(landmarks[21], landmarks[7])
    
    # Check if ankles, knees, and hips are aligned vertically for standing position
    is_straight = are_aligned_vertically(landmarks[27], landmarks[25], landmarks[23]) and are_aligned_vertically(landmarks[28], landmarks[26], landmarks[24])
    
    # If both thumbs are close enough to the ears and the person is standing straight
    thresh = get_threshold(gender, 'tekbir_distance_threshold')
    if distance_right < thresh and distance_left < thresh and is_straight:
        return True
    return False
    

def is_kiyam(landmarks_res, gender='k'):
    landmarks = landmarks_res[0]
    
    # Define a point between the thumb and wrist for both hands
    right_hand_center = Point((landmarks[16].x + landmarks[22].x) / 2, (landmarks[16].y + landmarks[22].y) / 2)
    left_hand_center = Point((landmarks[15].x + landmarks[21].x) / 2, (landmarks[15].y + landmarks[21].y) / 2)

    # Calculate distance between the central points of the two hands
    distance_between_hands = calculate_distance(right_hand_center, left_hand_center)
    
    # Estimate head position (average of ears)
    head_position = (landmarks[3].y + landmarks[4].y) / 2
    
    # Estimate chest and stomach positions
    chest_position = (landmarks[11].y + landmarks[12].y) / 2  # Y-coordinate average of left and right shoulders
    stomach_position = (landmarks[23].y + landmarks[24].y) / 2  # Y-coordinate average of left and right hips
    
    # Ensure person is standing
    if head_position < chest_position < stomach_position:
        
        # Check if the hands are close together
        if distance_between_hands < get_threshold(gender, 'kiyam_distance_threshold') :
            
            # For women, hands must be above the chest
            if gender == 'k':
                if chest_position > right_hand_center.y and chest_position > left_hand_center.y:
                    return True
            
            # For men, hands must be above the waist (stomach_position)
            else:
                if stomach_position > right_hand_center.y and stomach_position > left_hand_center.y:
                    return True
    
    return False

def is_ruku(landmarks_res, gender="k"):
    landmarks = landmarks_res[0]

    # Get y-coordinates of relevant landmarks
    nose_y = landmarks[0].y
    mid_spine_y = (landmarks[11].y + landmarks[12].y) / 2
    hips_y = (landmarks[23].y + landmarks[24].y) / 2

    # Check if the upper body is approximately parallel to the floor
    upper_body_parallel = abs(nose_y - mid_spine_y) < get_threshold(gender, 'ruku_head_spine_parallel_threshold') and abs(hips_y - mid_spine_y) < get_threshold(gender, 'ruku_parallel_threshold')

    # Check if hands are on the knees
    left_wrist_y = landmarks[15].y
    right_wrist_y = landmarks[16].y
    hands_on_knees_left = abs(left_wrist_y - landmarks[25].y) < get_threshold(gender, 'ruku_hand_to_knee_threshold')
    hands_on_knees_right = abs(right_wrist_y - landmarks[26].y) < get_threshold(gender, 'ruku_hand_to_knee_threshold')

    # Check if the person is standing
    knees_avg_y = (landmarks[25].y + landmarks[26].y) / 2
    ankles_avg_y = (landmarks[27].y + landmarks[28].y) / 2
    is_standing = nose_y < mid_spine_y < hips_y < knees_avg_y < ankles_avg_y

    # If all conditions are satisfied, return True
    if upper_body_parallel and hands_on_knees_left and hands_on_knees_right and is_standing:
        return True

    return False

def is_secde(landmarks_res, gender="k"):
    landmarks = landmarks_res[0]
    
    # Get the y-coordinates of nose, wrists, knees, hips, and ankles
    nose_y = landmarks[0].y
    left_wrist_y = landmarks[15].y
    right_wrist_y = landmarks[16].y
    left_knee_y = landmarks[25].y
    right_knee_y = landmarks[26].y
    left_hip_y = landmarks[23].y
    right_hip_y = landmarks[24].y
    left_ankle_y = landmarks[27].y
    right_ankle_y = landmarks[28].y

    # Check if the forehead (nose) is close to the ground.
    forehead_on_ground = abs(nose_y - left_ankle_y) < get_threshold(gender, 'secde_forehead_threshold') and abs(nose_y - right_ankle_y) < get_threshold(gender, 'secde_forehead_threshold')
    
    # Check if the palms are near the head. 
    hands_near_head_left = abs(left_wrist_y - nose_y) < get_threshold(gender, 'secde_hand_to_head_threshold')
    hands_near_head_right = abs(right_wrist_y - nose_y) < get_threshold(gender, 'secde_hand_to_head_threshold')

    # Check if the knees are near the head.
    knees_near_head_left = abs(left_knee_y - nose_y) < get_threshold(gender, 'secde_knee_to_head_threshold')
    knees_near_head_right = abs(right_knee_y - nose_y) < get_threshold(gender, 'secde_knee_to_head_threshold')

    # Check if the hips are close to the knees.
    hips_close_to_knees = abs(left_hip_y - left_knee_y) < get_threshold(gender, 'secde_hips_to_knee_threshold') and abs(right_hip_y - right_knee_y) < get_threshold(gender, 'secde_hips_to_knee_threshold')

    # If all conditions are satisfied, return True
    if forehead_on_ground and hands_near_head_left and hands_near_head_right and knees_near_head_left and knees_near_head_right and hips_close_to_knees:
        return True

    return False

def is_secde2(landmarks_res, gender="k"):
    landmarks = landmarks_res[0]
    
    # Get the y-coordinates of nose, wrists, knees, and ankles
    nose_y = landmarks[0].y
    left_wrist_y = landmarks[15].y
    right_wrist_y = landmarks[16].y
    left_knee_y = landmarks[25].y
    right_knee_y = landmarks[26].y
    left_ankle_y = landmarks[27].y
    right_ankle_y = landmarks[28].y

    # Ensure the forehead (nose) is close to the ground.
    forehead_on_ground = abs(nose_y - left_ankle_y) < get_threshold(gender, 'secde_forehead_threshold')
    
    # Ensure the hands are near the head.
    hands_near_head_left = abs(left_wrist_y - nose_y) < get_threshold(gender, 'secde_hand_to_head_threshold')
    hands_near_head_right = abs(right_wrist_y - nose_y) < get_threshold(gender, 'secde_hand_to_head_threshold')

    # Check if the person is not in a standing position
    # The idea is if the nose is closer to the knees and ankles, it indicates prostration
    not_standing = nose_y > left_knee_y and nose_y > right_knee_y and nose_y > left_ankle_y and nose_y > right_ankle_y

    # If all conditions are satisfied, return True
    if forehead_on_ground and hands_near_head_left and hands_near_head_right and not_standing:
        return True

    return False

    
def is_kade(landmarks_res, gender="k"):
    landmarks = landmarks_res[0]
    
    # Extract necessary landmarks
    left_wrist = landmarks[15].y
    right_wrist = landmarks[16].y
    left_knee = landmarks[25].y
    right_knee = landmarks[26].y
    left_hip = landmarks[23].y
    right_hip = landmarks[24].y
    nose = landmarks[0].y
    mid_spine = landmarks[12].y
    left_ankle = landmarks[27].y
    right_ankle = landmarks[28].y

    # Check if hips and knees have a significant y-difference, suggesting sitting
    if abs(left_knee - left_hip) > get_threshold(gender, 'kade_threshold') and abs(right_knee - right_hip) > get_threshold(gender, 'kade_threshold'):
        
        # Check if both wrists or hands are close to the knees
        if abs(left_wrist - left_knee) < get_threshold(gender, 'wrist_to_knee_threshold') and abs(right_wrist - right_knee) < get_threshold(gender, 'wrist_to_knee_threshold'):
            
            # Check the back's straightness using the nose and mid-spine
            if abs(nose - mid_spine) < get_threshold(gender, 'spine_straightness_threshold'):
                
                # Check ankles' position relative to hips
                if left_ankle > left_hip and right_ankle > right_hip:
                    return True
                    
    return False



def check_position(landmarks_res, gender):
    if is_tekbir(landmarks_res, gender):
        return PrayerPositions.TEKBIR
    elif is_kiyam(landmarks_res, gender):
        return PrayerPositions.KIYAM
    elif is_ruku(landmarks_res, gender):
        return PrayerPositions.RUKU
    elif is_secde(landmarks_res, gender):
        return PrayerPositions.SECDE
    elif is_kade(landmarks_res, gender):
        return PrayerPositions.KADE
    else:
        return None
