import cv2
import os

# Path to your video
video_path = '/home/cappittall/Videos/namaz/sabah_namazi_2rekat_farz.mp4'

# Create a folder to save the images
save_folder = 'data/position_images/messages'
os.makedirs(save_folder, exist_ok=True)

# Open the video
cap = cv2.VideoCapture(video_path)

# Check if video opened successfully
if not cap.isOpened():
    print("Error: Could not open video.")
    exit()

# Get the frame rate of the video
fps = cap.get(cv2.CAP_PROP_FPS)

# Count for frames
frame_count = 0

while True:
    ret, frame = cap.read()
    if not ret:
        break

    # Get the height and width of the frame
    height, width, _ = frame.shape

    # Calculate the height to crop (10% of the height)
    crop_height = int(height * 0.15)

    # Crop the bottom part of the frame
    cropped_frame = frame[height - crop_height:height, 0:width]

    # Save every second
    if frame_count % int(fps) == 0:
        second = frame_count // int(fps)
        cv2.imwrite(os.path.join(save_folder, f'frame_{second}.jpg'), cropped_frame)

    frame_count += 1

cap.release()
print("Finished processing.")
