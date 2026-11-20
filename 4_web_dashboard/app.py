"""Airbnb Europe Analytics - European Short-Stay Market Intelligence (Streamlit + Plotly on PostgreSQL)."""
import streamlit as st

st.set_page_config(page_title="Airbnb Europe Analytics", page_icon="🏙️", layout="wide", initial_sidebar_state="expanded")

from components import filters, ui  # noqa: E402

st.markdown(ui.CSS, unsafe_allow_html=True)
PAGES = [
    st.Page("pages/1_Executive_Overview.py", title="Executive Overview", icon="📊", default=True),
    st.Page("pages/2_City_Intelligence.py", title="City Intelligence", icon="🏙️"),
    st.Page("pages/3_Pricing_Analytics.py", title="Pricing Analytics", icon="💶"),
    st.Page("pages/4_Property_Room_Insights.py", title="Property & Room Insights", icon="🛏️"),
    st.Page("pages/5_Ratings_Location.py", title="Ratings & Location", icon="⭐"),
    st.Page("pages/6_Geospatial_View.py", title="Geospatial View", icon="🗺️"),
    st.Page("pages/7_Data_Quality_Pipeline.py", title="Data Quality & Pipeline", icon="🛡️"),
    st.Page("pages/8_SQL_Explorer.py", title="SQL Analytics Explorer", icon="🧮"),
]
nav = st.navigation(PAGES)
try:
    filters.sidebar()
except Exception as exc:  # database down -> clear message instead of a stack trace
    st.error("Cannot reach the SQL data warehouse. Start PostgreSQL and run the pipeline (see HOW_TO_RUN.md).")
    st.caption(f"{type(exc).__name__}")
    st.stop()
nav.run()
