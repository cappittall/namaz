
from .prayer_positions import PrayerPositions

# Constants
# Define thresholds as dictionaries
thresholds_xs= 0.01
thresholds_s = 0.05
thresholds_m = 0.10
thresholds_l = 0.15
thresholds_xl = 0.20

last_time = 0
min_stable_time = 1  # Time in seconds
# sabah namazı position order
sabah_namazi_2 =  [
    PrayerPositions.NIYET, PrayerPositions.TEKBIR, PrayerPositions.KIYAM, 
    PrayerPositions.RUKU, PrayerPositions.NIYET, PrayerPositions.SECDE, 
    PrayerPositions.KADE, PrayerPositions.SECDE, PrayerPositions.KIYAM, 
    PrayerPositions.RUKU, PrayerPositions.NIYET, PrayerPositions.SECDE, 
    PrayerPositions.KADE, PrayerPositions.SECDE, PrayerPositions.KADE, 
    PrayerPositions.LRSELAM, PrayerPositions.SON
]

oglen_namazi_4 = [
    PrayerPositions.NIYET, PrayerPositions.TEKBIR, PrayerPositions.KIYAM, PrayerPositions.RUKU, 
    PrayerPositions.NIYET, PrayerPositions.SECDE, PrayerPositions.KADE, PrayerPositions.SECDE, 
    PrayerPositions.KIYAM, 
    PrayerPositions.RUKU, PrayerPositions.NIYET,  PrayerPositions.SECDE,PrayerPositions.KADE, 
    PrayerPositions.SECDE,PrayerPositions.KADE,  PrayerPositions.KIYAM, PrayerPositions.RUKU, 
    PrayerPositions.NIYET, PrayerPositions.SECDE, PrayerPositions.KADE, PrayerPositions.SECDE, 
    PrayerPositions.KIYAM, PrayerPositions.RUKU, PrayerPositions.NIYET, PrayerPositions.SECDE,
    PrayerPositions.KADE, PrayerPositions.SECDE, PrayerPositions.KADE, 
    PrayerPositions.LRSELAM, PrayerPositions.SON
]

ikindi_namazi_4 = oglen_namazi_4

aksam_namazi_3 = [
    PrayerPositions.NIYET, PrayerPositions.TEKBIR, PrayerPositions.KIYAM, PrayerPositions.RUKU,  
    PrayerPositions.NIYET, PrayerPositions.SECDE, PrayerPositions.KADE, PrayerPositions.SECDE, 
    PrayerPositions.KIYAM, 
    PrayerPositions.RUKU, PrayerPositions.NIYET, PrayerPositions.SECDE, PrayerPositions.KADE, 
    PrayerPositions.SECDE, PrayerPositions.KADE, PrayerPositions.KIYAM, PrayerPositions.RUKU,
    PrayerPositions.NIYET, PrayerPositions.SECDE, PrayerPositions.KADE, PrayerPositions.SECDE,
    PrayerPositions.KADE, PrayerPositions.KIYAM, PrayerPositions.RUKU, PrayerPositions.NIYET, 
    PrayerPositions.SECDE, PrayerPositions.KADE, PrayerPositions.SECDE, PrayerPositions.KADE,
    PrayerPositions.LRSELAM, PrayerPositions.SON
]

yatsi_namazi_4 = oglen_namazi_4


position_names = {
    PrayerPositions.ALL: "None",
    PrayerPositions.NIYET: "Niyet",
    PrayerPositions.TEKBIR: "Tekbir",
    PrayerPositions.KIYAM: "Kiyam",
    PrayerPositions.RUKU: "Ruku",
    PrayerPositions.SECDE: "Secde",
    PrayerPositions.KADE: "Kade-oturus",
    PrayerPositions.LRSELAM: "Saga-Sola Selam",
    PrayerPositions.SON: "Bitti",
    
}

sabah_manazi_timeline = {
    PrayerPositions.NIYET: (0, 13 ),
    PrayerPositions.TEKBIR: (25, 28),
    PrayerPositions.KIYAM:(35, 38),
    PrayerPositions.RUKU:(58, 61),
    PrayerPositions.SECDE:(74 ,77 ),
    PrayerPositions.KADE:(173, 176),
    PrayerPositions.LRSELAM:(180, 183),
    PrayerPositions.SON:(190,195)

}

sabah_dualari = {
    PrayerPositions.ALL: 'data/sounds/sabah1.ogg',

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
    PrayerPositions.LRSELAM: f'data/position_images/[gender]/lrselam_position.png',
    PrayerPositions.SON: f'data/position_images/[gender]/tebrikler.jpg',
}