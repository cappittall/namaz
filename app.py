import time
import threading
import cv2
from PIL import Image
import gi
from tools.constant_settings import * 
from helper import *
import mediapipe as mp
# initialize Gtk
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, Gdk, GdkPixbuf, GLib

# Initialize Pose and audio
model_path = 'models/mp/pose_landmarker_full.task'

BaseOptions = mp.tasks.BaseOptions
PoseLandmarker = mp.tasks.vision.PoseLandmarker
PoseLandmarkerOptions = mp.tasks.vision.PoseLandmarkerOptions
VisionRunningMode = mp.tasks.vision.RunningMode

options = PoseLandmarkerOptions(num_poses=1, 
                                min_pose_detection_confidence=0.25,
                                min_pose_presence_confidence=0.25,
                                min_tracking_confidence=0.25,
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
                                prayer_time, (None, None))
    
    return current_sequence, current_prayer_sounds, timeline
    
def resize_image(image, target_height, target_width):
    dH, dW = target_height - image.shape[0], target_width - image.shape[1]
    if dH < 0 or dW < 0:
        aspect_ratio = image.shape[1] / float(image.shape[0])
        new_width = target_width if dW < dH else int(target_height * aspect_ratio)
        new_height = target_height if dH < dW else int(target_width / aspect_ratio)
        image = cv2.resize(image, (new_width, new_height))
    return image

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
        self.sound = pygame.mixer.music
        self.sound_end_check = True
        self.namaz_timeline = None
        self.current_prayer_sounds = None
        
        # Resize the images
        self.target_width, self.target_height = 640, 480  # Desired dimensions
        
        # Initialize camera
        self.cap = cv2.VideoCapture(0)
                
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
        button {
            background: yellow;
            color: black;
            font-size: 30px;
            margin: 10px 200px;
            padding: 10px 50px;
        }
        window {
            background: green;
            
            
        }
        '''
        load_dynamic_css(css)
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=20)

        # Add back button
        button_back = Gtk.Button(label="GERİ")

        button_back.connect("clicked", self.on_back_clicked)
        box.pack_start(button_back, False, False, 0)

        for prayer in ["Sabah", "Öğle", "İkindi", "Akşam", "Yatsı"]:
            button = Gtk.Button(label=prayer)
            button.set_size_request(-1, int(self.get_allocated_height() * 0.125))  # Set to half height
            align = Gtk.Alignment(xalign=0.5, yalign=0.5)
            align.add(button)
            button.connect("clicked", self.on_prayer_type_selected, prayer)
            box.add(align)
        
        self.add_exit_button(box)  # Add exit button
        self.add(box)
        self.show_all()

    def on_prayer_type_selected(self, button, prayer):
        self.prayer_type = prayer
        self.remove(self.get_child())
        
        self.grid = Gtk.Grid()
        self.add(self.grid)
        # Gtk.Image widget to display the camera frame
        self.cam_frame = Gtk.Image()
        self.grid.attach(self.cam_frame, 0, 0, 1, 1)

        # Gtk.Image widget to display the position to be taken next
        self.next_position_frame = Gtk.Image()
        self.grid.attach(self.next_position_frame, 1, 0, 1, 1)
        threading.Thread(target=self.run_main_code).start()
        
    def run_main_code(self, ):

        current_sequence, current_prayer_sounds, namaz_timeline = load_squences(self.prayer_type)
        
        self.current_prayer_sounds = current_prayer_sounds
        self.namaz_timeline = namaz_timeline
        
        position_iterator = iter(current_sequence)
        try:
            initial_position = next(position_iterator)
            self.next_position = next(position_iterator)
        except StopIteration:
            print("Namaz bitti.")
            return
        
        self.update_reference_image(initial_position)

        self.sound.load(self.current_prayer_sounds.get(PrayerPositions.ALL, None))
        # Start initial sound and update the reference image when it finishes
        threading.Thread(target=self.play_sound, args=(initial_position, lambda: self.update_reference_image(self.next_position))).start()
 
        ## Start looping 
        while self.cap.isOpened():
            ret, image = self.cap.read()
            if not ret:
                print("Boş frame i geç ")
                continue
            

            detection_result = get_landmarks_infrance(image.copy(), landmarker)
            
            # draw landmarks on image           
            if detection_result:
                annotated_image = draw_landmarks_on_image(image, detection_result)
                
                if detection_result.pose_landmarks:
                    self.current_position = check_position(detection_result.pose_landmarks, self.gender)
                    
                    if self.current_position == self.next_position and self.sound_end_check: 
                        position_note = "✔️ DOGRU"
                    else: position_note = "" 
                
                    # Write current position name on frame.
            annotated_image = self.display_position_on_image(annotated_image, self.current_position, self.next_position, position_notes=position_note)
                                                                                
            if self.current_position != self.previous_position and \
                    self.current_position == self.next_position and \
                    self.current_position is not None and self.sound_end_check:
                        
                self.previous_position = self.current_position    
                                         
                try:
                    self.next_position = next(position_iterator)
                    self.update_reference_image(self.next_position)
                except StopIteration:
                    print("Sequence completed.")
                    break
                
                threading.Thread(target=self.play_sound, args=(self.next_position,)).start()
                                
            resized_annotated_image = resize_image_to_fixed(annotated_image, self.target_width, self.target_height)          
            pixbuf_annotated = self.cv2_to_gdkpixbuf(resized_annotated_image)
            GLib.idle_add(self.cam_frame.set_from_pixbuf, pixbuf_annotated)

            self.show_all()
            while Gtk.events_pending():
                Gtk.main_iteration()                           
            
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
        if self.sound and time_period:
            start, stop = time_period
            self.sound.play( start = start )
            time.sleep( stop - start )
            self.sound.stop()
                        
        """ for devided music for each sequence
        self.sound = self.current_prayer_sounds.get(sequence)        
        if self.sound:
            self.sound.play()
            while pygame.mixer.get_busy():
                pass """
            
        self.sound_end_check = True

        if callback:
            callback()
        
    def update_reference_image(self, next_sequence):
        
        reference_image = self.get_reference_image(next_sequence)
        resized_reference_image = resize_image_to_fixed(reference_image, self.target_width, self.target_height)
        pixbuf_reference = self.cv2_to_gdkpixbuf(resized_reference_image)
        GLib.idle_add(self.next_position_frame.set_from_pixbuf, pixbuf_reference)
        self.show_all() 
        
    def display_position_on_image(self, image, detected_position, next_position, position_notes=None):
        # Get the position name from the mapping
        position_name = position_names.get(detected_position, "")
        next_poz = position_names.get(next_position, "")
        # Put the detected position name on the image
        cv2.putText(image, f"Poz: {position_name}", (5, 400), cv2.FONT_HERSHEY_SIMPLEX, 3, (0, 255, 0), 2)
        cv2.putText(image, f"Nxt: {next_poz}", (5, 480), cv2.FONT_HERSHEY_SIMPLEX, 3, (0, 255, 0), 2)
        
        # If there are notes for the detected position, display them too
        if position_notes:
            cv2.putText(image, position_notes, (10, 70), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
        
        return image
    
    def on_back_clicked(self, button):
        self.remove(self.get_child())
        self.show_gender_buttons()
        
    def add_exit_button(self, box):
        button_exit = Gtk.Button(label="Çıkış")
        button_exit.connect("clicked", self.on_exit_clicked)
        box.pack_end(button_exit, False, False, 0)
        
    def on_exit_clicked(self, button):
        Gtk.main_quit()
        
if __name__ == "__main__":
    win = PrayerApp()
    win.connect("destroy", Gtk.main_quit)
    win.show_all()
    Gtk.main()

