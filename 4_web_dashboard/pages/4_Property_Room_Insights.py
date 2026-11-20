import plotly.express as px
import streamlit as st

from components import data, ui

ui.header("Property & Room Insights", "Room characteristics, capacity and host indicators available in the source data")
f = ui.filtered_or_stop()
ui.n_or_stop(f)
ui.note("The source has <b>no property-type, listing-id or host-id fields</b>. Only room type, capacity, bedrooms and host-status flags "
        "exist, so this page does not (and cannot) analyse apartments vs houses or individual hosts.")
c1, c2 = st.columns(2)
with c1:
    r = data.run("""SELECT room_type, count(*) offers, avg(two_night_total_eur) avg_eur,
        percentile_cont(0.5) WITHIN GROUP (ORDER BY two_night_total_eur) median_eur FROM gold.vw_offers_enriched WHERE {WHERE} GROUP BY 1""", f)
    ui.plot(px.bar(r, x="room_type", y="offers", color="room_type", title="Offers by room type", labels={"room_type": ""}), "pi_room")
with c2:
    ui.plot(px.bar(r.melt("room_type", ["avg_eur", "median_eur"], var_name="stat", value_name="eur"), x="room_type", y="eur", color="stat",
                   barmode="group", title="Price by room type (EUR)", labels={"room_type": "", "eur": "EUR"}), "pi_roomp")
c3, c4 = st.columns(2)
with c3:
    b = data.run("""SELECT least(bedrooms,4) bedrooms_cap, count(*) offers, avg(two_night_total_eur) avg_eur
        FROM gold.vw_offers_enriched WHERE {WHERE} GROUP BY 1 ORDER BY 1""", f)
    b["bedrooms"] = b.bedrooms_cap.map(lambda x: "Studio (0)" if x == 0 else ("4+" if x == 4 else str(x)))
    ui.plot(px.bar(b, x="bedrooms", y="avg_eur", text=b.offers, title="Average price by bedrooms (label = offers; 0 = studio)",
                   labels={"avg_eur": "EUR", "bedrooms": "Bedrooms"}), "pi_bed")
with c4:
    cp = data.run("SELECT person_capacity, room_type, count(*) offers FROM gold.vw_offers_enriched WHERE {WHERE} GROUP BY 1,2", f)
    ui.plot(px.bar(cp, x="person_capacity", y="offers", color="room_type", title="Guest capacity by room type", labels={"person_capacity": "Max guests"}), "pi_cap")
c5, c6 = st.columns(2)
with c5:
    h = data.run("""SELECT host_status_label, count(*) offers, avg(two_night_total_eur) avg_eur, avg(guest_satisfaction_overall) sat
        FROM gold.vw_offers_enriched WHERE {WHERE} GROUP BY 1 ORDER BY 2 DESC""", f)
    ui.plot(px.bar(h, x="offers", y="host_status_label", orientation="h", title="Host-status indicator mix", labels={"host_status_label": ""}), "pi_host")
with c6:
    sh = data.run("""SELECT CASE WHEN is_superhost THEN 'Superhost' ELSE 'Not superhost' END status, room_type, count(*) offers
        FROM gold.vw_offers_enriched WHERE {WHERE} GROUP BY 1,2""", f)
    sh["share_pct"] = 100 * sh.offers / sh.groupby("status").offers.transform("sum")
    ui.plot(px.bar(sh, x="status", y="share_pct", color="room_type", title="Room-type mix: superhost vs other (%)", labels={"share_pct": "%", "status": ""}), "pi_sh")
ui.note("<b>multi</b> = host with 2–4 offers, <b>biz</b> = host with more than 4 offers (Zenodo column definitions); these are portfolio-size flags, not host identities.")
st.dataframe(h, width="stretch", hide_index=True, column_config={"avg_eur": st.column_config.NumberColumn("Avg EUR", format="€%.0f"), "sat": st.column_config.NumberColumn("Avg satisfaction", format="%.1f")})
ui.download(h, "host_status_summary")
