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

Still needed before this is classification-ready:
- Kameshki and Stalber's pixel estimates look low-confidence relative to
  their validation density (520 and 1031 landings respectively - lower
  than their apparent visual prominence as named cities suggests) -
  re-examine placement before trusting them for classification.
- Every other map (Miramar/Desert_Main, Sanhok/Savage_Main,
  Vikendi/DihorOtok_Main, Taego/Tiger_Main, Rondo/Neon_Main, etc.) -
  Erangel was done first because it dominates the cached telemetry pool
  (177 of a 300-match sample). Same research process needs repeating per
  map before this tool can profile drops on non-Erangel matches -
  see the "map not yet supported" fallback requirement in issue #44 for
  what should happen for matches on a map not yet in this file.
"""

# Map coordinate ranges in centimeters (0 to this value on both x and y),
# per https://documentation.pubg.com/en - confirmed official, not guessed.
# Rondo's isn't independently confirmed yet despite it appearing in our
# cached telemetry (Neon_Main) - needs its own verification pass.
MAP_SIZE_CM = {
    "Baltic_Main": 816000,      # Erangel
    "Desert_Main": 816000,      # Miramar
    "DihorOtok_Main": 816000,   # Vikendi
    "Tiger_Main": 816000,       # Taego
    "Kiki_Main": 816000,        # Deston
    "Savage_Main": 408000,      # Sanhok
    "Chimera_Main": 306000,     # Paramo
    "Summerland_Main": 204000,  # Karakin
    "Range_Main": 204000,       # Camp Jackal
    "Heaven_Main": 102000,      # Haven
    # "Neon_Main": None,        # Rondo - NOT YET VERIFIED, do not add a
    #                             guessed number here.
}

# Official reference map image (source: github.com/pubg/api-assets,
# Erangel_Main_Low_Res.png), used to derive the pixel->world coordinates
# below. 819x819px covering the full 0-816000cm range on both axes.
ERANGEL_IMAGE_PATH = "docs/design/maps/erangel_official.png"
ERANGEL_IMAGE_SIZE_PX = 819

# POI name -> (pixel_x, pixel_y) read directly off ERANGEL_IMAGE_PATH,
# top-left origin. NEEDS_REVIEW flags entries whose validation density
# (see erangel_landing_validation.py in the same research pass) looked
# lower than expected for a named city - re-examine before trusting.
ERANGEL_POI_PIXELS = {
    "Zharki": (75, 100),
    "Severny": (350, 105),
    "Kameshki": (655, 90),           # NEEDS_REVIEW - low validation density (520)
    "Stalber": (570, 115),           # NEEDS_REVIEW - low validation density (1031)
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
