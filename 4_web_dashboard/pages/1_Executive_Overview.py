import plotly.express as px
import streamlit as st

from components import data, ui

ui.header("Airbnb Europe Analytics", "European Short-Stay Market Intelligence · Executive Overview")
f = ui.filtered_or_stop()
n = ui.n_or_stop(f)

k = data.run("""SELECT count(*) n, count(DISTINCT city) cities, avg(two_night_total_eur) avg_p,
    percentile_cont(0.5) WITHIN GROUP (ORDER BY two_night_total_eur) med_p, avg(nightly_equivalent_eur) nightly,
    avg(guest_satisfaction_overall) sat, avg(cleanliness_rating) clean FROM gold.vw_offers_enriched WHERE {WHERE}""", f).iloc[0]
ui.kpis([("Offer observations", f"{int(k.n):,}", "rows in fact table"), ("Cities", f"{int(k.cities)}", "of 10 in source"),
         ("Avg two-night total", ui.eur(k.avg_p), "2 guests · 2 nights"), ("Median two-night total", ui.eur(k.med_p), "robust to skew"),
         ("Avg satisfaction", f"{k.sat:.1f}/100", "guest overall"), ("Avg cleanliness", f"{k.clean:.2f}/10", "rating")])
st.write("")
ui.note("Price = <b>two-night total for two guests (EUR)</b>. The 'nightly equivalent' is that total ÷ 2 — a derived figure, "
        f"not an observed nightly rate (avg {ui.eur(k.nightly)}).")

city = data.run("""SELECT city, count(*) observations, avg(two_night_total_eur) avg_eur,
    percentile_cont(0.5) WITHIN GROUP (ORDER BY two_night_total_eur) median_eur
    FROM gold.vw_offers_enriched WHERE {WHERE} GROUP BY city""", f)
c1, c2 = st.columns(2)
with c1:
    d = city.sort_values("avg_eur")
    fig = px.bar(d, x="avg_eur", y="city", orientation="h", title="Average two-night total by city (EUR)",
                 labels={"avg_eur": "EUR", "city": ""}, text=d.avg_eur.round(0))
    ui.plot(fig, "ov_avg")
with c2:
    d = city.sort_values("median_eur")
    fig = px.bar(d, x="median_eur", y="city", orientation="h", title="Median two-night total by city (EUR)",
                 labels={"median_eur": "EUR", "city": ""}, text=d.median_eur.round(0), color_discrete_sequence=[ui.BLUE])
    ui.plot(fig, "ov_med")

c3, c4 = st.columns(2)
with c3:
    room = data.run("SELECT room_type, count(*) observations FROM gold.vw_offers_enriched WHERE {WHERE} GROUP BY 1", f)
    fig = px.pie(room, names="room_type", values="observations", hole=.55, title="Room-type distribution")
    ui.plot(fig, "ov_room")
with c4:
    wk = data.run("""SELECT day_type, avg(two_night_total_eur) average, percentile_cont(0.5) WITHIN GROUP (ORDER BY two_night_total_eur) median
        FROM gold.vw_offers_enriched WHERE {WHERE} GROUP BY 1""", f).melt("day_type", var_name="statistic", value_name="eur")
    fig = px.bar(wk, x="day_type", y="eur", color="statistic", barmode="group", title="Weekday vs weekend two-night total (EUR)",
                 labels={"eur": "EUR", "day_type": ""})
    ui.plot(fig, "ov_wk")
    st.caption("Weekday and weekend are separate offer samples, not the same listings tracked over time.")

cap = float(data.run("SELECT percentile_cont(0.99) WITHIN GROUP (ORDER BY two_night_total_eur) p FROM gold.vw_offers_enriched WHERE {WHERE}", f)["p"][0])
cap = max(cap, 50.0)
hist = data.run("""SELECT width_bucket(two_night_total_eur, 0, :cap, 40) b, count(*) n FROM gold.vw_offers_enriched
    WHERE {WHERE} AND two_night_total_eur < :cap GROUP BY 1 ORDER BY 1""", f, {"cap": cap})
hist["eur_from"] = (hist.b - 1) * cap / 40
above = n - int(hist.n.sum())
fig = px.bar(hist, x="eur_from", y="n", title=f"Price distribution (0–{cap:,.0f} EUR, 99th percentile; {above:,} higher offers not shown)",
             labels={"eur_from": "Two-night total (EUR, bin start)", "n": "Offers"})
fig.update_traces(marker_line_width=0)
ui.plot(fig, "ov_hist")
ui.download(city, "overview_city_metrics")
