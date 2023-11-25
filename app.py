import subprocess
import threading

import cv2
from tools.constant_settings import * 
from tools.helper import *


# initialize Gtk...Çok ilginç 
import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, Gdk, GdkPixbuf, GLib

try:
    # Try to import and initialize GStreamer
    gi.require_version('Gst', '1.0')
    from gi.repository import Gst
    Gst.init(None)
    use_gstreamer = True
except ImportError:
    print('Error') 
    

Gtk.init()


# from tensorflow.lite.python.interpreter import Interpreter, load_delegate
import logging

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
        self.position_change_event = threading.Event()
        self.debug = False
        # Resize the images
        self.screen = Gdk.Display.get_default().get_monitor(0).get_geometry()    
        self.target_width, self.target_height = int(self.screen.width * 0.95 / 2), int(self.screen.height * 0.7)  
              
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
        debug = "1" if self.debug else "0"
        # Launch the camera loop script with subprocess
        subprocess.Popen(["python", "loop.py", self.gender, self.prayer_time, debug])
        
        # Close the GTK application
        Gtk.main_quit()
    
    def on_back_clicked(self, button, page):        
        self.remove(self.get_child())
        if page=="page_1":
            self.show_gender_buttons()
        if page=="page_2":
            self.show_prayering_time_buttons()
        
    def on_debug_toggled(self, checkbutton):
        # Set the DEBUG value based on the checkbox state
        self.debug = checkbutton.get_active()

    def on_exit_clicked(self, button=None):  # button might be None if called without a button event
        # Exit the application
        Gtk.main_quit()
        
if __name__ == "__main__":
    win = PrayerApp()
    win.connect("destroy", Gtk.main_quit)
    win.show_all()
    Gtk.main()

