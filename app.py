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
gi.require_version('Gst', '1.0')
from gi.repository import Gtk, Gdk, GdkPixbuf, GLib, Gst
Gtk.init()
Gst.init(None)

from tflite_runtime.interpreter import load_delegate, Interpreter
# from tensorflow.lite.python.interpreter import Interpreter, load_delegate

""" models = glob.glob('models/all/*.tflite')
for i, m in enumerate(models):
    print(i,'-> ', m)
while True:
    model_no = int(input('Model numarsınız seçiniz...?'))
    if model_no < len(models) and model_no >=0 : break
    
model = models[model_no] """

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

def load_dynamic_css(css):
        css_provider = Gtk.CssProvider()
        css_provider.load_from_data(css.encode('utf-8'))
        screen = Gdk.Screen.get_default()
        style_context = Gtk.StyleContext()
        style_context.add_provider_for_screen(screen, css_provider, Gtk.STYLE_PROVIDER_PRIORITY_USER)
    
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
    return cv2.resize(image, (int(target_width), int(target_height)))

class PrayerApp(Gtk.Window):
    def __init__(self):
        super(PrayerApp, self).__init__(title="Namaz Applikasyonu")
        self.fullscreen()
          
        self.gender = None
        self.prayer_time = None
        self.set_border_width(10)

        self.current_position = None
        self.detected_position = None
        self.next_position = None
        
        self.check_image = False
        self.frame_counter = 0
        self.sound_end_check = True
        self.namaz_timeline = None
        self.current_prayer_sounds = None
        
        self.worker_threads = []
        self.debug = False
        # Resize the images
        self.screen = Gdk.Display.get_default().get_monitor(0).get_geometry()    
        self.target_width, self.target_height = int(self.screen.width * 0.95 / 2), int(self.screen.height * 0.8)  
        
        # Initialize camera
        self.cam_no = check_cameras()[-1]
        
        self.setup_camera()

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
        window {
            background: green;      
        }
        button {
            background: yellow;
            color: black;
            font-size: 50px;
            font-weight: bold;
            margin: 10px 10px;
            padding: 10px 5px;
        }
        
        label {
            background: yellow;
            color: black;
            font-size: 30px;
            margin: 10px 10px;
            padding: 10px 5px;
        }
        
        button:focus {
            background: #CCCC00;
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
        self.show_prayering_time_buttons()

    def show_prayering_time_buttons(self):
        css = '''
        window {
            background: green;
        }
        button, label {
            background: yellow;
            color: black;
            font-size: 30px;
            margin: 10px 10px;
            padding: 10px 5px;
        }
        
        button:focus {
            background: #CCCC00;
        }
        
        label#title_label {
            font-weight: bold;
        }
        
        #debug {
            color: white;
            
            font-size: 14px;
            padding: 5px 10px;
            margin: 5px 0;
        }

        #debug label {
            background: green;
            color: white;
            font-size:14px;
        }
        '''
        load_dynamic_css(css)

        # Create a new box to hold everything
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=20)
        
        # Create the grid
        grid = Gtk.Grid()
        grid.set_column_homogeneous(True)
        grid.set_margin_start(50)
        grid.set_margin_end(50)

        # Create buttons and labels, connect them to their callbacks
        back_button = Gtk.Button(label="Geri")
        back_button.set_hexpand(True)
        back_button.connect("clicked", lambda button: self.on_back_clicked(button, "page_1"))

        exit_button = Gtk.Button(label="ÇIKIŞ")
        exit_button.set_hexpand(True)
        exit_button.connect("clicked", self.on_exit_clicked)

        # Attach the buttons and labels to the grid
        grid.attach(back_button, 0, 0, 1, 1)
        label = Gtk.Label(label="NAMAZ SAATİNİ SEÇİNİZ")
        label.set_hexpand(True)
        label.set_name("title_label")
        grid.attach(label, 1, 0, 4, 1)
        grid.attach(exit_button, 5, 0, 1, 1)

        prayering_times = ["Sabah", "Öğle", "İkindi", "Akşam", "Yatsı"]
        for idx, prayering_time in enumerate(prayering_times, start=1):
            button = Gtk.Button(label=prayering_time)
            button.set_hexpand(True)
            button.connect("clicked", self.on_prayering_time_selected, prayering_time)
            grid.attach(button, 0, idx, 6, 1)  # Span entire width of the grid
        
        
        # Create the checkbox for debug mode
        debug_checkbutton = Gtk.CheckButton(label="Debug")
        debug_checkbutton.set_active(self.debug)
        debug_checkbutton.set_name('debug')
        debug_checkbutton.set_halign(Gtk.Align.START)  # Align to the start, which is the left
        debug_checkbutton.set_valign(Gtk.Align.END)   # Align to the end, which is the bottom
        debug_checkbutton.connect("toggled", self.on_debug_toggled)  # Connect to a callback function

        # You might need to adjust the grid attachment to leave space for the debug checkbox
        grid.attach(debug_checkbutton, 0, len(prayering_times) + 1, 1, 1)  # Attach the debug checkbox to the grid

        # Pack the grid into the box
        box.pack_start(grid, True, True, 0)

        # Add the box to the window
        self.add(box)
        self.show_all()
    
    def on_prayering_time_selected(self, button, prayering_time):
        self.prayer_time = prayering_time
        self.remove(self.get_child())  
        # Make sure to run this in the main GTK thread
        Gdk.threads_add_idle(GLib.PRIORITY_DEFAULT_IDLE, self.run_main_code)
        
    def run_main_code(self):
        css = '''
        button, label {
            background: yellow;
            color: black;
            font-size: 10px;
            margin: 5px 5px;  
            padding: 5px 2.5px;  

        }
        button:focus {
            background: #CCCC00;
        }
        label#title_label {
            font-weight: bold;
            font-size:40px;
        }
        label#message1 {
            font-weight: bold;
            font-size:40px;
            margin-bottom: 10px;
            
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
        label = Gtk.Label(label=f"{self.prayer_time.upper()} NAMAZI ")
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
        self.message_box1 = Gtk.Label(label="Sonraki hareket")  
        self.message_box1.set_name('message1')
        self.message_img_frame = Gtk.Image() # message 2
        """ self.message_box2 = Gtk.Label(label="İkinci mesaj ")  
        self.message_box2.set_name('message2') """

        grid.attach(self.message_box1, 0, 2, 3, 1)  # Occupy 3 columns for the first message
        grid.attach(self.message_img_frame, 3, 2, 3, 1)  # Occupy 3 columns for the second message

        main_box.pack_start(grid, True, True, 0)  # Add grid with widgets to the main box
        main_box.set_border_width(20)

        self.add(main_box)
        self.show_all()
        
        # clear inspect directory 
        clear_directory('data/inspect/')
        
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

        
        self.player = Gst.ElementFactory.make("playbin", "player")
        self.player.set_property('uri', 'file://' + absolute_path)
        
        # Connect to the bus for EOS and ERROR messages
        bus = self.player.get_bus()
        bus.add_signal_watch()
        bus.connect("message::eos", self.on_eos)
        bus.connect("message::error", self.on_error)
        
        # Initial ref image and sound
        self.update_reference_image( self.current_position )
        worker = threading.Thread(target=self.play_sound_and_update_ui, args=(self.current_position, self.next_position, ))  
        worker.daemon = True
        worker.start()
        self.worker_threads.append(worker)
            
        # Start the camera capture in a new thread
        camera_thread = threading.Thread(target=self.capture_camera )
        camera_thread.daemon = True
        camera_thread.start()    
            
    def capture_camera(self,):
        # Setup camera
        self.setup_camera()
        self.last_time = time.time()
        ## Start looping 
        while self.cap.isOpened():
            ret, image = self.cap.read()
            self.frame_counter += 1
             # Initialize time variable   
            if not ret or self.frame_counter % 2 == 0:
                continue
            try: 
                detection_result = get_landmarks_infrance(image, landmarker)
                # draw landmarks on image           
                if detection_result :
                    annotated_image, position_notes = self.handle_detection_result(detection_result, image )
                    # Write current position name on frame.
                    annotated_image = self.display_position_on_image(annotated_image, self.detected_position, self.next_position, position_notes=position_notes)
                else: annotated_image = image
                
            except Exception as e:
                print("Exception: ", e)
                traceback.print_exc()
                                                 
            if self.should_change_position():
                print('Posizyon check e girdi... ', self.sound_end_check, threading.active_count() - 1 )
                self.sound_end_check = False
                self.current_position = self.next_position
                try:
                    self.next_position = next(self.position_iterator)
                    self.counter += 1
                    self.play_sound_and_update_ui(self.current_position, self.next_position) #, )).start()
                    
                except StopIteration:
                    self.on_exit_clicked()
                    
            # Update annotated image 
            self.update_cam_image(annotated_image )
                
    def should_change_position(self):
         # Fixed the method name and simplified the logic for clarity
        is_different_position = self.detected_position != self.current_position
        is_correct_next_position = compare_positions(self.next_position, self.detected_position)
        is_final_position = self.next_position == PrayerPositions.RLSELAM
        return (is_different_position and is_correct_next_position or is_final_position) and \
            self.sound_end_check and self.detected_position is not None
                              
    def play_sound_segment(self, start, duration, next_position):
        # Prepare the player for seeking
        self.player.set_state(Gst.State.PAUSED)
        self.player.get_state(Gst.CLOCK_TIME_NONE)  # Wait for the state to change
        
        # Seek to the desired start position and play for the duration
        seek_event = Gst.Event.new_seek(
            1.0, Gst.Format.TIME,
            Gst.SeekFlags.FLUSH | Gst.SeekFlags.ACCURATE,
            Gst.SeekType.SET, start * Gst.SECOND,
            Gst.SeekType.SET, (start + duration) * Gst.SECOND
        )
        self.player.send_event(seek_event)
        
        # Start playing after seeking
        self.player.set_state(Gst.State.PLAYING)

        # Set a timer to execute the end_of_duration callback after the duration
        GLib.timeout_add_seconds(duration, self.end_of_duration, next_position)
        
    def end_of_duration(self, next_position):
        # This function will be called by GLib after 'duration' seconds
        print('Duration ended, stopping playback')
        self.player.set_state(Gst.State.NULL)
        self.update_reference_image(next_position)
        self.sound_end_check = True        
        return False  # Return False to stop the timer from repeating
    
    def on_eos(self, bus, msg):
        # Stop the audio when EOS is received, just as a safety measure
        self.player.set_state(Gst.State.NULL)
        # No need to update UI here, it's handled by end_of_duration callback
    def on_error(self, bus, msg):
        error, debug = msg.parse_error()
        print(f"Error: {error}, {debug}")

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
            w1 = threading.Thread(target=self.play_sound_segment, args=(start, duration, next_position ))
            w1.daemon = True
            w1.start()
            self.worker_threads.append(w1)
            
            # Start updating message images in a separate thread
            w2= threading.Thread(target=self.update_message_images, args=(start, stop))
            w2.daemon = True
            w2.start()
            self.worker_threads.append(w2)
        
        except Exception as e:
            print('Hata: ', e)
            traceback.print_exc()

    
    def update_cam_image(self, img):     
        # Resize the image before passing to the UI thread
        resized_annotated_image = resize_image_to_fixed(img, self.target_width, self.target_height) 
        
        # Schedule the UI update on the main thread without blocking the camera thread
        GLib.idle_add(self._update_cam_image, resized_annotated_image)
        
    def _update_cam_image(self, img):
        # Convert to GdkPixbuf in the main thread to be thread-safe
        pixbuf = self.cv2_to_gdkpixbuf(img)
        # Update the GTK Image or any UI component
        self.annotated_img_frame.set_from_pixbuf(pixbuf)
        return False
    
    def cv2_to_gdkpixbuf(self, cv2_image):
        image = Image.fromarray(cv2.cvtColor(cv2_image, cv2.COLOR_BGR2RGB))
        arr = np.array(image)
        height, width, channels = arr.shape
        pixbuf = GdkPixbuf.Pixbuf.new_from_data(
            arr.tobytes(), GdkPixbuf.Colorspace.RGB, False, 8, width, height, width * channels)
        return pixbuf
    
    def update_reference_image(self, next_sequence):
        reference_image = self.get_reference_image(next_sequence)
        resized_reference_image = resize_image_to_fixed(reference_image, self.target_width, self.target_height)
        GLib.idle_add(self._update_reference_image, resized_reference_image )
                 
    def _update_reference_image(self, img):
        self.reference_img_frame.set_from_pixbuf(self.cv2_to_gdkpixbuf(img))
        return False
    
    
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
                message_image = resize_image_to_fixed(message_image, self.target_width, self.target_height/7 )
                GLib.idle_add(self._update_message_images,  message_image)
                # self.message_img_frame.set_from_pixbuf(pixbuf_reference)
            except Exception as e:
                print('Message image reading error', e )
                traceback.print_exc()
            time.sleep(1)
        return False
            
    def _update_message_images(self,img):
        self.message_img_frame.set_from_pixbuf(self.cv2_to_gdkpixbuf(img))
        return False
     
    def handle_detection_result(self, detection_result, image ):
        annotated_image = draw_landmarks_on_image(image, detection_result)
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
                    args = {'args': f'{clasfy_result} {int(conf*100)}%' }
                    # threading.Thread(target=write_inspection_on_image, args=(croped_image,args,)).start()
            if self.debug:
                pass
                # print(f'Det time - pose:{det_time} -  tflite-edge: {(time.monotonic() - start ) * 1000} Tread #:{num_uncompleted_threads} FPS: {frame_rate}')
            
        position_notes  = f"Dp:{self.detected_position}: {self.counter}/{len(self.current_sequence)}-{yzmodel_result}- FPS:{frame_rate:.0f}"
        return annotated_image, position_notes
    
    def display_position_on_image(self, image, detected_position, next_position, position_notes=None):
        # Get the position name from the mapping
        position_name = position_names.get(detected_position, "")
        next_poz = position_names.get(next_position, "")
        # Put the detected position name on the image
        if self.debug:
            h,w,_ = image.shape 
            cv2.putText(image, f"{position_name}", (5, h-50), cv2.FONT_HERSHEY_SIMPLEX, 4, (0, 255, 0), 4)
            cv2.putText(image, position_notes, (10, 50), cv2.FONT_HERSHEY_SIMPLEX, 1.5 , (0, 0, 255), 4)
        self.update_message1(next_poz)
        return image
                
    
    def on_debug_toggled(self, checkbutton):
        # Set the DEBUG value based on the checkbox state
        self.debug = checkbutton.get_active()
    
    def update_message1(self, new_text):
        self.message_box1.set_text('SONRAKI- ' +  new_text.upper())

    def update_message2(self, new_text):
        self.message_box2.set_text(new_text)
                    
    def calculate_frame_rate(self):
        # Calculate the frame rate
        current_time = time.time()
        time_taken = current_time - self.last_time
        frame_rate = 1 / time_taken if time_taken != 0 else 0
        self.last_time = current_time
        return frame_rate
    
    def setup_camera(self,):
        if hasattr(self, 'cap'):
            if self.cap is None or not self.cap.isOpened():
                self.cap = cv2.VideoCapture(self.cam_no)  # Assuming 0 is the id for your primary camera
                self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.target_width)
                self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.target_height)
                if not self.cap.isOpened():
                    print("Error: Kamera Açılamadı")
                    return
        else:
            self.cap = cv2.VideoCapture(self.cam_no)
            if not self.cap.isOpened():
                print("Error: Kamera açılamadı.")
                return        
    
    def on_back_clicked(self, button, page):        
        self.close_cap_and_sound()
        self.remove(self.get_child())
        if page=="page_1":
            self.show_gender_buttons()
        if page=="page_2":
            self.show_prayering_time_buttons()
                    
    def close_cap_and_sound(self):
        # Stop any playing sounds with GStreamer
        if hasattr(self, 'player') and self.player:
            self.player.set_state(Gst.State.NULL)  # Stop playing and set state to NULL
        
        # Release OpenCV capture
        if hasattr(self, 'cap') and self.cap:
            self.cap.release()

    def on_exit_clicked(self, button=None):  # button might be None if called without a button event
        self.close_cap_and_sound()
        # Exit the application
        Gtk.main_quit()
        
if __name__ == "__main__":
    win = PrayerApp()
    win.connect("destroy", Gtk.main_quit)
    win.show_all()
    Gtk.main()

