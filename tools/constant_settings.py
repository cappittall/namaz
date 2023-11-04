
from tools.prayer_positions import PrayerPositions

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
    PrayerPositions.RUKU, PrayerPositions.NIYET_S, PrayerPositions.SECDE, 
    PrayerPositions.KADE_S, PrayerPositions.SECDE, PrayerPositions.KIYAM2, 
    PrayerPositions.RUKU, PrayerPositions.NIYET_S, PrayerPositions.SECDE, 
    PrayerPositions.KADE_S, PrayerPositions.SECDE, PrayerPositions.KADE, 
    PrayerPositions.RLSELAM, PrayerPositions.SON
]

oglen_namazi_4 = [
    PrayerPositions.NIYET, PrayerPositions.TEKBIR, PrayerPositions.KIYAM, PrayerPositions.RUKU, 
    PrayerPositions.NIYET_S, PrayerPositions.SECDE, PrayerPositions.KADE_S, PrayerPositions.SECDE, 
    PrayerPositions.KIYAM2, 
    PrayerPositions.RUKU, PrayerPositions.NIYET_S,  PrayerPositions.SECDE,PrayerPositions.KADE_S, 
    PrayerPositions.SECDE,PrayerPositions.KADE,  PrayerPositions.KIYAM2, PrayerPositions.RUKU, 
    PrayerPositions.NIYET_S, PrayerPositions.SECDE, PrayerPositions.KADE_S, PrayerPositions.SECDE, 
    PrayerPositions.KIYAM3, PrayerPositions.RUKU, PrayerPositions.NIYET_S, PrayerPositions.SECDE,
    PrayerPositions.KADE_S, PrayerPositions.SECDE, PrayerPositions.KADE2,  
    PrayerPositions.RLSELAM, PrayerPositions.SON
]

ikindi_namazi_4 = oglen_namazi_4

aksam_namazi_3 = [
    PrayerPositions.NIYET, PrayerPositions.TEKBIR, PrayerPositions.KIYAM, PrayerPositions.RUKU,  
    PrayerPositions.NIYET_S, PrayerPositions.SECDE, PrayerPositions.KADE_S, PrayerPositions.SECDE, 
    PrayerPositions.KIYAM2, 
    PrayerPositions.RUKU, PrayerPositions.NIYET_S, PrayerPositions.SECDE, PrayerPositions.KADE_S, 
    PrayerPositions.SECDE, PrayerPositions.KADE, PrayerPositions.KIYAM, PrayerPositions.RUKU,
    PrayerPositions.NIYET_S, PrayerPositions.SECDE, PrayerPositions.KADE_S, PrayerPositions.SECDE,
    PrayerPositions.KADE2, PrayerPositions.KIYAM3, PrayerPositions.RUKU, PrayerPositions.NIYET_S, 
    PrayerPositions.SECDE, PrayerPositions.KADE_S, PrayerPositions.SECDE, PrayerPositions.KADE3,
    PrayerPositions.RLSELAM, PrayerPositions.SON
]

yatsi_namazi_4 = oglen_namazi_4


position_names = {
    PrayerPositions.ALL: "None",
    PrayerPositions.NIYET: "Niyet etme",
    PrayerPositions.NIYET_S:"Ara Dogrulma",
    PrayerPositions.TEKBIR: "Tekbir",
    PrayerPositions.KIYAM: "Kiyam",
    PrayerPositions.KIYAM2: "Kiyam",
    PrayerPositions.KIYAM3: "Kiyam",
    PrayerPositions.RUKU: "Ruku",
    PrayerPositions.SECDE: "Secde",
    PrayerPositions.KADE: "Kade-Oturma",
    PrayerPositions.KADE2: "Kade-Oturma",
    PrayerPositions.KADE3: "Kade-Oturma",
    PrayerPositions.KADE_S:"Ara oturma", #
    PrayerPositions.RLSELAM: "Saga-Sola Selam",
    PrayerPositions.SON: "Bitti",    
}

sabah_manazi_timeline = {
    PrayerPositions.NIYET: (0,2),
    PrayerPositions.TEKBIR: (2, 6),
    PrayerPositions.KIYAM:(7, 2*60 + 36),
    PrayerPositions.RUKU:(2*60 + 38, 2*60+ 51),
    
    PrayerPositions.NIYET_S:(2*60 + 51, 2*60 + 57),
    PrayerPositions.SECDE:(3*60, 3*60 + 11),
    PrayerPositions.KADE_S:(3*60 + 11, 3*60 + 16),
    
    PrayerPositions.KIYAM2:(3*60 + 33, 5*60 + 41),
    PrayerPositions.KADE:(6*60 + 35, 9*60 + 53 ),
    PrayerPositions.RLSELAM:(9*60 + 54, 10*60 + 3),
    
    PrayerPositions.SON:(9*60 + 54, 10*60 + 3 )
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
    PrayerPositions.NIYET_S:f'data/position_images/[gender]/niyet_position.png',
    PrayerPositions.TEKBIR: f'data/position_images/[gender]/tekbir_position.png',
    PrayerPositions.KIYAM: f'data/position_images/[gender]/kiyam_position.png',
    PrayerPositions.KIYAM2: f'data/position_images/[gender]/kiyam_position.png',
    PrayerPositions.KIYAM3: f'data/position_images/[gender]/kiyam_position.png',
    PrayerPositions.RUKU: f'data/position_images/[gender]/ruku_position.png',
    PrayerPositions.SECDE: f'data/position_images/[gender]/secde_position.png',
    PrayerPositions.SECDE: f'data/position_images/[gender]/secde_position.png',
    PrayerPositions.KADE: f'data/position_images/[gender]/kade_position.png',
    PrayerPositions.KADE2: f'data/position_images/[gender]/kade_position.png',
    PrayerPositions.KADE3: f'data/position_images/[gender]/kade_position.png',
    PrayerPositions.KADE_S: f'data/position_images/[gender]/kade_position.png',
    PrayerPositions.RLSELAM: f'data/position_images/[gender]/rlselam_position.png',
    PrayerPositions.SON: f'data/position_images/[gender]/tebrikler.jpg',
}