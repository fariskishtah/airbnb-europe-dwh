import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from components import data, ui

ui.header("City Intelligence", "Compare the ten European cities on price, ratings, capacity and location")
f = ui.filtered_or_stop()
ui.n_or_stop(f)

m = data.run("""SELECT city, country, count(*) observations, avg(two_night_total_eur) avg_eur,
    percentile_cont(0.5) WITHIN GROUP (ORDER BY two_night_total_eur) median_eur, avg(guest_satisfaction_overall) satisfaction,
    avg(cleanliness_rating) cleanliness, avg(person_capacity) capacity, avg(bedrooms) bedrooms,
    avg(dist_city_center_km) dist_center_km, avg(dist_metro_km) dist_metro_km
    FROM gold.vw_offers_enriched WHERE {WHERE} GROUP BY city, country""", f).sort_values("avg_eur", ascending=False)
m.insert(0, "rank_by_avg_price", range(1, len(m) + 1))

st.subheader("City ranking")
st.dataframe(m, width="stretch", hide_index=True, column_config={
    "avg_eur": st.column_config.NumberColumn("Avg two-night (EUR)", format="€%.0f"),
    "median_eur": st.column_config.NumberColumn("Median two-night (EUR)", format="€%.0f"),
    "satisfaction": st.column_config.NumberColumn("Satisfaction (0-100)", format="%.1f"),
    "cleanliness": st.column_config.NumberColumn("Cleanliness (0-10)", format="%.2f"),
    "capacity": st.column_config.NumberColumn("Avg guests capacity", format="%.2f"),
    "bedrooms": st.column_config.NumberColumn("Avg bedrooms", format="%.2f"),
    "dist_center_km": st.column_config.NumberColumn("Dist. centre (km)", format="%.2f"),
    "dist_metro_km": st.column_config.NumberColumn("Dist. metro (km)", format="%.2f")})
ui.download(m, "city_ranking")

c1, c2 = st.columns(2)
with c1:
    d = m.melt("city", ["avg_eur", "median_eur"], var_name="statistic", value_name="eur")
    ui.plot(px.bar(d, x="city", y="eur", color="statistic", barmode="group", title="Average vs median two-night total (EUR)",
                   labels={"eur": "EUR", "city": ""}), "ci_price")
with c2:
    ui.plot(px.scatter(m, x="satisfaction", y="avg_eur", size="observations", text="city", title="Satisfaction vs average price (bubble = observations)",
                       labels={"satisfaction": "Avg guest satisfaction (0-100)", "avg_eur": "Avg two-night (EUR)"}), "ci_scatter")
c3, c4 = st.columns(2)
with c3:
    mix = data.run("SELECT city, room_type, count(*) n FROM gold.vw_offers_enriched WHERE {WHERE} GROUP BY 1,2", f)
    mix["share_pct"] = 100 * mix.n / mix.groupby("city").n.transform("sum")
    ui.plot(px.bar(mix, x="city", y="share_pct", color="room_type", title="Room-type mix by city (%)",
                   labels={"share_pct": "% of offers", "city": ""}), "ci_mix")
with c4:
    d = m.melt("city", ["dist_center_km", "dist_metro_km"], var_name="metric", value_name="km")
    ui.plot(px.bar(d, x="city", y="km", color="metric", barmode="group", title="Average distance to centre / nearest metro (km)",
                   labels={"km": "km", "city": ""}), "ci_dist")

st.subheader("City deep dive")
sel = st.selectbox("Select a city", m.city.tolist(), format_func=str.title)
r = m[m.city == sel].iloc[0]
ui.kpis([("Rank by avg price", f"#{int(r.rank_by_avg_price)}", f"of {len(m)} selected"), ("Avg two-night", ui.eur(r.avg_eur), r.country),
         ("Median two-night", ui.eur(r.median_eur), "EUR"), ("Satisfaction", f"{r.satisfaction:.1f}", "/100"),
         ("Avg capacity", f"{r.capacity:.1f}", "guests"), ("Dist. centre", f"{r.dist_center_km:.1f} km", f"metro {r.dist_metro_km:.1f} km")])
box = data.run("SELECT two_night_total_eur eur, day_type FROM gold.vw_offers_enriched WHERE {WHERE} AND city = :c", f, {"c": sel})
ui.plot(px.box(box, x="day_type", y="eur", points=False, title=f"{sel.title()}: two-night total by day type (EUR)", labels={"eur": "EUR", "day_type": ""}), "ci_box", 340)
