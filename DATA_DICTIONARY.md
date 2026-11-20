# Data dictionary
Source columns (Zenodo record descriptions) → Silver / Gold names.

| Source | Silver / Gold column | Type | Meaning |
|---|---|---|---|
| (unnamed index) | `source_row_index` | int | zero-based row index inside the file; restarts per file; **not a listing id** |
| file name | `source_file`, `city`, `day_type` | text | lineage: `rome_weekends.csv` → Rome / weekend |
| – | `offer_id` | text | stable key `{city}_{daytype}_{row:05d}` e.g. `amsterdam_weekday_00000` |
| `realSum` | `real_sum`, `two_night_total_eur` | float | full price for 2 people, 2 nights, EUR |
| – | `nightly_equivalent_eur` | float | derived `realSum/2` |
| `room_type` | `room_type` | text | Entire home/apt, Private room, Shared room |
| `room_shared`, `room_private` | same | bool | dummies |
| `person_capacity` | same | int | max guests (2–6) |
| `host_is_superhost` | same | bool | superhost dummy |
| `multi` | `multi_listing_host` | bool | host has 2–4 offers |
| `biz` | `business_host` | bool | host has more than 4 offers |
| `cleanliness_rating` | same | float | 0–10 |
| `guest_satisfaction_overall` | same | float | 0–100 |
| `bedrooms` | same | int | 0 = studio |
| `dist` | `dist_city_center_km` | float | km to city centre |
| `metro_dist` | `dist_metro_km` | float | km to nearest metro |
| `attr_index`, `attr_index_norm` | same | float | attraction index (raw, normalised 0–100) |
| `rest_index`, `rest_index_norm` | same | float | restaurant index (raw, normalised 0–100) |
| `lng`, `lat` | same | float | listing coordinates |
| – | `is_studio` | bool | derived `bedrooms = 0` |
| – | `price_outlier_iqr` | bool | derived upper Tukey fence per city/day type |
Gold tables: see `ARCHITECTURE.md` and `3_gold_layer/ddl/02_gold_star_schema.sql`. Bronze stores every value as text exactly as in the CSV (`realSum` → column `realsum`, unnamed index → `source_row_index`).
