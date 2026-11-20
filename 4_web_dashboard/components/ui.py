from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go
import plotly.io as pio
import streamlit as st

from . import data

NAVY, CYAN, BLUE = "#0A1830", "#22D3EE", "#3B82F6"
COLORWAY = ["#22D3EE", "#3B82F6", "#A78BFA", "#F59E0B", "#34D399", "#F472B6", "#94A3B8", "#FB7185", "#60A5FA", "#FACC15"]

pio.templates["airbnb_navy"] = go.layout.Template(layout=dict(
    paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", colorway=COLORWAY,
    font=dict(family="Inter, Segoe UI, sans-serif", color="#EAF2FF", size=13),
    xaxis=dict(gridcolor="rgba(148,163,184,.18)", zerolinecolor="rgba(148,163,184,.25)"),
    yaxis=dict(gridcolor="rgba(148,163,184,.18)", zerolinecolor="rgba(148,163,184,.25)"),
    legend=dict(bgcolor="rgba(0,0,0,0)"), margin=dict(l=10, r=10, t=50, b=10),
    hoverlabel=dict(bgcolor="#11284B", font_color="#EAF2FF")))
pio.templates.default = "airbnb_navy"

CSS = """
<style>
.block-container{padding-top:3.2rem;max-width:1400px}
.hero{background:linear-gradient(120deg,#0E2A57 0%,#0A1830 60%,#0B3A57 100%);border:1px solid rgba(34,211,238,.25);
 border-radius:16px;padding:1.1rem 1.4rem;margin-bottom:1rem}
.hero h1{margin:0;font-size:1.9rem;letter-spacing:-.5px}.hero p{margin:.2rem 0 0;color:#9FB6D8}
.kpi{background:#11284B;border:1px solid rgba(34,211,238,.2);border-radius:14px;padding:.85rem 1rem;height:100%}
.kpi .l{font-size:.72rem;letter-spacing:.08em;text-transform:uppercase;color:#8FA9CE}
.kpi .v{font-size:1.65rem;font-weight:700;color:#fff;line-height:1.2}.kpi .s{font-size:.75rem;color:#22D3EE}
.note{border-left:3px solid #22D3EE;background:rgba(34,211,238,.07);padding:.55rem .8rem;border-radius:6px;color:#C8D9F2;font-size:.88rem}
@media (max-width:640px){.hero h1{font-size:1.35rem}.kpi .v{font-size:1.25rem}}
</style>
"""
PLOT_CONFIG = {"displaylogo": False, "toImageButtonOptions": {"format": "png", "scale": 2}}


def header(title: str, subtitle: str) -> None:
    st.markdown(f'<div class="hero"><h1>{title}</h1><p>{subtitle}</p></div>', unsafe_allow_html=True)


def kpis(items: list[tuple[str, str, str]]) -> None:
    cols = st.columns(len(items))
    for col, (label, value, sub) in zip(cols, items):
        col.markdown(f'<div class="kpi"><div class="l">{label}</div><div class="v">{value}</div><div class="s">{sub}</div></div>',
                     unsafe_allow_html=True)


def note(text: str) -> None:
    st.markdown(f'<div class="note">{text}</div>', unsafe_allow_html=True)


def plot(fig: go.Figure, key: str | None = None, height: int = 380) -> None:
    fig.update_layout(height=height)
    st.plotly_chart(fig, width="stretch", config=PLOT_CONFIG, key=key)


def download(df: pd.DataFrame, name: str, key: str | None = None) -> None:
    st.download_button("Download CSV", df.to_csv(index=False).encode(), f"{name}.csv", "text/csv", key=key or f"dl_{name}")


def eur(x: float) -> str:
    return f"€{x:,.0f}"


def filtered_or_stop() -> data.Filters:
    f: data.Filters = st.session_state["filters"]
    if f.is_empty_selection():
        st.warning("No data selected: choose at least one value in every sidebar filter.")
        st.stop()
    return f


def n_or_stop(f: data.Filters) -> int:
    n = int(data.run("SELECT count(*) n FROM gold.vw_offers_enriched WHERE {WHERE}", f)["n"][0])
    if n == 0:
        st.info("No offers match the current filters. Widen the price range, capacity or categories in the sidebar.")
        st.stop()
    return n
