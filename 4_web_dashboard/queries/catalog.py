"""Whitelisted building blocks for the SQL Analytics Explorer. User input only ever selects a KEY from these
dictionaries; SQL identifiers are never taken from the user, and all filter values are bound parameters."""

METRICS = {
    "Observations (count)": "count(*)",
    "Average two-night total (EUR)": "avg(two_night_total_eur)",
    "Median two-night total (EUR)": "percentile_cont(0.5) WITHIN GROUP (ORDER BY two_night_total_eur)",
    "Average nightly equivalent (EUR, total/2)": "avg(nightly_equivalent_eur)",
    "Average guest satisfaction (0-100)": "avg(guest_satisfaction_overall)",
    "Average cleanliness (0-10)": "avg(cleanliness_rating)",
    "Average distance to city centre (km)": "avg(dist_city_center_km)",
    "Average distance to metro (km)": "avg(dist_metro_km)",
    "Average person capacity": "avg(person_capacity)",
    "Price outlier share (%)": "100.0 * avg(price_outlier_iqr::int)",
}
GROUPINGS = {
    "City": "city",
    "Day type": "day_type",
    "Room type": "room_type",
    "Superhost": "is_superhost",
    "Person capacity": "person_capacity",
    "Bedrooms": "bedrooms",
    "Host status": "host_status_label",
    "Country": "country",
}
CORR_COLUMNS = {
    "two_night_total_eur": "Price (2 nights)", "guest_satisfaction_overall": "Satisfaction", "cleanliness_rating": "Cleanliness",
    "dist_city_center_km": "Dist. centre", "dist_metro_km": "Dist. metro", "attr_index_norm": "Attraction idx",
    "rest_index_norm": "Restaurant idx", "person_capacity": "Capacity", "bedrooms": "Bedrooms",
}


def build_explorer_sql(metric: str, group1: str, group2: str | None) -> str:
    """Return SQL containing the {WHERE} token. Raises KeyError for anything outside the whitelists."""
    m = METRICS[metric]
    g1 = GROUPINGS[group1]
    cols = [g1] + ([GROUPINGS[group2]] if group2 and group2 != group1 and group2 != "(none)" else [])
    sel = ", ".join(cols)
    return (f"SELECT {sel}, {m} AS metric_value, count(*) AS observations FROM gold.vw_offers_enriched "
            f"WHERE {{WHERE}} GROUP BY {sel} ORDER BY {sel}")
