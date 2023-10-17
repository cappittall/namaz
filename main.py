import time
import cv2

from helper import *
from tools.constant_settings import * 


import mediapipe as mp
from mediapipe.tasks import python
from mediapipe.tasks.python import vision



# Initialize Pose and audio
model_path = 'models/mp/pose_landmarker_full.task'

BaseOptions = mp.tasks.BaseOptions
PoseLandmarker = mp.tasks.vision.PoseLandmarker
PoseLandmarkerOptions = mp.tasks.vision.PoseLandmarkerOptions
VisionRunningMode = mp.tasks.vision.RunningMode

options = PoseLandmarkerOptions(
    base_options=BaseOptions(model_asset_path=model_path),
    running_mode=VisionRunningMode.IMAGE)

landmarker = PoseLandmarker.create_from_options(options)

while True:
    gender = input("Cinsiyetinizi giriniz K - Kadın, E - Erkek ? ")
    if gender.lower() in ["e", "k"]:
        break
while True:
    prayer_time = input("Namaz Vaktini Seçiniz ? S - Sabah, Ö - Öğlen, İ - İkindi, A - Akşam, Y - Yatsı ? ")
    if prayer_time.lower() in ['s', 'ö', 'i', 'a', 'y' ]:
        break

print('Cinsiyet ', gender, 'Vakit : ', prayer_time )
sequences = {
    's': (sabah_namazi_2, sabah_dualari),
    'ö': (oglen_namazi_4, oglen_dualari), 
    'i': (ikindi_namazi_4, ikindi_dualari),
    'a': (aksam_namazi_3, aksam_dualari),
    'y': (yatsi_namazi_4, yatsi_dualari)
}

current_sequence, current_prayer_time_sounds = sequences.get(
                            prayer_time, (sabah_namazi_2, sabah_dualari))

print('>>>>> ', current_sequence, current_prayer_time_sounds)

# Initialize camera
cap = cv2.VideoCapture(0)


# Constants
distance_threshold = 0.1
current_position = None
previous_position = None
last_time = 0
min_stable_time = 1  # Time in seconds

# Initialize with a default prayer time (change this based on the actual prayer time)


while cap.isOpened():
    ret, image = cap.read()
    if not ret:
        print("Skipping empty frame")
        continue
    
       
    current_time = time.time()
    detection_result = get_landmarks_infrance(image.copy(), landmarker)
    
    if detection_result:
        annotated_image = draw_landmarks_on_image(image, detection_result)
        
    if detection_result.pose_landmarks:
        current_position = check_position(detection_result.pose_landmarks)
        print(current_position, previous_position)
        
    if current_position == previous_position and current_position is not None:
        if current_time - last_time >= min_stable_time:
           
            # pygame.mixer.Sound(current_prayer_time_sounds[current_position]).play()
            print('PLAY !:', current_prayer_time_sounds[current_position] )
            print('current_position : ', current_position)
            
            previous_position = current_position

            
            
    cv2.imshow('Praying with AI', annotated_image)
    if cv2.waitKey(5) & 0xFF == 27:
        break

# Release resources
cap.release()
cv2.destroyAllWindows()