import os
import time
import pygame

# Load the sound file

pygame.init()

# Initialize mixer and load OGG file
pygame.mixer.init()
sound = pygame.mixer.music
sound.load("data/sounds/sabah.ogg")

# Play from 20 to 40 seconds
sound.play(start=30)
time.sleep(20)  # let it play for 20 seconds
sound.stop()

# Some conditions here, for demonstration using time.sleep
time.sleep(1)  

# Play from 45 to 55 seconds
sound.play(start=45)
time.sleep(10)  # let it play for 10 seconds
sound.stop()

# Some conditions here, for demonstration using time.sleep
time.sleep(1)

# Play from your desired start time to end time, say 1 to 10 seconds
pygame.mixer.music.play(start=1)
time.sleep(9)  # let it play for 9 seconds
pygame.mixer.music.stop()