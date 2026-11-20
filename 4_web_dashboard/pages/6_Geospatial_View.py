import plotly.express as px
import streamlit as st

from components import data, ui

ui.header("Geospatial View", "Offer locations from the source coordinates (lat/lng), sampled for performance")
f = ui.filtered_or_stop()
total = ui.n_or_stop(f)
ui.note("Coordinates come from the source dataset (public Airbnb listing coordinates, which Airbnb perturbs); they are not exact addresses and no location was invented.")
c1, c2 = st.columns([1, 1])
n = c1.slider("Points to render (deterministic sample)", 500, 8000, 3000, step=500)
color_by = c2.selectbox("Colour by", ["Two-night total (EUR)", "Room type", "Guest satisfaction", "City"])
cap = float(data.run("SELECT percentile_cont(0.95) WITHIN GROUP (ORDER BY two_night_total_eur) p FROM gold.vw_offers_enriched WHERE {WHERE}", f)["p"][0])
pts = data.run("""SELECT city, room_type, lat, lng, two_night_total_eur eur, guest_satisfaction_overall sat, person_capacity cap
    FROM gold.vw_offers_enriched WHERE {WHERE} ORDER BY md5(offer_id) LIMIT :n""", f, {"n": int(n)})
st.caption(f"Showing {len(pts):,} of {total:,} matching offers. Price colour scale is capped at the 95th percentile ({cap:,.0f} EUR).")
kw = dict(lat="lat", lon="lng", hover_name="city", hover_data={"eur": ":.0f", "room_type": True, "sat": True, "lat": False, "lng": False}, zoom=3.2, opacity=.7)
if color_by.startswith("Two-night"):
    kw.update(color="eur", range_color=[0, cap], color_continuous_scale="Turbo")
elif color_by == "Room type":
    kw.update(color="room_type")
elif color_by == "City":
    kw.update(color="city")
else:
    kw.update(color="sat", color_continuous_scale="Viridis", range_color=[70, 100])
import math
lat_span = max(pts.lat.max() - pts.lat.min(), 0.02)
lng_span = max(pts.lng.max() - pts.lng.min(), 0.02)
kw["center"] = {"lat": float((pts.lat.max() + pts.lat.min()) / 2), "lon": float((pts.lng.max() + pts.lng.min()) / 2)}
kw["zoom"] = max(1.0, min(12.0, math.log2(360 / max(lng_span * 1.3, lat_span * 2.0 * 1.3)) - 0.3))
fig = px.scatter_map(pts, map_style="carto-darkmatter", **kw)
fig.update_traces(marker=dict(size=6))
fig.update_layout(margin=dict(l=0, r=0, t=0, b=0))
ui.plot(fig, "geo_map", 620)
st.subheader("Geographic extent by city")
ext = data.run("""SELECT city, count(*) offers, min(lat) lat_min, max(lat) lat_max, min(lng) lng_min, max(lng) lng_max
    FROM gold.vw_offers_enriched WHERE {WHERE} GROUP BY 1 ORDER BY 1""", f)
st.dataframe(ext, width="stretch", hide_index=True)
ui.download(ext, "geographic_extent")
