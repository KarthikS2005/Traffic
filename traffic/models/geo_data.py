"""
geo_data.py
-----------
Approximate lat/lng coordinates for the Bengaluru areas and hotspots
that appear in "Traffic 3.csv". These are static, hand-maintained
reference points (city-locality centroids) used only to place markers
and draw route lines on the dashboard map — they are not survey-grade
coordinates.
"""

AREA_COORDS = {
    "Koramangala": (12.9352, 77.6245),
    "Whitefield": (12.9698, 77.7500),
    "Indiranagar": (12.9784, 77.6408),
    "Electronic City": (12.8452, 77.6602),
    "Hebbal": (13.0355, 77.5970),
    "MG Road": (12.9758, 77.6045),
    "HSR Layout": (12.9116, 77.6389),
    "Manyata Tech Park": (13.0475, 77.6205),
    "Jayanagar": (12.9308, 77.5838),
    "ITPL": (12.9855, 77.7278),
    "BTM Layout": (12.9166, 77.6101),
    "Banashankari": (12.9250, 77.5540),
    "Kengeri": (12.9081, 77.4855),
    "Rajajinagar": (12.9915, 77.5551),
    "Yelahanka": (13.1005, 77.5963),
    "Marathahalli": (12.9569, 77.7011),
}

HOTSPOT_COORDS = {
    "Silk Board Junction": (12.9172, 77.6228),
    "Marathahalli Multiplex": (12.9569, 77.7011),
    "HAL Airport Road": (12.9611, 77.6484),
    "Madiwala Market": (12.9200, 77.6170),
    "Mekhri Circle": (13.0069, 77.5811),
    "Cantonment Station": (12.9857, 77.5990),
    "Tin Factory": (13.0027, 77.6631),
    "Kasturi Nagar": (13.0100, 77.6600),
    "Hebbal Flyover": (13.0358, 77.5975),
    "Domlur Flyover": (12.9611, 77.6387),
    "Goraguntepalya": (13.0280, 77.5540),
    "Nayandahalli": (12.9420, 77.5340),
    "NICE Junction": (12.9070, 77.5100),
    "Kanankapura Signal": (12.9010, 77.5700),
    "Town Hall": (12.9581, 77.5852),
}

CITY_CENTER = (12.9716, 77.5946)  # Bengaluru


def get_area_coords(name):
    return AREA_COORDS.get(name)


def get_hotspot_coords(name):
    return HOTSPOT_COORDS.get(name)


def get_coords(name):
    """Look up coordinates for any known area OR hotspot name."""
    return AREA_COORDS.get(name) or HOTSPOT_COORDS.get(name)


def all_areas_geojson():
    return [
        {"name": name, "lat": lat, "lng": lng, "type": "area"}
        for name, (lat, lng) in AREA_COORDS.items()
    ]


def all_hotspots_geojson():
    return [
        {"name": name, "lat": lat, "lng": lng, "type": "hotspot"}
        for name, (lat, lng) in HOTSPOT_COORDS.items()
    ]
