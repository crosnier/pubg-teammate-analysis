# ==============================
# utils/weapon_classes.py
# ==============================
# Static reference: telemetry damageCauserName -> firearm class.
# Scoped to guns only (PUBG's own weapon categories) - melee, throwables,
# vehicles, and environmental causers return None, since Weapon Signature
# is about gun preference, not "what killed you."
WEAPON_CLASS = {
    # Assault Rifles
    "WeapAK47_C": "AR",
    "WeapHK416_C": "AR",
    "WeapSCAR-L_C": "AR",
    "WeapM16A4_C": "AR",
    "WeapGroza_C": "AR",
    "WeapAUG_C": "AR",
    "WeapBerylM762_C": "AR",
    "WeapQBZ95_C": "AR",
    "WeapG36C_C": "AR",
    "WeapFamasG2_C": "AR",
    "WeapMk47Mutant_C": "AR",
    "WeapACE32_C": "AR",

    # Designated Marksman Rifles
    "WeapSKS_C": "DMR",
    "WeapMini14_C": "DMR",
    "WeapMk12_C": "DMR",
    "WeapVSS_C": "DMR",
    "WeapQBU88_C": "DMR",
    "WeapMk14_C": "DMR",
    "WeapFNFal_C": "DMR",
    "WeapDragunov_C": "DMR",

    # Sniper Rifles (bolt/lever-action)
    "WeapKar98k_C": "Sniper Rifle",
    "WeapM24_C": "Sniper Rifle",
    "WeapAWM_C": "Sniper Rifle",
    "WeapWin94_C": "Sniper Rifle",
    "WeapMosinNagant_C": "Sniper Rifle",

    # SMGs
    "WeapUMP_C": "SMG",
    "WeapVector_C": "SMG",
    "WeapUZI_C": "SMG",
    "WeapThompson_C": "SMG",
    "WeapBizonPP19_C": "SMG",
    "WeapJS9_C": "SMG",
    "WeapP90_C": "SMG",
    "Weapvz61Skorpion_C": "SMG",
    "WeapMP5K_C": "SMG",

    # LMGs
    "WeapM249_C": "LMG",
    "WeapDP28_C": "LMG",
    "WeapMG3_C": "LMG",
    "WeapL6_C": "LMG",

    # Shotguns
    "WeapSaiga12_C": "Shotgun",
    "WeapBerreta686_C": "Shotgun",
    "WeapWinchester_C": "Shotgun",
    "WeapSawnoff_C": "Shotgun",
    "WeapDP12_C": "Shotgun",

    # Pistols
    "WeapM9_C": "Pistol",
    "WeapM1911_C": "Pistol",
    "WeapDesertEagle_C": "Pistol",
    "WeapNagantM1895_C": "Pistol",
    "WeapSkorpion_C": "Pistol",

    # Crossbow
    "WeapCrossbow_1_C": "Crossbow",
}


def classify_weapon(damage_causer_name):
    """Return the firearm class for a telemetry damageCauserName, or None.

    None covers anything that isn't a gun-preference signal: melee,
    throwables/explosives, vehicles, environmental causers, and any
    weapon not yet in WEAPON_CLASS.
    """
    return WEAPON_CLASS.get(damage_causer_name)
