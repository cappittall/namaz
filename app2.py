import threading
import pygame
import subprocess
import sys
from loop import CameraLoop
# Initialize Pygame
pygame.init()

# Set up the screen (fullscreen for kiosk mode)
screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
screen_width, screen_height = screen.get_size()

# Colors and Fonts
GREEN = (0, 255, 0)
YELLOW = (255, 255, 0)
BLACK = (0, 0, 0)
FONT = pygame.font.Font(None, 36)

# Button dimensions and positions
button_width = int(screen_width * 0.45)
button_height = int(screen_height * 0.9)
button_y = int(screen_height * 0.05)
total_buttons_width = button_width * 2 + int(screen_width * 0.05)
side_margin = (screen_width - total_buttons_width) // 2
button_x_male = side_margin
button_x_female = button_x_male + button_width + int(screen_width * 0.05)

# Gender Buttons
gender_buttons = [
    {"rect": pygame.Rect(button_x_male, button_y, button_width, button_height), "label": "ERKEK"},
    {"rect": pygame.Rect(button_x_female, button_y, button_width, button_height), "label": "KADIN"}
]

# Back and Exit Buttons
back_button = pygame.Rect(10, 10, 100, 50)
exit_button = pygame.Rect(screen_width - 110, 10, 100, 50)
back_button_text = FONT.render("Geri", True, BLACK)
exit_button_text = FONT.render("Çıkış", True, BLACK)

# Title for time selection
title_text = "NAMAZ SAATİNİ SEÇİNİZ"
title_button_width = screen_width - 300  # Reduced from the width of the screen by the width of both buttons and some padding
title_button = pygame.Rect(150, 10, title_button_width, 50)
title_surf = FONT.render(title_text, True, BLACK)
title_rect = title_surf.get_rect(center=title_button.center)

# Time Buttons
prayer_times = ["Sabah", "Öğle", "İkindi", "Akşam", "Yatsı"]
time_button_width = int(screen_width * 0.4)
time_button_height = 100
time_button_y = title_button.bottom + 20
time_side_margin = (screen_width - time_button_width) // 2
time_buttons = [{"rect": pygame.Rect(time_side_margin, time_button_y + i*120, time_button_width, time_button_height), "label": time} for i, time in enumerate(prayer_times)]

# Checkbox dimensions and position
checkbox_size = 20
checkbox_x = 20  # You can adjust this position
checkbox_y = screen_height - 30  # Place it at the bottom left
checkbox_rect = pygame.Rect(checkbox_x, checkbox_y, checkbox_size, checkbox_size)
checkbox_checked = False  # Initially, the checkbox is unchecked

# Define the "Debug" text
debug_text = FONT.render("Debug", True, BLACK)
debug_text_rect = debug_text.get_rect()
debug_text_rect.left = checkbox_rect.right + 10  # Add some space after the checkbox
debug_text_rect.centery = checkbox_rect.centery

# State variables
selected_gender = None
selected_time = None
debug_mode = False

# Function to start the camera loop
def start_camera_loop(gender, prayer_time, debug):
    camera_loop = CameraLoop(gender, prayer_time, debug)
    camera_loop_thread = threading.Thread(target=camera_loop.run)
    camera_loop_thread.daemon = True  # Daemon thread will close when main thread exits
    camera_loop_thread.start()
    
# Main loop
running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if selected_gender is None:
                for button in gender_buttons:
                    if button["rect"].collidepoint(event.pos):
                        selected_gender = button["label"]
                        break
            else:
                if back_button.collidepoint(event.pos):
                    selected_gender = None
                    continue
                if exit_button.collidepoint(event.pos):
                    running = False
                    break
                for button in time_buttons:
                    if button["rect"].collidepoint(event.pos):
                        selected_time = button["label"]
                        gender_arg = "e" if selected_gender == "ERKEK" else "k"
                        debug_arg = "1" if debug_mode else "0"
                        subprocess.Popen(["python", "loop.py", gender_arg, selected_time, debug_arg])
                        # subprocess.run(["python", "loop.py", gender_arg, selected_time, debug_arg])
                        running = False
                        break

    screen.fill(GREEN)
    if selected_gender is None:
        for button in gender_buttons:
            pygame.draw.rect(screen, YELLOW, button["rect"])
            label = FONT.render(button["label"], True, BLACK)
            label_rect = label.get_rect(center=(button["rect"].x + button_width // 2, button["rect"].y + button_height // 2))
            screen.blit(label, label_rect)
    else:
        pygame.draw.rect(screen, YELLOW, back_button)
        pygame.draw.rect(screen, YELLOW, exit_button)
        pygame.draw.rect(screen, YELLOW, title_button)
        screen.blit(back_button_text, back_button_text.get_rect(center=back_button.center))
        screen.blit(exit_button_text, exit_button_text.get_rect(center=exit_button.center))
        screen.blit(title_surf, title_rect)
        for button in time_buttons:
            pygame.draw.rect(screen, YELLOW, button["rect"])
            label = FONT.render(button["label"], True, BLACK)
            label_rect = label.get_rect(center=button["rect"].center)  # Center the text
            screen.blit(label, label_rect)
            
        # Draw the checkbox
        pygame.draw.rect(screen, YELLOW, checkbox_rect, 2)  # Draw the border
        # Draw the "Debug" text next to the checkbox
        screen.blit(debug_text, debug_text_rect)
        if checkbox_checked:
            pygame.draw.line(screen, YELLOW, (checkbox_x, checkbox_y), (checkbox_x + checkbox_size, checkbox_y + checkbox_size), 2)  # Diagonal line 1
            pygame.draw.line(screen, YELLOW, (checkbox_x, checkbox_y + checkbox_size), (checkbox_x + checkbox_size, checkbox_y), 2)  # Diagonal line 2

        # Handle checkbox click
        if event.type == pygame.MOUSEBUTTONDOWN:
            if checkbox_rect.collidepoint(event.pos):
                checkbox_checked = not checkbox_checked
                debug_mode = checkbox_checked


    pygame.display.flip()

pygame.quit()
sys.exit()
