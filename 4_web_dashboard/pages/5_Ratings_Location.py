import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from components import data, ui
from queries.catalog import CORR_COLUMNS

ui.header("Ratings & Location", "Guest satisfaction, cleanliness and location indices versus price")
f = ui.filtered_or_stop()
ui.n_or_stop(f)
ui.note("<b>Correlation is not causation.</b> These are observational associations between listing attributes; no causal effect of ratings or location on price can be inferred.")

c1, c2 = st.columns(2)
with c1:
    s = data.run("""SELECT width_bucket(guest_satisfaction_overall, 20, 100, 40) b, count(*) n FROM gold.vw_offers_enriched
        WHERE {WHERE} AND guest_satisfaction_overall >= 20 AND guest_satisfaction_overall < 100 GROUP BY 1 ORDER BY 1""", f)
    s["score"] = 20 + (s.b - 1) * 2
    full = data.run("SELECT count(*) n FROM gold.vw_offers_enriched WHERE {WHERE} AND guest_satisfaction_overall = 100", f)["n"][0]
    s = pd.concat([s, pd.DataFrame([{"b": 41, "n": full, "score": 100}])], ignore_index=True)
    ui.plot(px.bar(s, x="score", y="n", title="Guest satisfaction distribution (bin start; 100 shown separately)", labels={"score": "Overall satisfaction", "n": "Offers"}), "rl_sat")
with c2:
    cl = data.run("SELECT cleanliness_rating r, count(*) n FROM gold.vw_offers_enriched WHERE {WHERE} GROUP BY 1 ORDER BY 1", f)
    ui.plot(px.bar(cl, x="r", y="n", title="Cleanliness rating distribution", labels={"r": "Cleanliness (0-10)", "n": "Offers"}), "rl_clean")

# SQL-computed Pearson correlation matrix (cols come from a fixed whitelist)
keys = list(CORR_COLUMNS)
exprs = ", ".join(f"corr({a}, {b}) AS c_{i}_{j}" for i, a in enumerate(keys) for j, b in enumerate(keys) if j >= i)
res = data.run(f"SELECT {exprs} FROM gold.vw_offers_enriched WHERE {{WHERE}}", f).iloc[0]
mat = [[None] * len(keys) for _ in keys]
for i in range(len(keys)):
    for j in range(i, len(keys)):
        v = res[f"c_{i}_{j}"]
        mat[i][j] = mat[j][i] = None if v != v else float(v)
labels = list(CORR_COLUMNS.values())
fig = go.Figure(go.Heatmap(z=mat, x=labels, y=labels, zmin=-1, zmax=1, colorscale="RdBu", reversescale=True,
                           text=[[f"{v:.2f}" if v is not None else "" for v in r] for r in mat], texttemplate="%{text}"))
fig.update_layout(title="Pearson correlation matrix (computed in SQL with corr())")
ui.plot(fig, "rl_corr", 520)

c3, c4 = st.columns(2)
smp = data.run("""SELECT city, room_type, two_night_total_eur eur, guest_satisfaction_overall sat, dist_city_center_km dist_center,
    dist_metro_km dist_metro, attr_index_norm attr, rest_index_norm rest FROM gold.vw_offers_enriched WHERE {WHERE}
    ORDER BY md5(offer_id) LIMIT 5000""", f)
with c3:
    ui.plot(px.scatter(smp, x="sat", y="eur", color="room_type", opacity=.45, log_y=True, title="Price vs satisfaction (5,000-offer sample)",
                       labels={"sat": "Satisfaction", "eur": "EUR (log)"}), "rl_s1")
with c4:
    ui.plot(px.scatter(smp, x="dist_center", y="eur", color="city", opacity=.45, log_y=True, title="Price vs distance to centre (sample)",
                       labels={"dist_center": "km to city centre", "eur": "EUR (log)"}), "rl_s2")
c5, c6 = st.columns(2)
with c5:
    ui.plot(px.scatter(smp, x="attr", y="eur", opacity=.4, log_y=True, trendline=None, title="Price vs attraction index (sample)",
                       labels={"attr": "Attraction index (0-100)", "eur": "EUR (log)"}), "rl_s3")
with c6:
    ui.plot(px.scatter(smp, x="rest", y="eur", opacity=.4, log_y=True, title="Price vs restaurant index (sample)",
                       labels={"rest": "Restaurant index (0-100)", "eur": "EUR (log)"}), "rl_s4")
band = data.run("""SELECT CASE WHEN dist_metro_km < 0.25 THEN '<250 m' WHEN dist_metro_km < 0.5 THEN '250-500 m' WHEN dist_metro_km < 1 THEN '0.5-1 km'
    ELSE '1 km+' END metro_band, min(dist_metro_km) o, count(*) offers, avg(two_night_total_eur) avg_eur, avg(guest_satisfaction_overall) sat
    FROM gold.vw_offers_enriched WHERE {WHERE} GROUP BY 1 ORDER BY 2""", f)
st.subheader("Price and satisfaction by metro distance")
st.dataframe(band.drop(columns="o"), width="stretch", hide_index=True, column_config={"avg_eur": st.column_config.NumberColumn("Avg EUR", format="€%.0f"), "sat": st.column_config.NumberColumn("Avg satisfaction", format="%.1f")})
ui.download(band.drop(columns="o"), "metro_distance_bands")
