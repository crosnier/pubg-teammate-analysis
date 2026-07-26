# ==============================
# utils/map_regions_data.py
# ==============================
"""
Researched reference data for Map Drop Zone + Flow (issue #44). NOT YET
CONSUMED by any classification code - this file is the validated raw
material for that module, committed on its own so the research isn't lost.

Sourced 2026-07-25:
- Map coordinate ranges (MAP_SIZE_CM below): official PUBG API docs,
  https://documentation.pubg.com/en/rate-limits.html-adjacent telemetry
  docs (confirmed: locations are in centimeters, coordinate range scales
  with map size).
- POI names + relative positions: read directly off the official PUBG
  developer asset image (docs/design/maps/erangel_official.png, from
  github.com/pubg/api-assets - an official PUBG developer resource, no
  IP/copyright concern). Pixel positions are visual estimates against
  this 819x819px image.
- Cross-validated against REAL cached telemetry, not trusted on sourcing
  alone: for each POI's estimated world coordinate, counted real
  LogParachuteLanding events within a 400m radius across all 1,047
  cached Baltic_Main (Erangel) matches (136,247 total landings). The
  relative density ranking matches well-established PUBG community
  knowledge closely (School and Pochinki are the two most legendary
  hot-drops in the game and topped the count by a wide margin; Zharki is
  a famously dead corner and landed near-zero - see erangel_landing_
  validation below), which is strong evidence the pixel-to-world
  conversion and assumed coordinate orientation (top-left origin,
  x-right, y-down, matching telemetry's own convention) are both
  correct - not asserted on faith.

Kameshki/Stalber re-examined 2026-07-25 (resolved, was NEEDS_REVIEW):
re-cropped tight, high-zoom regions of the official image around both
pixel estimates and located each town's actual building cluster
directly - both estimates (Kameshki 655,90 / Stalber 570,115) land
within ~10px of the real cluster centroid, i.e. correctly placed. The
lower landing counts (520 / 1031) are real gameplay signal, not a
placement error: both are small, mountainous, remote NE-corner towns,
genuinely less popular drops than central POIs like Pochinki/School.
Stalber's 1031 is in line with other minor POIs (Mylta Power 1066,
Quarry 1263), so it was never actually anomalous. Kameshki's 520 is the
one real outlier low count, but consistent with it being the more
isolated of the two - not evidence of mis-mapped coordinates.

Still needed before this is classification-ready:
- Every other map (Miramar/Desert_Main, Sanhok/Savage_Main,
  Vikendi/DihorOtok_Main, Rondo/Neon_Main, etc.) - Erangel and Taego are
  done, the rest still need the same research process repeated before
  this tool can profile drops on their matches - see the "map not yet
  supported" fallback requirement in issue #44 for what should happen
  for matches on a map not yet in this file.

Taego (Tiger_Main) added 2026-07-25, second map after Erangel: same
process - official image from github.com/pubg/api-assets
(Taego_Main_Low_Res.png, also 819x819px), POI pixels read via PIL crops
(sips's --cropOffset turned out to NOT be top-left-relative as assumed
during Erangel's research - it's centered on the source image and shifts
from there; this was caught and corrected before Taego's crops were
taken, and Erangel's Kameshki/Stalber placements were independently
re-verified with reliable PIL crops afterward to confirm that earlier
mistake never actually produced wrong coordinates - see
TAEGO_POI_PIXELS's crop method below, which all future maps should
reuse), cross-validated against 19,376 real LogParachuteLanding events
across cached Tiger_Main matches. Terminal and Palace topped the count
(3,644 / 2,732) - both well-known Taego hot-drops per community
knowledge, consistent with Erangel's School/Pochinki validation pattern.
Ha Po's count (273) sits just above the automatic NEEDS_REVIEW threshold
(271.5, half of the 543 median) - not flagged, but close enough to be
worth a second look if it ever looks off in practice.
"""

# Map coordinate ranges in centimeters (0 to this value on both x and y),
# per https://documentation.pubg.com/en - confirmed official, not guessed.
MAP_SIZE_CM = {
    "Baltic_Main": 816000,      # Erangel
    "Desert_Main": 816000,      # Miramar
    "DihorOtok_Main": 816000,   # Vikendi
    "Tiger_Main": 816000,       # Taego
    "Kiki_Main": 816000,        # Deston
    "Savage_Main": 408000,      # Sanhok
    "Chimera_Main": 306000,     # Paramo
    "Summerland_Main": 204000,  # Karakin
    "Range_Main": 204000,       # Camp Jackal - DISCONTINUED as of 2026-07-26
                                # (not in PUBG's current map rotation per
                                # pubg.com's official Map Service Report).
                                # No POI work planned; do not prioritize.
    "Heaven_Main": 102000,      # Haven - DISCONTINUED as of 2026-07-26,
                                # same source/status as Camp Jackal above.
                                # No POI work planned; do not prioritize.
    "Neon_Main": 816000,        # Rondo - confirmed 2026-07-26: max real
                                 # LogParachuteLanding coords across 112
                                 # cached matches (~793000/~791000) sit
                                 # comfortably below 816000, consistent with
                                 # every other 8x8 map in this file.
}

# Official reference map image (source: github.com/pubg/api-assets,
# Erangel_Main_Low_Res.png), used to derive the pixel->world coordinates
# below. 819x819px covering the full 0-816000cm range on both axes.
ERANGEL_IMAGE_PATH = "docs/design/maps/erangel_official.png"
ERANGEL_IMAGE_SIZE_PX = 819

# POI name -> (pixel_x, pixel_y) read directly off ERANGEL_IMAGE_PATH,
# top-left origin. Kameshki/Stalber were re-verified against tight crops
# of the source image (see docstring above) - both confirmed accurate.
ERANGEL_POI_PIXELS = {
    "Zharki": (75, 100),
    "Severny": (350, 105),
    "Kameshki": (655, 90),
    "Stalber": (570, 115),
    "Shooting Range": (330, 195),
    "Georgopol": (175, 255),
    "Yasnaya Polyana": (530, 250),
    "Rozhok": (395, 290),
    "Hospital": (140, 310),
    "Ruins": (305, 335),
    "School": (430, 330),
    "Mansion": (615, 310),
    "Lipovka": (705, 330),
    "Gatka": (225, 385),
    "Pochinki": (345, 400),
    "Shelter": (555, 375),
    "Prison": (625, 365),
    "Mylta Power": (735, 415),
    "Farm": (530, 450),
    "Mylta": (605, 460),
    "Quarry": (180, 530),
    "Ferry Pier": (290, 575),
    "Primorsk": (165, 610),
    "Sosnovka Island": (460, 600),
    "Sosnovka Military Base": (460, 660),
    "Novorepnoye": (635, 615),
}

# Real-data validation: landings within 400m (40000cm) of each POI's
# converted world coordinate, across all 1,047 cached Baltic_Main matches
# (136,247 total LogParachuteLanding events). Kept here as the evidence
# trail for the pixel estimates above, not consumed programmatically.
ERANGEL_LANDING_VALIDATION_400M = {
    "Farm": 2093, "Ferry Pier": 1788, "Gatka": 4468, "Georgopol": 4438,
    "Hospital": 3488, "Kameshki": 520, "Lipovka": 2191, "Mansion": 1337,
    "Mylta": 6011, "Mylta Power": 1066, "Novorepnoye": 2414,
    "Pochinki": 13650, "Primorsk": 2243, "Prison": 3106, "Quarry": 1263,
    "Rozhok": 6165, "Ruins": 2901, "School": 16017, "Severny": 1745,
    "Shelter": 2608, "Shooting Range": 1015, "Sosnovka Island": 2763,
    "Sosnovka Military Base": 4390, "Stalber": 1031,
    "Yasnaya Polyana": 5679, "Zharki": 23,
}


def erangel_poi_world_coordinates():
    """Convert the pixel estimates above to real telemetry-space (cm)
    coordinates. Kept as a function (not a precomputed dict) so the
    scale math stays visibly tied to ERANGEL_IMAGE_SIZE_PX / MAP_SIZE_CM
    rather than drifting out of sync if either constant changes."""
    scale = MAP_SIZE_CM["Baltic_Main"] / ERANGEL_IMAGE_SIZE_PX
    return {name: (px * scale, py * scale) for name, (px, py) in ERANGEL_POI_PIXELS.items()}


# Official reference map image (source: github.com/pubg/api-assets,
# Taego_Main_Low_Res.png). 819x819px covering the full 0-816000cm range.
TAEGO_IMAGE_PATH = "docs/design/maps/taego_official.png"
TAEGO_IMAGE_SIZE_PX = 819

# POI name -> (pixel_x, pixel_y) read directly off TAEGO_IMAGE_PATH,
# top-left origin, via reliable PIL crops (see module docstring for the
# sips --cropOffset caveat this method replaced).
TAEGO_POI_PIXELS = {
    "Army Base": (378, 114),
    "Wol Song": (153, 164),
    "Hae Moo Sa": (100, 229),
    "Go Dok": (250, 243),
    "Yong Cheon": (447, 232),
    "Shipyard": (600, 147),
    "Palace": (304, 358),
    "Fishing Camp": (252, 412),
    "Terminal": (475, 350),
    "Airport": (722, 318),
    "Ha Po": (72, 440),
    "Ho San": (347, 498),
    "Buk San Sa": (500, 498),
    "Kang Neung": (648, 440),
    "Ho San Prison": (187, 582),
    "School": (313, 627),
    "Song Am": (408, 662),
    "Oh Hyang": (577, 600),
    "Hospital": (562, 673),
}

# Real-data validation: landings within 400m (40000cm) of each POI's
# converted world coordinate, across all cached Tiger_Main matches
# (19,376 total LogParachuteLanding events). Kept here as the evidence
# trail for the pixel estimates above, not consumed programmatically.
TAEGO_LANDING_VALIDATION_400M = {
    "Terminal": 3644, "Palace": 2732, "Ho San": 2026, "Buk San Sa": 1980,
    "Yong Cheon": 1334, "Kang Neung": 962, "Go Dok": 927, "Airport": 816,
    "School": 726, "Fishing Camp": 543, "Shipyard": 518, "Oh Hyang": 470,
    "Song Am": 445, "Ho San Prison": 436, "Hospital": 429, "Army Base": 414,
    "Wol Song": 351, "Hae Moo Sa": 350, "Ha Po": 273,
}


def taego_poi_world_coordinates():
    """Convert the pixel estimates above to real telemetry-space (cm)
    coordinates - same approach as erangel_poi_world_coordinates()."""
    scale = MAP_SIZE_CM["Tiger_Main"] / TAEGO_IMAGE_SIZE_PX
    return {name: (px * scale, py * scale) for name, (px, py) in TAEGO_POI_PIXELS.items()}


# Official reference map image (source: github.com/pubg/api-assets,
# Miramar_Main_Low_Res.png). 819x819px covering the full 0-816000cm range.
MIRAMAR_IMAGE_PATH = "docs/design/maps/miramar_official.png"
MIRAMAR_IMAGE_SIZE_PX = 819

# POI name -> (pixel_x, pixel_y) read directly off MIRAMAR_IMAGE_PATH,
# top-left origin, via PIL crops. 9 of 28 POIs came back NEEDS_REVIEW on
# validation below (a much bigger fraction than Erangel/Taego's one-or-
# none) - spot-checked the two hardest-to-locate ones (Oasis, Crater
# Fields) with a fresh high-zoom crop and both landed within 15px of the
# stored estimate, i.e. correctly placed. The flagged cluster is
# concentrated in Miramar's north/inland region (Oasis, Crater Fields,
# Alcantara, La Cobreria, Cruz del Valle, Tierra Bronca) plus a few far
# coastal corners (Puerto Paraiso, Valle del Mar, Prison) - this matches
# well-documented PUBG community knowledge that Miramar's north sees far
# less real traffic than the Pecado/Los Leones/San Martin/Hacienda del
# Patron southern corridor. Treated as real gameplay signal, not a
# placement error, same conclusion pattern as Erangel's Kameshki.
MIRAMAR_POI_PIXELS = {
    "Oasis": (350, 60),
    "La Cobreria": (252, 115),
    "Alcantara": (90, 220),
    "Crater Fields": (343, 190),
    "El Pozo": (155, 290),
    "Campo Militar": (563, 60),
    "Tierra Bronca": (670, 117),
    "Cruz del Valle": (530, 150),
    "Water Treatment": (430, 190),
    "San Martin": (363, 283),
    "Hacienda del Patron": (463, 280),
    "El Azahar": (643, 240),
    "Truck Stop": (613, 318),
    "Power Grid": (280, 360),
    "Graveyard": (445, 375),
    "Minas Generales": (517, 357),
    "Cantera": (512, 428),
    "Pecado": (373, 428),
    "Monte Nuevo": (177, 403),
    "Brick Yard": (170, 470),
    "Chumacera": (260, 543),
    "Impala": (630, 470),
    "Los Leones": (473, 563),
    "Valle del Mar": (153, 593),
    "Puerto Paraiso": (607, 603),
    "Resort": (460, 660),
    "Prison": (120, 700),
    "Partona": (343, 753),
}

# Real-data validation: landings within 400m (40000cm) of each POI's
# converted world coordinate, across all cached Desert_Main matches.
# Kept here as the evidence trail for the pixel estimates above, not
# consumed programmatically.
DESERT_MAIN_LANDING_VALIDATION_400M = {
    "Pecado": 3349, "Los Leones": 1914, "San Martin": 1750,
    "Hacienda del Patron": 1637, "Chumacera": 1092, "Minas Generales": 987,
    "Impala": 943, "Water Treatment": 814, "Monte Nuevo": 731,
    "Cantera": 678, "El Pozo": 655, "Truck Stop": 587, "El Azahar": 496,
    "Graveyard": 495, "Resort": 373, "Power Grid": 348, "Partona": 271,
    "Campo Militar": 268, "Brick Yard": 262, "Cruz del Valle": 233,
    "Valle del Mar": 227, "Oasis": 207, "Puerto Paraiso": 197,
    "Alcantara": 190, "Crater Fields": 180, "Tierra Bronca": 178,
    "La Cobreria": 155, "Prison": 141,
}


def miramar_poi_world_coordinates():
    """Convert the pixel estimates above to real telemetry-space (cm)
    coordinates - same approach as erangel_poi_world_coordinates()."""
    scale = MAP_SIZE_CM["Desert_Main"] / MIRAMAR_IMAGE_SIZE_PX
    return {name: (px * scale, py * scale) for name, (px, py) in MIRAMAR_POI_PIXELS.items()}


# Official reference map image (source: github.com/pubg/api-assets,
# Vikendi_Main_Low_Res.png). 819x819px covering the full 0-816000cm range.
VIKENDI_IMAGE_PATH = "docs/design/maps/vikendi_official.png"
VIKENDI_IMAGE_SIZE_PX = 819

# POI name -> (pixel_x, pixel_y) read directly off VIKENDI_IMAGE_PATH,
# top-left origin, via PIL crops. 5 of 16 POIs came back NEEDS_REVIEW -
# all peripheral/corner locations (Cosmodrome NE, Kranik SE, Naznova SW,
# Coal Mine NW, Pavilka S). Spot-checked Coal Mine (the lowest count,
# 121) with a fresh high-zoom crop - landed within 16px of the stored
# estimate, i.e. correctly placed. Matches real Vikendi community
# knowledge that the central towns (Train Station, Lumber Yard, Naros,
# Deka Mesto, Laveni, Castle) dominate real drop traffic while the map's
# corners see little - same "real gameplay signal, not a placement
# error" conclusion as Erangel's Kameshki and Miramar's northern cluster.
VIKENDI_POI_PIXELS = {
    "Coal Mine": (163, 177),
    "Observatory": (372, 133),
    "Cosmodrome": (610, 118),
    "Laveni": (530, 257),
    "Naros": (350, 280),
    "Dinoland": (183, 330),
    "Villa": (690, 323),
    "Lumber Yard": (260, 430),
    "Train Station": (497, 397),
    "Trika": (693, 470),
    "Naznova": (93, 497),
    "Castle": (542, 518),
    "Deka Mesto": (377, 540),
    "Kranik": (600, 640),
    "Pavilka": (193, 628),
    "Winery": (317, 667),
}

# Real-data validation: landings within 400m (40000cm) of each POI's
# converted world coordinate, across all cached DihorOtok_Main matches.
# Kept here as the evidence trail for the pixel estimates above, not
# consumed programmatically.
DIHOROTOK_MAIN_LANDING_VALIDATION_400M = {
    "Train Station": 1219, "Lumber Yard": 907, "Naros": 905,
    "Deka Mesto": 798, "Laveni": 768, "Castle": 678, "Observatory": 447,
    "Dinoland": 443, "Winery": 292, "Trika": 280, "Villa": 242,
    "Cosmodrome": 216, "Kranik": 211, "Naznova": 186, "Coal Mine": 121,
    "Pavilka": 104,
}


def vikendi_poi_world_coordinates():
    """Convert the pixel estimates above to real telemetry-space (cm)
    coordinates - same approach as erangel_poi_world_coordinates()."""
    scale = MAP_SIZE_CM["DihorOtok_Main"] / VIKENDI_IMAGE_SIZE_PX
    return {name: (px * scale, py * scale) for name, (px, py) in VIKENDI_POI_PIXELS.items()}


# Official reference map image (source: github.com/pubg/api-assets,
# Sanhok_Main_Low_Res.png). Still 819x819px like every other map's image,
# but Sanhok's own coordinate range (MAP_SIZE_CM["Savage_Main"]) is half
# the "8km" maps' - the scale math below divides by the map's own
# MAP_SIZE_CM entry, so this needs no special-casing.
SANHOK_IMAGE_PATH = "docs/design/maps/sanhok_official.png"
SANHOK_IMAGE_SIZE_PX = 819

# POI name -> (pixel_x, pixel_y) read directly off SANHOK_IMAGE_PATH,
# top-left origin, via PIL crops. Mongnai's first-pass estimate (693,167)
# was re-cropped and corrected to (662,148) after a validation spot-check
# showed a bigger-than-usual ~35px gap (vs. the ~10-16px seen on every
# other spot-checked POI so far) - re-validating with the corrected
# coordinate actually dropped Mongnai's count slightly (69 -> 63),
# confirming its low traffic is real, not an artifact of the original
# placement error. Docks (100) was also spot-checked and confirmed
# accurately placed - both Docks and Mongnai are remote coastal corners,
# consistent with the "corners are quiet" pattern seen on every map so
# far. Bootcamp's count (1,218, by far the highest) matches its
# reputation as Sanhok's single most famous hot-drop.
SANHOK_POI_PIXELS = {
    "Khao": (460, 147),
    "Mongnai": (662, 148),
    "Tat Mok": (415, 193),
    "Ha Tinh": (250, 220),
    "Paradise Resort": (503, 270),
    "Camp Alpha": (163, 320),
    "Camp Bravo": (685, 307),
    "Bootcamp": (390, 383),
    "Bhan": (587, 397),
    "Lakawi": (690, 445),
    "Ruins": (243, 513),
    "Quarry": (540, 493),
    "Kampong": (697, 570),
    "Pai Nan": (380, 540),
    "Cave": (537, 610),
    "Tambang": (160, 577),
    "Na Kham": (230, 647),
    "Camp Charlie": (477, 680),
    "Docks": (665, 690),
    "Sahmee": (300, 713),
    "Ban Tai": (483, 735),
}

# Real-data validation: landings within 400m (40000cm) of each POI's
# converted world coordinate, across all cached Savage_Main matches.
# Kept here as the evidence trail for the pixel estimates above, not
# consumed programmatically.
SAVAGE_MAIN_LANDING_VALIDATION_400M = {
    "Bootcamp": 1218, "Pai Nan": 561, "Paradise Resort": 474,
    "Ruins": 363, "Ha Tinh": 349, "Camp Bravo": 339, "Camp Alpha": 315,
    "Tat Mok": 308, "Khao": 293, "Sahmee": 243, "Quarry": 212,
    "Camp Charlie": 208, "Bhan": 207, "Ban Tai": 195, "Lakawi": 193,
    "Kampong": 155, "Na Kham": 145, "Cave": 133, "Tambang": 108,
    "Docks": 100, "Mongnai": 63,
}


def sanhok_poi_world_coordinates():
    """Convert the pixel estimates above to real telemetry-space (cm)
    coordinates - same approach as erangel_poi_world_coordinates()."""
    scale = MAP_SIZE_CM["Savage_Main"] / SANHOK_IMAGE_SIZE_PX
    return {name: (px * scale, py * scale) for name, (px, py) in SANHOK_POI_PIXELS.items()}


# Official reference map image (source: github.com/pubg/api-assets,
# Rondo_Main_Low_Res.png - note the asset filename uses Rondo's marketing
# name, not its telemetry mapName Neon_Main). 819x819px, same convention as
# every other map. MAP_SIZE_CM["Neon_Main"] confirmed 2026-07-26: real
# LogParachuteLanding coordinates across 112 cached matches top out around
# (793000, 791000), comfortably below 816000 and consistent with every
# other 8x8 map in this file - never independently stated in cm by any
# source found, so this rests on the empirical check, not sourcing alone.
RONDO_IMAGE_PATH = "docs/design/maps/rondo_official.png"
RONDO_IMAGE_SIZE_PX = 819

# POI name -> (pixel_x, pixel_y) read directly off RONDO_IMAGE_PATH,
# top-left origin, via PIL crops (see docs/design/map-poi-discovery-
# procedure.md for the exact method). Mai Hu and Jadena City's first-pass
# estimates targeted their label text rather than the actual building
# cluster - re-cropped and corrected, which raised their validated counts
# meaningfully (Mai Hu 0 -> 31, Jadena City 181 -> 217), confirming those
# were real placement errors. Hernay Town, Long Ho, Tu Ling, and Yun Su
# were also re-cropped on suspicion but barely moved (a couple actually
# ticked down slightly) - per the discovery procedure's loop-back
# criteria, that pattern means they're genuinely low-traffic rather than
# mis-placed: Hernay Town and Long Ho both sit in far map corners
# (consistent with the "corners are quiet" pattern already seen on every
# other map), and Tu Ling/Yun Su are small, sparse settlements even on
# close inspection. Bei Li and Kun Xiu flagged NEEDS_REVIEW only because
# the map median rose after Jadena City's correction, not because their
# own placement looks wrong on inspection - accepted as real geography
# (small, remote spots) rather than re-looped.
RONDO_POI_PIXELS = {
    "Mai Hu": (85, 100),
    "Nan Chuan": (232, 73),
    "Rai An": (372, 65),
    "Kun Xiu": (538, 79),
    "Mu Ho Pan": (572, 150),
    "Hernay Town": (680, 160),
    "Bei Li": (136, 196),
    "Stadium": (286, 259),
    "Bianbun": (357, 259),
    "La Hua Xing": (601, 300),
    "Test Track": (452, 329),
    "Mey Ran": (636, 329),
    "Jao Tin": (186, 314),
    "Neox Factory": (496, 391),
    "Yu Lin": (301, 429),
    "Yun Su": (635, 445),
    "Fong Tun": (101, 493),
    "Dan Ching": (511, 539),
    "Tu Ling": (575, 565),
    "Jadena City": (705, 590),
    "Hung Shan": (356, 626),
    "Rin Jiang": (276, 689),
    "Ein Long Garden": (486, 701),
    "Long Ho": (150, 700),
}

# Real-data validation: landings within 400m (40000cm) of each POI's
# converted world coordinate, across all 112 cached Neon_Main matches.
# Kept here as the evidence trail for the pixel estimates above, not
# consumed programmatically.
NEON_MAIN_LANDING_VALIDATION_400M = {
    "Yu Lin": 1625, "Stadium": 1242, "Neox Factory": 936, "Dan Ching": 905,
    "Hung Shan": 750, "Jao Tin": 629, "Test Track": 577, "La Hua Xing": 483,
    "Mey Ran": 475, "Fong Tun": 279, "Jadena City": 217, "Mu Ho Pan": 216,
    "Bianbun": 198, "Rin Jiang": 190, "Ein Long Garden": 172,
    "Nan Chuan": 154, "Rai An": 132, "Bei Li": 107, "Kun Xiu": 104,
    "Tu Ling": 92, "Yun Su": 90, "Long Ho": 68, "Mai Hu": 31,
    "Hernay Town": 10,
}


def rondo_poi_world_coordinates():
    """Convert the pixel estimates above to real telemetry-space (cm)
    coordinates - same approach as erangel_poi_world_coordinates()."""
    scale = MAP_SIZE_CM["Neon_Main"] / RONDO_IMAGE_SIZE_PX
    return {name: (px * scale, py * scale) for name, (px, py) in RONDO_POI_PIXELS.items()}


# Map telemetry mapName -> that map's landing-validation dict, so consumers
# that need to reason about "which POIs are actually popular on whichever
# map this came from" (e.g. squad_drop_zone.py's "change it up" pick) don't
# have to hardcode a single map's data. Keys match drop_zone.py's
# MAP_POI_LOOKUP exactly - every map with POI data has both.
MAP_LANDING_VALIDATION_400M = {
    "Baltic_Main": ERANGEL_LANDING_VALIDATION_400M,
    "Tiger_Main": TAEGO_LANDING_VALIDATION_400M,
    "Desert_Main": DESERT_MAIN_LANDING_VALIDATION_400M,
    "DihorOtok_Main": DIHOROTOK_MAIN_LANDING_VALIDATION_400M,
    "Savage_Main": SAVAGE_MAIN_LANDING_VALIDATION_400M,
    "Neon_Main": NEON_MAIN_LANDING_VALIDATION_400M,
}
