import os
import time
import cv2
import numpy as np
from PIL import Image
from tflite_runtime.interpreter import Interpreter
import mediapipe as mp

from helper import get_bounding_box, get_landmarks_infrance


# Initialize Pose and audio
model_path = 'models/mp/pose_landmarker_full.task'
model_path_tflite = 'models/epoch10/namazV0_E0.tflite'
effi0_path = 'models/efficientdet_lite0.tflite'

BaseOptions = mp.tasks.BaseOptions
ObjectDetector = mp.tasks.vision.ObjectDetector
ObjectDetectorOptions = mp.tasks.vision.ObjectDetectorOptions
VisionRunningMode = mp.tasks.vision.RunningMode

options = ObjectDetectorOptions(
    max_results=1, 
    category_allowlist=['person'],
    score_threshold = 0.25,
    base_options=BaseOptions(model_asset_path=effi0_path),
    running_mode=VisionRunningMode.IMAGE)
                                
                                
  

landmarker = ObjectDetector.create_from_options(options)

def classify_and_save_images(image_folder, model_path, output_folder, labels):
    global start_time
    #try:
    # Initialize TFLite interpreter
    interpreter = Interpreter(model_path=model_path)
    interpreter.allocate_tensors()

    input_details = interpreter.get_input_details()
    output_details = interpreter.get_output_details()

    # Get input size from model details
    input_size = tuple(input_details[0]['shape'][1:3])

    for image_file in os.listdir(image_folder):
        if not image_file.endswith(('.jpg', '.png', '.jpeg')):
            continue

        image_path = os.path.join(image_folder, image_file)
        img_np = cv2.imread(image_path)
        img = Image.fromarray(img_np)

        detection_result = get_landmarks_infrance(img_np, landmarker)
        print('detection_result : ', detection_result)

        if detection_result.detections:
            bounding_box = detection_result.detections[0].bounding_box
            origin_x = bounding_box.origin_x
            origin_y = bounding_box.origin_y
            width = bounding_box.width
            height = bounding_box.height

            # Crop the image using the bounding box details
            cropped_img_np = img_np[origin_y:origin_y+height, origin_x:origin_x+width]

            
            # Convert cropped numpy array to PIL Image
            img = Image.fromarray(cropped_img_np)

            if img.mode not in ('RGB', 'L'):
                img = img.convert('RGB')

            img = img.resize(input_size)
            img_array = np.array(img)

            scale, zero_point = input_details[0]['quantization']
            img_array = np.uint8(img_array / scale + zero_point)
            img_array = np.expand_dims(img_array, axis=0)

            interpreter.set_tensor(input_details[0]['index'], img_array)
            interpreter.invoke()

            output_data = interpreter.get_tensor(output_details[0]['index'])
            label = labels[np.argmax(output_data)]

            label_folder = os.path.join(output_folder, label)
            if not os.path.exists(label_folder):
                os.makedirs(label_folder)

            # Save the cropped image
            cv2.imwrite(os.path.join(label_folder, image_file), cropped_img_np)

            print(f'{image_file} Detected time: {(time.monotonic() - start_time) * 1000:.3f} ms')
            start_time = time.monotonic()
        else: 
            print('Detection result is  ', detection_result)

    """ except Exception as e:
        print(f"An error occurred: {e}") """

# Initialize global start time
start_time = time.monotonic()

# Folder containing the images you want to classify
image_folder = 'data/salat/imagesv1'

# Output folder where you want to save classified images
output_folder = 'data/salat/output'

# Labels corresponding to the output of your model, assumed to be in order
labels = ['kade', 'kiyam', 'ruku', 'secde']

classify_and_save_images(image_folder, model_path_tflite, output_folder, labels)

