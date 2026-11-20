import plotly.graph_objects as go
import streamlit as st

from components import data, ui

ui.header("Data Quality & Pipeline", "Bronze → Silver → Gold → Analytics: ingestion status, reconciliation and automated checks")
q = data.query

rec = q("SELECT object, row_count FROM gold.vw_layer_reconciliation")
cnt = dict(zip(rec.object, rec.row_count))
b, s, g = cnt["bronze.raw_offers"], cnt["silver.airbnb_europe_master"], cnt["gold.fact_offer_observation"]
files = q("SELECT * FROM bronze.ingestion_log ORDER BY source_file")
ui.kpis([("Source files", f"{len(files)}", f"{int(files.md5_verified.sum())} MD5-verified"), ("Bronze rows", f"{b:,}", "raw text"),
         ("Silver rows", f"{s:,}", "typed + validated"), ("Gold fact rows", f"{g:,}", "star schema"),
         ("Reconciled", "YES" if b == s == g else "NO", "bronze = silver = gold")])
st.write("")
fig = go.Figure(go.Sankey(
    arrangement="fixed",
    node=dict(label=[f"Raw CSV ({len(files)} files)", f"Bronze {b:,}", f"Silver {s:,}", f"Gold {g:,}", "Analytics"],
              color=["#94A3B8", "#F59E0B", "#3B82F6", "#22D3EE", "#34D399"], pad=20, thickness=18,
              x=[0.02, 0.28, 0.52, 0.76, 0.98], y=[0.5] * 5),
    link=dict(source=[0, 1, 2, 3], target=[1, 2, 3, 4], value=[b, s, g, g],
              color=["rgba(148,163,184,.35)", "rgba(245,158,11,.35)", "rgba(59,130,246,.35)", "rgba(34,211,238,.35)"])))
fig.update_layout(title="Data lineage (row counts)")
ui.plot(fig, "dq_lineage", 300)

st.subheader("Automated data-quality checks (latest run)")
dq = q("SELECT * FROM meta.dq_result WHERE run_id = (SELECT run_id FROM meta.dq_result ORDER BY id DESC LIMIT 1) ORDER BY id")
if dq.empty:
    st.warning("No data-quality run recorded yet. Run `make quality`.")
else:
    p = int((dq.status == "PASS").sum())
    ui.kpis([("Checks passed", f"{p}/{len(dq)}", "latest run"), ("Failed", f"{len(dq) - p}", "should be 0"), ("Run", dq.run_id[0], str(dq.checked_at[0])[:19])])
    layer = st.radio("Layer", ["all", "bronze", "silver", "gold"], horizontal=True)
    v = dq if layer == "all" else dq[dq.layer == layer]
    st.dataframe(v[["layer", "check_name", "expected", "actual", "status", "detail"]], width="stretch", hide_index=True)
    ui.download(dq, "data_quality_results")

st.subheader("Pipeline execution metadata")
runs = q("SELECT run_id, layer, step, status, rows_affected, started_at, finished_at, detail FROM meta.pipeline_run ORDER BY id DESC LIMIT 20")
st.dataframe(runs, width="stretch", hide_index=True)

st.subheader("Null and duplicate checks (live SQL)")
nl = q("""SELECT 'null cells in Silver (any column)' AS check_name, count(*) AS violations FROM silver.airbnb_europe_master s
    WHERE s IS NOT DISTINCT FROM NULL OR num_nulls(s.*) > 0
    UNION ALL SELECT 'duplicate offer_id in Silver', count(*) - count(DISTINCT offer_id) FROM silver.airbnb_europe_master
    UNION ALL SELECT 'duplicate (file,row) in Gold fact', count(*) - count(DISTINCT (source_file_key, source_row_index)) FROM gold.fact_offer_observation
    UNION ALL SELECT 'orphan fact rows (city)', count(*) FROM gold.fact_offer_observation f LEFT JOIN gold.dim_city c USING(city_key) WHERE c.city_key IS NULL""")
st.dataframe(nl, width="stretch", hide_index=True)

st.subheader("Source file inventory (Bronze ingestion log)")
st.dataframe(files[["source_file", "city", "day_type", "row_count", "column_count", "size_bytes", "md5_verified", "sha256", "ingested_at"]],
             width="stretch", hide_index=True)
ui.download(files, "bronze_ingestion_log")
ui.note("Known schema adaptations: no calendar date, host id, listing id or property type exists in the source, so there is no Date, Host or Property dimension.")
