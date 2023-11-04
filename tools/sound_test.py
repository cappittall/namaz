# RUN: python -m tools.sound_test

from tools.constant_settings import *
from tools.helper import *

import pygame.mixer

pygame.mixer.init()

current_sequence, current_prayer_sounds, namaz_timeline = load_squences('Sabah')

print('current_sequence',  current_sequence)
print('current_prayer_sounds', current_prayer_sounds)
print('namaz_timeline', namaz_timeline )

pygame.mixer.music.load(current_prayer_sounds.get(PrayerPositions.ALL, None))

def play_sound(sequence):
    # For timeline playlist exist from one file 
    time_period = sabah_manazi_timeline.get(sequence, None)  
    print(time_period)      
    if time_period:
        try:
            start, stop = time_period
            if DEBUG:  # For long perion make it shorter
                stop = start+5 if (stop - start) > 30 else stop
                
            pygame.mixer.music.play(start = start)
            time.sleep( stop - start )
            pygame.mixer.music.stop()
        except Exception as e:
            print('Hata , ', e )


play_sound(PrayerPositions.RLSELAM)
