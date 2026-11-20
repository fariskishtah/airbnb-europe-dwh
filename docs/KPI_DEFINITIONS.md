# KPI / semantic layer (views in `3_gold_layer/ddl/03_gold_views.sql`)
Unit of price: **EUR, two guests, two nights** unless stated. No time-series KPIs exist (the source has no dates).

| KPI | SQL | Unit | Interpretation / limitation |
|---|---|---|---|
| Total observations | `count(*)` on `fact_offer_observation` | rows | offer observations, **not** unique listings |
| Cities covered | `count(DISTINCT city)` | count | 10 in source |
| Average two-night total | `avg(two_night_total_eur)` | EUR | pulled up by a long right tail |
| Median two-night total | `percentile_cont(0.5) WITHIN GROUP (ORDER BY two_night_total_eur)` | EUR | preferred for skewed prices |
| Nightly equivalent | `two_night_total_eur / 2` | EUR/night | **derived**, not an observed nightly rate; not per person |
| Avg guest satisfaction | `avg(guest_satisfaction_overall)` | 0–100 | listing-level overall rating; ceiling effect (median 95) |
| Avg cleanliness | `avg(cleanliness_rating)` | 0–10 | ceiling effect (median 10) |
| Weekend difference % | `100*(avg_weekend/avg_weekday-1)` (`vw_weekend_premium`) | % | two *different* samples; not a within-listing price change |
| Room-type comparison | `vw_room_type_stats` | EUR | differences confounded by city/capacity |
| Superhost vs other | `vw_superhost_stats` | EUR | association only |
| Avg distance to city centre | `avg(dist_city_center_km)` | km | |
| Price outlier flag | price > Q3+1.5·IQR within city/day type | boolean | flagged, never removed |
Filters: all dashboard KPIs honour the sidebar filters (city, day type, room type, superhost, price range, capacity).
