from pathlib import Path

import plotly.express as px
import streamlit as st
from sqlalchemy import text

from components import data, ui
from queries.catalog import GROUPINGS, METRICS, build_explorer_sql

ui.header("SQL Analytics Explorer", "Safe, parameterised analytics: pick a metric and grouping — no free-form SQL is accepted")
f = ui.filtered_or_stop()
ui.n_or_stop(f)
tab1, tab2 = st.tabs(["Metric builder", "Predefined analytical queries"])
with tab1:
    c1, c2, c3 = st.columns(3)
    metric = c1.selectbox("Metric", list(METRICS))
    g1 = c2.selectbox("Group by", list(GROUPINGS), index=0)
    g2 = c3.selectbox("Then by (optional)", ["(none)"] + list(GROUPINGS))
    sql = build_explorer_sql(metric, g1, g2)
    df = data.run(sql, f)
    st.dataframe(df, width="stretch", hide_index=True)
    st.download_button("Download aggregated result (CSV)", df.to_csv(index=False).encode(), "explorer_result.csv", "text/csv", key="dl_explorer")
    if len(df):
        x = df.columns[0]
        if g2 != "(none)" and g2 != g1:
            fig = px.bar(df, x=x, y="metric_value", color=df.columns[1], barmode="group", title=metric)
        else:
            fig = px.bar(df, x=x, y="metric_value", title=metric)
        ui.plot(fig, "ex_chart", 340)
    with st.expander("Generated SQL (filters are bound parameters)"):
        where, params = f.where()
        st.code(sql.replace("{WHERE}", where), language="sql")
        st.json(params)
with tab2:
    qdir = Path(__file__).resolve().parents[2] / "3_gold_layer" / "analytics_queries"
    files = {p.stem: p for p in sorted(qdir.glob("*.sql"))}   # fixed allow-list built from the repository folder
    pick = st.selectbox("Query", list(files))
    body = files[pick].read_text()
    st.code(body, language="sql")
    out = data.query(body)
    st.dataframe(out, width="stretch", hide_index=True)
    st.download_button("Download CSV", out.to_csv(index=False).encode(), f"{pick}.csv", "text/csv", key="dl_predef")
    st.caption("Predefined queries run over the whole warehouse (global filters do not apply).")
