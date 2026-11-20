from __future__ import annotations

import streamlit as st

from . import data


def sidebar() -> data.Filters:
    """Global filters. They drive every page's SQL via Filters.where()."""
    opt = data.dimension_options()
    st.sidebar.markdown("### Global filters")
    cities = st.sidebar.multiselect("City", opt["cities"], default=opt["cities"], format_func=str.title, key="f_city")
    days = st.sidebar.multiselect("Day type", opt["days"], default=opt["days"], key="f_day")
    rooms = st.sidebar.multiselect("Room type", opt["rooms"], default=opt["rooms"], key="f_room")
    sh = st.sidebar.multiselect("Superhost status", ["Superhost", "Not superhost"], default=["Superhost", "Not superhost"], key="f_sh")
    lo, hi = opt["price"]
    price = st.sidebar.slider("Two-night total (EUR)", lo, hi, (lo, hi), step=5.0, key="f_price",
                              help="realSum: price for 2 guests, 2 nights, incl. fees")
    cap = st.sidebar.slider("Person capacity", opt["cap"][0], opt["cap"][1], opt["cap"], key="f_cap")
    f = data.Filters(cities=cities, day_types=days, room_types=rooms,
                     superhost=[s == "Superhost" for s in sh], price_min=price[0], price_max=price[1],
                     cap_min=cap[0], cap_max=cap[1])
    st.session_state["filters"] = f
    st.sidebar.caption("Source: Zenodo 10.5281/zenodo.4446043 (CC BY 4.0). Prices are two-night totals, not nightly rates.")
    return f
