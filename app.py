import glob
import os
import time
import threading
import traceback
import cv2
from PIL import Image
from tools.constant_settings import * 
from tools.helper import *
import mediapipe as mp

# initialize Gtk
import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, Gdk, GdkPixbuf, GLib

from tflite_runtime.interpreter import load_delegate, Interpreter
# from tensorflow.lite.python.interpreter import Interpreter, load_delegate

import pygame.mixer

pygame.mixer.init()

""" models = glob.glob('models/all/*.tflite')
for i, m in enumerate(models):
    print(i,'-> ', m)
while True:
    model_no = int(input('Model numarsınız seçiniz...?'))
    if model_no < len(models) and model_no >=0 : break
    
model = models[model_no] """

models = [
    'models/all/mobilenet_v2_1.0_224_quant_edgetpu.tflite',
    'models/all/mobilenet_v2_1.0_224.tflite',
    'models/all/namazV0_E0.tflite',
    'models/all/namazV2_E0.tflite' 
]
# Initialize Pose and audio
model_path = 'models/all/pose_landmarker_full.task'
model_path_tflite = models[0]

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

def load_dynamic_css(css):
        css_provider = Gtk.CssProvider()
        css_provider.load_from_data(css.encode('utf-8'))
        screen = Gdk.Screen.get_default()
        style_context = Gtk.StyleContext()
        style_context.add_provider_for_screen(screen, css_provider, Gtk.STYLE_PROVIDER_PRIORITY_USER)

def load_squences(prayer_time):
    
    print( 'Vakit : ', prayer_time )
    sequences = {
        'Sabah': (sabah_namazi_2, sabah_dualari, sabah_manazi_timeline),
        'Öğle': (oglen_namazi_4, oglen_dualari, sabah_manazi_timeline), 
        'İkindi': (ikindi_namazi_4, ikindi_dualari, sabah_manazi_timeline),
        'Akşam': (aksam_namazi_3, aksam_dualari, sabah_manazi_timeline),
        'Yatsı': (yatsi_namazi_4, yatsi_dualari, sabah_manazi_timeline)
    }

    current_sequence, current_prayer_sounds, timeline = sequences.get(
                                prayer_time, (None, None, None))
    
    return current_sequence, current_prayer_sounds, timeline
    
def resize_image(image, target_height, target_width):
    dH, dW = target_height - image.shape[0], target_width - image.shape[1]
    if dH < 0 or dW < 0:
        aspect_ratio = image.shape[1] / float(image.shape[0])
        new_width = target_width if dW < dH else int(target_height * aspect_ratio)
        new_height = target_height if dH < dW else int(target_width / aspect_ratio)
        image = cv2.resize(image, (new_width, new_height))
    return image

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
            
def resize_image_to_fixed(image, target_width, target_height):
    return cv2.resize(image, (target_width, target_height))

class PrayerApp(Gtk.Window):
    def __init__(self):
        super().__init__(title="Namaz Applikasyonu")
        self.fullscreen()
          
        self.gender = None
        self.prayer_type = None
        self.set_border_width(10)

        self.previous_position = None
        self.current_position = None
        self.next_position = None
        
        self.check_image = False

        self.sound_end_check = True
        self.namaz_timeline = None
        self.current_prayer_sounds = None
        
        # Resize the images
        self.screen = Gdk.Display.get_default().get_monitor(0).get_geometry()    
        self.target_width, self.target_height = int(self.screen.width * 0.95 / 2), int(self.screen.height * 0.8)  
        
        # Initialize camera
        self.cap = cv2.VideoCapture(1) # '/home/cappittall/Videos/namaz/namaz1.mp4')
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.target_width)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.target_height)
        self.cap.set(cv2.CAP_PROP_FPS, 30) 

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
        
        # Initial Gender Selection Screen
        self.show_gender_buttons()
        

    def show_gender_buttons(self):
        css = '''
        button {
            background: yellow;
            color: black;
            font-size: 50px;
            font-weight: bold;
            margin: 50px;
        }
        window {
            background: green;
           
            
        }
        '''        
        load_dynamic_css(css)
 
        box = Gtk.Box(spacing=20)
        box.set_homogeneous(False)

        button_male = Gtk.Button(label="Erkek")
        button_male.set_size_request(40, 60)

        align_male = Gtk.Alignment(xalign=0.5, yalign=0.5)
        align_male.add(button_male)

        button_female = Gtk.Button(label="Kadın")
        button_female.set_size_request(40, 60)

        align_female = Gtk.Alignment(xalign=0.5, yalign=0.5)
        align_female.add(button_female)

        button_male.connect("clicked", self.on_gender_selected, "Erkek")
        button_female.connect("clicked", self.on_gender_selected, "Kadın")

        box.pack_start(align_male, True, True, 0)
        box.pack_start(align_female, True, True, 0)
        
        self.add(box)
        self.show_all()

    def on_gender_selected(self, button, gender):
        self.gender = "e" if gender == "Erkek" else "k"
        self.remove(self.get_child())
        self.show_prayer_type_buttons()

    def show_prayer_type_buttons(self):
        css = '''
        
        button, label {
            background: yellow;
            color: black;
            font-size: 30px;
            margin: 10px 10px;
            padding: 10px 5px;
        }
        
        label#title_label {
            font-weight: bold;
        }
        window {
            background: green;
        }
        '''
        load_dynamic_css(css)
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=20)

        grid = Gtk.Grid()
        grid.set_column_homogeneous(True)  # Make all columns same width
        grid.set_margin_start(50)  # 50 px margin on the left
        grid.set_margin_end(50)  # 50 px margin on the right
        
        back_button = Gtk.Button(label="Geri")
        back_button.set_hexpand(True)  # Expand button horizontally
        back_button.connect("clicked", lambda button: self.on_back_clicked(button, "page_1"))

        exit_button = Gtk.Button(label="ÇIKIŞ")
        exit_button.set_hexpand(True)
        exit_button.connect("clicked", self.on_exit_clicked)

        grid.attach(back_button, 0, 0, 1, 1)
        label = Gtk.Label(label="NAMAZ SAATİNİ SEÇİNİZ")
        label.set_hexpand(True)  # Expand label horizontally
        label.set_name("title_label")
        grid.attach(label, 1, 0, 4, 1)
        grid.attach(exit_button, 5, 0, 1, 1)

        prayers = ["Sabah", "Öğle", "İkindi", "Akşam", "Yatsı"]
        for idx, prayer in enumerate(prayers, start=2):
            button = Gtk.Button(label=prayer)
            button.set_hexpand(True)  # Expand button horizontally
            button.connect("clicked", self.on_prayer_type_selected, prayer)
            grid.attach(button, 1, idx, 4, 1)  # Span entire width of the grid

        self.add(grid)
        self.show_all()
        
    def update_message1(self, new_text):
        self.message_box1.set_text(new_text)

    def update_message2(self, new_text):
        self.message_box2.set_text(new_text)
        
    def on_prayer_type_selected(self, button, prayer):
        self.prayer_type = prayer
        self.remove(self.get_child())  # Clear existing child
        # threading.Thread(target=self.run_main_code()).start()
        self.run_main_code()
    
    def capture_camera(self,):
        
        ## Start looping 
        while self.cap.isOpened():
            ret, image = self.cap.read()
            
            if not ret:
                continue
            try: 
                detection_result = get_landmarks_infrance(image.copy(), landmarker)
                # draw landmarks on image           
                if detection_result:
                    annotated_image = draw_landmarks_on_image(image.copy(), detection_result)
                    
                    if detection_result.pose_landmarks:
                        landmarks = detection_result.pose_landmarks[0]
                        bbox = get_bounding_box(landmarks, image)
                        start = time.monotonic()
                        # get current position
                        self.current_position = check_position(image.copy(), landmarks, self.gender)
                        
                        # crop image in order to classify position
                        croped_image = image[bbox[1]:bbox[3], bbox[0]:bbox[2]]
                                                
                        det_time = (time.monotonic() - start)*1000
                        start = time.monotonic()
                        
                        if 'edgetpu' in model_path_tflite:
                            clasfy_result, conf = get_class_of_position_int8(croped_image, 
                                        self.interpreter, self.input_details, self.output_details)
                        else:
                            clasfy_result, conf = get_class_of_position_fp32(croped_image, 
                                        self.interpreter, self.input_details, self.output_details)
                        
                        # print(f'Det time - pose:{det_time:.2f} -  tflite_edge: {(time.monotonic() - start ) * 1000 :.2f} ')
                  
                        # consider if confidence > 70% 
                        if conf > 0.7:
                            if clasfy_result == "secde":
                                self.current_position = PrayerPositions.SECDE
                            yzmodel_rez = f'{clasfy_result} {int(conf*100)}%' 
                            args = {'args': f'{clasfy_result} {int(conf*100)}%' }
                            threading.Thread(target=write_inspection_on_image, args=(croped_image,args,)).start()
                                                       
                        else:
                            yzmodel_rez = ''

                        # Write current position name on frame.
                        position_note  = f"CP_{self.current_position}{self.counter}/{len(self.current_sequence)}- {yzmodel_rez} "
                        annotated_image = self.display_position_on_image(annotated_image, self.current_position, self.next_position, position_notes=position_note)
           
            except Exception as e:
                print("Exception: ", e)
                traceback.print_exc()
                                                 
            if ((self.current_position != self.previous_position and \
                self.current_position == self.next_position and \
                self.current_position is not None) or \
                self.next_position==PrayerPositions.LRSELAM)  and self.sound_end_check :
                        
                self.previous_position = self.current_position                       
                try:
                    self.next_position = next(self.position_iterator)
                    self.counter += 1
                    if self.sound_end_check:
                        print('Yeni ses çalacak - ', )
                        threading.Thread(target=self.play_sound, args=(self.current_position, lambda: self.update_reference_image(self.next_position))).start()
                except StopIteration:
                    self.on_exit_clicked()

            # Update annotated image                
            start = time.monotonic()
            resized_annotated_image = resize_image_to_fixed(annotated_image, self.target_width, self.target_height)
            
            GLib.idle_add(self.update_image, resized_annotated_image)
        
    def update_image(self, img):
        self.annotated_img_frame.set_from_pixbuf(self.cv2_to_gdkpixbuf(img))
        self.show_all()
        
    def run_main_code(self):
        css = '''
        button, label {
            background: yellow;
            color: black;
            font-size: 10px;
            margin: 5px 5px;  
            padding: 5px 2.5px;  

        }
        label#title_label {
            font-weight: bold;

        }
        window {
            background: green;
        }
        '''
        load_dynamic_css(css)

        main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=20)
        grid = Gtk.Grid()
        
        
        # Add Geri and ÇIKIŞ buttons
        back_button = Gtk.Button(label="Geri")
        #back_button.set_hexpand(True)
        back_button.connect("clicked", lambda button: self.on_back_clicked(button, "page_2"))

        exit_button = Gtk.Button(label="ÇIKIŞ")
        #exit_button.set_hexpand(True)
        exit_button.connect("clicked", self.on_exit_clicked)

        
        grid.attach(back_button, 0, 0, 1, 1)
        label = Gtk.Label(label=f"{self.prayer_type.upper()} NAMAZI ")
        label.set_hexpand(True)
        label.set_name("title_label")
        grid.attach(label, 1, 0, 4, 1)  # Span the label across 5 columns
        grid.attach(exit_button, 5, 0, 1, 1)  # Shifted exit_button to column 6


        # Image widgets
        self.annotated_img_frame = Gtk.Image()  # Create a frame for annotated image
        self.reference_img_frame = Gtk.Image()  # Create a frame for reference image

        grid.attach(self.annotated_img_frame, 0, 1, 3, 1)  # Occupy 3 columns for annotated image
        grid.attach(self.reference_img_frame, 3, 1, 3, 1)  # Occupy 3 columns for reference image

        # Message boxes
        self.message_box1 = Gtk.Label(label="Birinci mesaj ")  
        self.message_box2 = Gtk.Label(label="İkinci mesaj ")  

        grid.attach(self.message_box1, 0, 2, 3, 1)  # Occupy 3 columns for the first message
        grid.attach(self.message_box2, 3, 2, 3, 1)  # Occupy 3 columns for the second message

        main_box.pack_start(grid, True, True, 0)  # Add grid with widgets to the main box
        main_box.set_border_width(20)
        
        """ back_button.set_size_request(50, 20)  # Width and height
        exit_button.set_size_request(50, 20)
        self.annotated_img_frame.set_size_request(250, 250)  # You can adjust based on actual image dimensions
        self.reference_img_frame.set_size_request(250, 250)"""
        self.message_box1.set_size_request(250, 100)
        self.message_box2.set_size_request(250, 100) 

        self.add(main_box)
        
        # clear inspect directory 
        clear_directory('data/inspect/')
        
        self.current_sequence, current_prayer_sounds, namaz_timeline = load_squences(self.prayer_type)
        
        self.current_prayer_sounds = current_prayer_sounds
        self.namaz_timeline = namaz_timeline
        
        self.position_iterator = iter(self.current_sequence)
        self.counter = 0
        try:
            initial_position = next(self.position_iterator)
            self.next_position = next(self.position_iterator)
            self.counter += 1 
        except StopIteration:
            print("Namaz bitti.")
            return
        
        self.update_reference_image(initial_position )

        pygame.mixer.music.load(self.current_prayer_sounds.get(PrayerPositions.ALL, None))
        print('Ses dosyası yüklendi...')

        # Start initial sound and update the reference image when it finishes
        threading.Thread(target= self.play_sound, args=(initial_position, lambda: self.update_reference_image(self.next_position),)).start()
        
        # Start the camera capture in a new thread
        camera_thread = threading.Thread(target=self.capture_camera )
        camera_thread.daemon = True
        camera_thread.start()
                              
            
    def cv2_to_gdkpixbuf(self, cv2_image):
        image = Image.fromarray(cv2.cvtColor(cv2_image, cv2.COLOR_BGR2RGB))
        arr = np.array(image)
        height, width, channels = arr.shape
        pixbuf = GdkPixbuf.Pixbuf.new_from_data(
            arr.tobytes(), GdkPixbuf.Colorspace.RGB, False, 8, width, height, width * channels)
        return pixbuf
    
    def get_reference_image(self, position):  # Replace this function with your actual logic
        image_path = position_to_image[position]
        image_path = image_path.replace('[gender]', self.gender)
        # return the image based on the current_position
        return cv2.imread(image_path)
    
    def play_sound(self, sequence, callback=None):
        self.sound_end_check = False
        """For timeline playlist exist from one file """
        time_period = self.namaz_timeline.get(sequence, None)        
        if time_period:
            try:
                start, stop = time_period
                pygame.mixer.music.play(start = start)
                time.sleep( stop - start )
                pygame.mixer.music.stop()
                self.sound_end_check = True
            except Exception as e:
                print('Hata , ', e )

        if callback:
            callback()
        return 
        
    def update_reference_image(self, next_sequence):
        start = time.monotonic()
        reference_image = self.get_reference_image(next_sequence)
        resized_reference_image = resize_image_to_fixed(reference_image, self.target_width, self.target_height)
        pixbuf_reference = self.cv2_to_gdkpixbuf(resized_reference_image)
        self.reference_img_frame.set_from_pixbuf(pixbuf_reference)
        print(f'Ref image time: {int((time.monotonic() - start)*1000)}')
        return
    
        
        
    def display_position_on_image(self, image, detected_position, next_position, position_notes=None):
        # Get the position name from the mapping
        position_name = position_names.get(detected_position, "PozYok")
        next_poz = position_names.get(next_position, "PozYok")
        # Put the detected position name on the image
        cv2.putText(image, f"P: {position_name}", (5, 200), cv2.FONT_HERSHEY_SIMPLEX, 4, (0, 255, 0), 4)
        cv2.putText(image, f"N: {next_poz}", (5, 480), cv2.FONT_HERSHEY_SIMPLEX, 3, (0, 255, 0), 2)
        
        # If there are notes for the detected position, display them too
        if position_notes:
            cv2.putText(image, position_notes, (10, 70), cv2.FONT_HERSHEY_SIMPLEX, 1.5 , (0, 0, 255), 4)
        
        return image
    
    def close_cap_and_sound(self,):
        # Stop any playing sounds with Pygame
        try:
            pygame.mixer.music.stop()
        except Exception as e:
            print('Errro: ', e )
            
         # Release OpenCV capture
        if hasattr(self, 'cap') and self.cap:
            self.cap.release()
        
            
    def on_back_clicked(self, button, page):
        print('Page ', page )
        
        self.close_cap_and_sound()
        self.remove(self.get_child())
        
        if page=="page_1":
            self.show_gender_buttons()
            
        elif page=="page_2":
            
            self.show_prayer_type_buttons()
        else:
            self.show_gender_buttons()   
                
    def on_exit_clicked(self, button):
        print('Exit clicked ', hasattr(self, 'cap') )
        self.close_cap_and_sound()
        # Exit the application
        Gtk.main_quit()
        print('Kapatıldı....')

        
if __name__ == "__main__":
    win = PrayerApp()
    win.connect("destroy", Gtk.main_quit)
    win.show_all()
    Gtk.main()

