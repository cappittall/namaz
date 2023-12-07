import os
import subprocess
import sys
import traceback
import cv2

from tflite_runtime.interpreter import load_delegate, Interpreter

from tools.helper import *

import pygame
from pygame.locals import *

pygame.init()

# Convert an OpenCV image to Pygame surface
def cvimage_to_pygame(image):
    image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    return pygame.image.frombuffer(image.tobytes(), image.shape[1::-1], "RGB")

models = [
    'models/all/mobilenet_v2_1.0_224_quant_edgetpu.tflite',
    'models/all/namazV0_E0_edgetpu.tflite',
    'models/all/namazV2_E0_edgetpu.tflite',
    'models/all/mobilenet_v2_1.0_224.tflite',
    'models/all/namazV0_E0.tflite',
    'models/all/namazV2_E0.tflite' 
]
# Initialize Pose and audio
model_path = 'models/all/pose_landmarker_full.task'
model_path_tflite = models[3]

BaseOptions = mp.tasks.BaseOptions
PoseLandmarker = mp.tasks.vision.PoseLandmarker
PoseLandmarkerOptions = mp.tasks.vision.PoseLandmarkerOptions
VisionRunningMode = mp.tasks.vision.RunningMode

options = PoseLandmarkerOptions(num_poses=1, 
                                min_pose_detection_confidence=0.35,
                                min_pose_presence_confidence=0.35,
                                min_tracking_confidence=0.35,
    base_options=BaseOptions(model_asset_path=model_path),
    running_mode=VisionRunningMode.IMAGE)

landmarker = PoseLandmarker.create_from_options(options)

def run_camera_loop(gender, prayer_time, debug):
    
    # Camera loop logic here
    print(f"Gender: {gender}, Prayer Time: {prayer_time} Debug: {debug}")
    clear_directory('data/inspect/')
    camera = CameraLoop(gender=gender, prayer_time=prayer_time, debug=debug)
    camera.run()
def resize_image_to_fixed(image, target_width, target_height):
    
    return cv2.resize(image, (int(target_width), int(target_height)))

def add_border(img, color, thickness):
    return cv2.copyMakeBorder(img, thickness, thickness, thickness, thickness, cv2.BORDER_CONSTANT, value=color)

class CameraLoop():
    def __init__(self, gender, prayer_time, debug):
        self.gender = gender
        self.prayer_time = prayer_time
        
        self.current_position = None
        self.detected_position = None
        self.next_position = None

        self.frame_counter = 0
        self.reference_image = None
        self.sound_message_image = None
        self.next_message_image = None
        
        self.sound_end_check = True
        self.namaz_timeline = None
        self.current_prayer_sounds = None
        
        self.position_change_event = threading.Event()
        self.debug = False if debug == "0" else True
        infoObject = pygame.display.Info()
        self.width, self.height = infoObject.current_w, infoObject.current_h
        self.target_width = int( self.width * 1 / 2)
        self.target_height = int(self.height * 0.80 )
        
        # Initialize camera
        self.cam_no = check_cameras()[-1]
        
        # Inıt interpreter
        if 'edgetpu' in model_path_tflite: 
            self.interpreter = Interpreter(
                    model_path=str(model_path_tflite),
                    experimental_delegates=[load_delegate('libedgetpu.so.1')]
                    )
        else:
             self.interpreter = Interpreter(model_path=str(model_path_tflite) )

        self.interpreter.allocate_tensors()
        self.input_details = self.interpreter.get_input_details()
        self.output_details = self.interpreter.get_output_details()
    
    def run(self,):
        self.current_sequence, current_prayer_sounds, namaz_timeline = load_squences(self.prayer_time)
        
        self.current_prayer_sounds = current_prayer_sounds
        self.namaz_timeline = namaz_timeline
        
        self.position_iterator = iter(self.current_sequence)
        self.counter = 0
        
        self.current_position = next(self.position_iterator)
        self.next_position = next(self.position_iterator)
        self.counter += 1 
        
        # sound initialize 
        relative_path = self.current_prayer_sounds.get(PrayerPositions.ALL, None)
        absolute_path = os.path.abspath(relative_path)
        # use gstreramer if available

        pygame.mixer.music.load(absolute_path)
        
        # Initial ref image and sound
        self.update_reference_image( self.current_position )
        worker = threading.Thread(target=self.play_sound_and_update_ui, args=(self.current_position, self.next_position, ))  
        worker.daemon = True
        worker.start()
        
        window = pygame.display.set_mode((self.width, self.height), pygame.FULLSCREEN)
        # Define exit button
        exit_button = pygame.Rect(self.width - 110, 10, 100, 50)
        exit_button_text = pygame.font.Font(None, 36).render("Çıkış", True, (0, 0, 0))

        # Start the camera capture in a new thread
        self.capture_camera(window, exit_button, exit_button_text)
            
    def capture_camera(self, window, exit_button, exit_button_text):
        
        # Setup camera
        self.setup_camera()
        self.last_time = time.time()
        # Pygame window setup
        pygame.display.set_caption('Camera Output')
        # window = pygame.display.set_mode((self.width, self.height))

        
        ## Start looping 
        while self.cap.isOpened():
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.release_camera()
                    pygame.quit()
                    return
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    if exit_button.collidepoint(event.pos):
                        self.release_camera()
                        pygame.quit()
                        subprocess.Popen(["python", "app2.py"])
                        return  # Exiting the script
            
            ret, image = self.cap.read()
            self.frame_counter += 1
                # Initialize time variable   
            if not ret or self.frame_counter % 10 == 0:
                continue
            # In order to increase frame 
            if self.sound_end_check:
                try: 
                    detection_result = get_landmarks_infrance(image, landmarker)
                    # draw landmarks on image           
                    if detection_result :
                        annotated_image, position_notes = self.handle_detection_result(detection_result, image )
                        # Write current position name on frame.                        
                        if self.debug:
                            annotated_image = self.display_position_on_image(annotated_image, self.detected_position, position_notes=position_notes)
                    else: annotated_image = image
                    next_poz = position_names.get(self.next_position, "")
                    self.update_next_message(next_poz)
                except Exception as e:
                    print("Exception: ", e)
                    traceback.print_exc()
            else:
                annotated_image = image  # Directly use the captured image without annotations
                position_notes = ""
                
    
                 
            if self.should_change_position():
                    # Wait until it's safe to proceed, which is when the event is set
                self.position_change_event.wait()
                self.position_change_event.clear()  # Clear the event for the next time
                print('Posizyon check e girdi... ', self.sound_end_check, threading.active_count() - 1 )
                
                self.current_position = self.next_position
                try:
                    self.next_position = next(self.position_iterator)
                    self.counter += 1
                    self.play_sound_and_update_ui(self.current_position, self.next_position) #, )).start()
                    
                except StopIteration:
                    self.on_exit_clicked()
                
                             
            # Update annotated image 
            processed_image = self.update_cam_image(annotated_image)  # Assuming this is where you process the image
            frame = cvimage_to_pygame(processed_image)  # Convert to Pygame surface
            window.blit(frame, (0, 0))  # Blit the camera frame

            # Draw the exit button over the frame
            pygame.draw.rect(window, (255, 255, 255), exit_button)
            window.blit(exit_button_text, exit_button_text.get_rect(center=exit_button.center))

            pygame.display.update()
            
        pygame.time.wait(10)
                
    def should_change_position(self):
            # Fixed the method name and simplified the logic for clarity
            is_different_position = self.detected_position != self.current_position
            is_correct_next_position = compare_positions(self.next_position, self.detected_position)
            is_final_position = self.next_position == PrayerPositions.RLSELAM
            """ return (is_different_position and is_correct_next_position or is_final_position) and \
                self.sound_end_check and self.detected_position is not None """
            if (is_different_position and is_correct_next_position or is_final_position) and self.sound_end_check and self.detected_position is not None:
                self.position_change_event.set()  # Signal that position should change
                return True
            else:
                return False
                            
    def play_sound_segment(self, start, duration, next_position):
        try:
            pygame.mixer.music.play(start = start)
            time.sleep(duration)
            pygame.mixer.music.stop()
            self.update_reference_image(next_position) 
        except Exception as e:
            print('Hata , ', e )

        self.sound_end_check = True        

    def play_sound_and_update_ui(self, current_position, next_position):
        self.sound_end_check = False
        try:
            time_period = self.namaz_timeline.get(current_position, None)        
            start, stop = time_period
            
            if self.debug:
                if (stop - start) > 30:
                    stop = start + 10
                    
            duration = stop - start  # Calculate duration based on start and stop
            
            # Play the sound segment in a separate thread to avoid blocking
            threading.Thread(target=self.play_sound_segment, args=(start, duration, next_position )).start()
            
            # Start updating message images in a separate thread
            threading.Thread(target=self.update_message_images, args=(start, stop)).start()
        
        except Exception as e:
            print('Hata: ', e)
            traceback.print_exc()

    
    def update_cam_image(self, img): 
        logging.debug("update_cam_image called")
        try:
            yellow_color = (48,48,48)  # (0, 255, 255)
            border_thickness = 10
            
            img = resize_image_to_fixed(img, self.target_width, self.target_height)
            self.reference_image = resize_image_to_fixed(self.reference_image, self.target_width, self.target_height)               
            img_a = add_border(img, yellow_color, border_thickness)
            img_b = add_border(self.reference_image, yellow_color, border_thickness)
            img_c = add_border(self.next_message_image, yellow_color, border_thickness)
            img_d = add_border(self.sound_message_image, yellow_color, border_thickness)
            top = np.concatenate((img_a , img_b), axis=1)
            bottom = np.concatenate((img_c , img_d), axis=1)
            all4img = np.concatenate((top,bottom), axis=0)
        except:
            logging.debug('Resim yüklenemedi')
            all4img = img
            
        return all4img
        
        
        
    def update_reference_image(self, next_sequence):
        reference_image = self.get_reference_image(next_sequence)
        self.reference_image = resize_image_to_fixed(reference_image, self.target_width, self.target_height)

    
    def get_reference_image(self, position):  
        image_path = position_to_image[position]
        image_path = image_path.replace('[gender]', self.gender)
        # return the image based on the detected_position
        return cv2.imread(image_path)
        
    def update_message_images(self, start, stop):
        for second in range(start, stop):
            try:
                mess_img_path = f'data/positions/messages/{self.prayer_time}/frame_{second}.jpg'
                message_image = cv2.imread(mess_img_path)
                self.sound_message_image = resize_image_to_fixed(message_image, self.target_width, self.target_height//7 )
                # self.message_img_frame.set_from_pixbuf(pixbuf_reference)
            except Exception as e:
                print('Message image reading error', e )
                mess_img_path = f'data/positions/messages/Error_Handling_image/frame_0.jpg'
                self.sound_message_image = resize_image_to_fixed(message_image, self.target_width, self.target_height//7 )
                traceback.print_exc()
            time.sleep(1)
        return False
                
    def handle_detection_result(self, detection_result, image ):
        if self.debug:
            image = draw_landmarks_on_image(image, detection_result)
        yzmodel_result = ""
        frame_rate = self.calculate_frame_rate() 
        if detection_result.pose_landmarks:
            landmarks = detection_result.pose_landmarks[0]
            bbox = get_bounding_box(landmarks, image)
            start = time.monotonic()
            # get current position
            self.detected_position, is_standing = check_position(image, landmarks, self.gender)
            
            # crop image in order to classify position
            croped_image = image[bbox[1]:bbox[3], bbox[0]:bbox[2]]
                        
            det_time = (time.monotonic() - start) * 1000
            start = time.monotonic()
            
            if self.sound_end_check:
                if 'edgetpu' in model_path_tflite:
                    clasfy_result, conf = get_class_of_position_int8(croped_image, 
                                self.interpreter, self.input_details, self.output_details)
                else:
                    clasfy_result, conf = get_class_of_position_fp32(croped_image, 
                                self.interpreter, self.input_details, self.output_details) 

                # consider if confidence > 80% and not standing
                if conf > 0.8 and not is_standing:
                    if clasfy_result == "kade":
                        self.detected_position = PrayerPositions.KADE 
                    if clasfy_result == "secde":
                        self.detected_position = PrayerPositions.SECDE
                    
                    yzmodel_result = f'{clasfy_result} {int(conf*100)}%' 
                    # args = {'args': f'{clasfy_result} {int(conf*100)}%' }
                    # threading.Thread(target=write_inspection_on_image, args=(croped_image,args,)).start()
                    
        position_notes = f"{self.detected_position}: {self.counter}/{len(self.current_sequence)}-YZ:{yzmodel_result}-FPS:{frame_rate:.0f}"
        return image, position_notes
    
    def display_position_on_image(self, image, detected_position, position_notes=None):
        
        # Get the position name from the mapping
        position_name = position_names.get(detected_position, "")
        
        # Put the detected position name on the image
        h,w,_ = image.shape 
        cv2.putText(image, f"{position_name}", (5, h-50), cv2.FONT_HERSHEY_SIMPLEX, 4, (0, 255, 0), 4)
        cv2.putText(image, position_notes, (10, 50), cv2.FONT_HERSHEY_SIMPLEX, 1.5 , (0, 0, 255), 4)
        
        return image
                    
    def update_next_message(self, new_text):
        img = np.zeros((self.target_height // 7, self.target_width, 3), dtype=np.uint8)
        img[:] = (0, 0, 0)
        try:
            font=cv2.FONT_HERSHEY_SIMPLEX
            text = 'Simdi - ' +  new_text.upper()
            # Calculate text size and position to center it
            text_size = cv2.getTextSize(text, font, 1, thickness=1)[0]
            text_x = (img.shape[1] - text_size[0]) // 2
            text_y = (img.shape[0] + text_size[1]) // 2
            # Put the text onto the image
            cv2.putText(img, text, (text_x, text_y), font, 1, (255,255,255), thickness=2)
        except:
            logging.debug('Hata: Message img oluşturulamadı.')
            
        self.next_message_image = img


                    
    def calculate_frame_rate(self):
        # Calculate the frame rate
        current_time = time.time()
        time_taken = current_time - self.last_time
        frame_rate = 1 / time_taken if time_taken != 0 else 0
        self.last_time = current_time
        return frame_rate
    
    def setup_camera(self):
        if not hasattr(self, 'cap') or not self.cap.isOpened():
            self.cap = cv2.VideoCapture(self.cam_no)
            if not self.cap.isOpened():
                logging.error("Error: Camera could not be opened.")
                return
            # Setting camera resolution
            if not self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.target_width):
                logging.warning(f"Warning: Unable to set frame width to {self.target_width}.")
            if not self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.target_height):
                logging.warning(f"Warning: Unable to set frame height to {self.target_height}.")
            


    def release_camera(self):
        if hasattr(self, 'cap') and self.cap.isOpened():
            self.cap.release()
            logging.info("Camera released.")    
    
                    
    def close_cap_and_sound(self):
        # Stop any playing sounds with GStreamer
        pygame.mixer.music.stop()
            
        # Release OpenCV capture
        self.release_camera()

if __name__ == "__main__":
    gender = sys.argv[1]  # First argument
    prayer_time = sys.argv[2]  # Second argument
    debug = sys.argv[3]
    run_camera_loop(gender, prayer_time, debug)