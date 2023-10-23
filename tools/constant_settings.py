
from tools.prayer_positions import PrayerPositions
import pygame
pygame.init()

# Constants
# Define thresholds as dictionaries
thresholds_xs= 0.01
thresholds_s = 0.05
thresholds_m = 0.10
thresholds_l = 0.15
thresholds_xl = 0.20

last_time = 0
min_stable_time = 1  # Time in seconds

sabah_namazi_2 =  [
    PrayerPositions.NIYET, PrayerPositions.TEKBIR,
    PrayerPositions.KIYAM, 
    PrayerPositions.RUKU, PrayerPositions.SECDE, 
    PrayerPositions.KADE, PrayerPositions.SECDE, PrayerPositions.KIYAM, 
    PrayerPositions.RUKU, PrayerPositions.SECDE, 
    PrayerPositions.KADE, PrayerPositions.SECDE, PrayerPositions.KADE, 
    PrayerPositions.RSELAM, PrayerPositions.LSELAM
]

oglen_namazi_4 = [
    PrayerPositions.NIYET, PrayerPositions.TEKBIR, PrayerPositions.KIYAM, PrayerPositions.RUKU, 
    PrayerPositions.SECDE, PrayerPositions.KADE, PrayerPositions.SECDE, PrayerPositions.KIYAM, 
    PrayerPositions.RUKU,  PrayerPositions.SECDE,PrayerPositions.KADE, 
    PrayerPositions.SECDE,PrayerPositions.KADE, PrayerPositions.KIYAM, PrayerPositions.RUKU, 
    PrayerPositions.SECDE, PrayerPositions.KADE, PrayerPositions.SECDE, 
    PrayerPositions.KIYAM, PrayerPositions.RUKU, PrayerPositions.SECDE,
    PrayerPositions.KADE, PrayerPositions.SECDE,PrayerPositions.KADE, 
    PrayerPositions.RSELAM, PrayerPositions.LSELAM  
]

ikindi_namazi_4 = oglen_namazi_4

aksam_namazi_3 = [
    PrayerPositions.NIYET, PrayerPositions.TEKBIR, PrayerPositions.KIYAM, PrayerPositions.RUKU,  
    PrayerPositions.SECDE, PrayerPositions.KADE, PrayerPositions.SECDE, PrayerPositions.KIYAM, 
    PrayerPositions.RUKU,  PrayerPositions.SECDE, PrayerPositions.KADE, 
    PrayerPositions.SECDE, PrayerPositions.KADE, PrayerPositions.KIYAM, PrayerPositions.RUKU,
    PrayerPositions.SECDE, PrayerPositions.KADE, PrayerPositions.SECDE,
    PrayerPositions.KADE, PrayerPositions.KIYAM, PrayerPositions.RUKU, 
    PrayerPositions.SECDE, PrayerPositions.KADE, PrayerPositions.SECDE, PrayerPositions.KADE,
    PrayerPositions.RSELAM, PrayerPositions.LSELAM 
]

yatsi_namazi_4 = oglen_namazi_4

position_names = {
    PrayerPositions.ALL: "None",
    PrayerPositions.NIYET: "Niyet",
    PrayerPositions.TEKBIR: "Tekbir",
    PrayerPositions.KIYAM: "Kiyam",
    PrayerPositions.RUKU: "Ruku",
    PrayerPositions.SECDE: "Secde",
    PrayerPositions.KADE: "Kade",
    PrayerPositions.RSELAM: "Right Selam",
    PrayerPositions.LSELAM: "Left Selam"
}

sabah_manazi_timeline = {
    PrayerPositions.NIYET: (0, 34 ),
    PrayerPositions.TEKBIR: (25, 27),
    PrayerPositions.KIYAM:(35, 58),
    PrayerPositions.RUKU:(58, 73),
    PrayerPositions.SECDE:(74 ,97 ),
    PrayerPositions.KADE:(173, 180),
    PrayerPositions.RSELAM:(180, 188),
    PrayerPositions.LSELAM:(188, 193)
}

sabah_dualari = {
    PrayerPositions.ALL: 'data/sounds/sabah.ogg',

}

oglen_dualari = {
    PrayerPositions.ALL: 'data/sounds/sabah.ogg',

}
ikindi_dualari = {
    PrayerPositions.ALL: 'data/sounds/sabah.ogg',

}
aksam_dualari = {
    PrayerPositions.ALL: 'data/sounds/sabah.ogg',

}
yatsi_dualari = {
    PrayerPositions.ALL: 'data/sounds/sabah.ogg',

}

# Position to image mapping
position_to_image = {
    PrayerPositions.NIYET: f'data/position_images/[gender]/niyet_position.png',
    PrayerPositions.TEKBIR: f'data/position_images/[gender]/tekbir_position.png',
    PrayerPositions.KIYAM: f'data/position_images/[gender]/kiyam_position.png',
    PrayerPositions.RUKU: f'data/position_images/[gender]/ruku_position.png',
    PrayerPositions.SECDE: f'data/position_images/[gender]/secde_position.png',
    PrayerPositions.KADE: f'data/position_images/[gender]/kade_position.png',
    PrayerPositions.RSELAM: f'data/position_images/[gender]/rselam_position.png',
    PrayerPositions.LSELAM: f'data/position_images/[gender]/lselam_position.png',
}