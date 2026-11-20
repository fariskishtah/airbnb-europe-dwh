import plotly.express as px
import streamlit as st

from components import data, ui

ui.header("Pricing Analytics", "Distribution, drivers and outliers of the two-night total price (EUR, 2 guests)")
f = ui.filtered_or_stop()
n = ui.n_or_stop(f)
logy = st.toggle("Logarithmic price axis (recommended: prices are right-skewed)", value=True)
ax = "log" if logy else "linear"

rows = data.run("""SELECT city, day_type, room_type, is_superhost, person_capacity, bedrooms, price_outlier_iqr,
    two_night_total_eur eur FROM gold.vw_offers_enriched WHERE {WHERE}""", f)
rows["superhost"] = rows.is_superhost.map({True: "Superhost", False: "Not superhost"})

c1, c2 = st.columns(2)
with c1:
    cap = rows.eur.quantile(.99)
    ui.plot(px.histogram(rows[rows.eur <= cap], x="eur", nbins=50, title=f"Price histogram (≤ 99th percentile {cap:,.0f} EUR)",
                         labels={"eur": "Two-night total (EUR)"}), "pr_hist")
with c2:
    ui.plot(px.box(rows, x="room_type", y="eur", color="room_type", points=False, title="Price by room type", log_y=logy,
                   labels={"eur": "EUR", "room_type": ""}), "pr_room")
order = rows.groupby("city").eur.median().sort_values().index.tolist()
ui.plot(px.box(rows, x="city", y="eur", points=False, category_orders={"city": order}, log_y=logy,
               title="Price by city (ordered by median)", labels={"eur": "EUR", "city": ""}), "pr_city", 420)

c3, c4 = st.columns(2)
with c3:
    wk = data.run("""SELECT city, day_type, avg(two_night_total_eur) avg_eur FROM gold.vw_offers_enriched WHERE {WHERE} GROUP BY 1,2""", f)
    ui.plot(px.bar(wk, x="city", y="avg_eur", color="day_type", barmode="group", title="Weekday vs weekend average (EUR)",
                   labels={"avg_eur": "EUR", "city": ""}), "pr_wk")
with c4:
    ui.plot(px.box(rows, x="superhost", y="eur", color="superhost", points=False, log_y=logy, title="Superhost vs other hosts",
                   labels={"eur": "EUR", "superhost": ""}), "pr_sh")
    st.caption("Association only — superhosts differ in room type, city and location mix.")
c5, c6 = st.columns(2)
with c5:
    cp = rows.groupby("person_capacity").eur.agg(["mean", "median", "size"]).reset_index()
    ui.plot(px.bar(cp.melt("person_capacity", ["mean", "median"], var_name="stat", value_name="eur"), x="person_capacity", y="eur",
                   color="stat", barmode="group", title="Price by guest capacity", labels={"eur": "EUR", "person_capacity": "Capacity (guests)"}), "pr_cap")
with c6:
    sc = rows.sample(min(4000, len(rows)), random_state=7)
    ui.plot(px.scatter(sc, x="bedrooms", y="eur", color="room_type", opacity=.5, log_y=logy, title="Price vs bedrooms (4,000-offer sample)",
                       labels={"eur": "EUR"}), "pr_bed")
st.subheader("Outliers")
out = rows.groupby("city").agg(offers=("eur", "size"), outliers=("price_outlier_iqr", "sum"), max_eur=("eur", "max")).reset_index()
out["outlier_pct"] = 100 * out.outliers / out.offers
st.dataframe(out.sort_values("outlier_pct", ascending=False), width="stretch", hide_index=True,
             column_config={"max_eur": st.column_config.NumberColumn("Max (EUR)", format="€%.0f"), "outlier_pct": st.column_config.NumberColumn("Outlier %", format="%.2f")})
ui.note("Outlier = above the upper Tukey fence (Q3 + 1.5·IQR) within its city/day-type sample; flagged, never removed.")
ui.download(out, "pricing_outliers")
