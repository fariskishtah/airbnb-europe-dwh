"""Small manually curated reference data (public knowledge, NOT from the Airbnb source).

Used only for (a) the country attribute of DimCity and (b) a coarse coordinate sanity bounding circle.
"""
CITY_REFERENCE = {
    # city: (display name, country, approx. centre lat, approx. centre lng)
    "amsterdam": ("Amsterdam", "Netherlands", 52.3676, 4.9041),
    "athens": ("Athens", "Greece", 37.9838, 23.7275),
    "barcelona": ("Barcelona", "Spain", 41.3851, 2.1734),
    "berlin": ("Berlin", "Germany", 52.5200, 13.4050),
    "budapest": ("Budapest", "Hungary", 47.4979, 19.0402),
    "lisbon": ("Lisbon", "Portugal", 38.7223, -9.1393),
    "london": ("London", "United Kingdom", 51.5074, -0.1278),
    "paris": ("Paris", "France", 48.8566, 2.3522),
    "rome": ("Rome", "Italy", 41.9028, 12.4964),
    "vienna": ("Vienna", "Austria", 48.2082, 16.3738),
}
MAX_COORD_OFFSET_DEG = 0.6  # a listing farther than this from the reference centre is flagged invalid
