# Power BI deliverable: NOT INCLUDED

The original Sprint 1 assignment requests a Power BI `.pbix` report.

**This submission does not include a Power BI report. No `.pbix` file exists, and none was generated, imitated or simulated.**
Power BI Desktop / Service were not installed or used (a deliberate constraint of this submission: macOS, no paid services).

## What is provided instead (a documented deviation)
A SQL-connected **Streamlit + Plotly** dashboard, `4_web_dashboard/`, which reads every number live from the PostgreSQL
Gold star schema (read-only session, parameterised SQL):

| Power BI expectation | Streamlit replacement |
|---|---|
| Connect to the SQL warehouse | `components/data.py` -> PostgreSQL `gold.*` views |
| Report pages / visuals | 8 pages: overview, cities, pricing, rooms, ratings, map, data-quality, SQL explorer |
| Slicers | Global sidebar filters (city, day type, room type, superhost, price range, capacity) that change the SQL |
| Export | CSV downloads, Plotly PNG export |

## What is NOT equivalent
* No `.pbix`, no DAX measures, no Power BI theme/bookmarks/row-level security.
* A reviewer expecting to open a `.pbix` file cannot do so. The original requirement is **NOT SATISFIED**; the Streamlit
  dashboard is a functional **alternative**, not a substitute that meets the exact deliverable.
