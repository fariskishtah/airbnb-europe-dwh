# External enrichment decision (Silver layer)
The training slides suggest Selenium scraping when extra features are needed. Assessment:

1. **Necessity** – the source already provides price, room type, capacity, bedrooms, host flags, ratings, distances, attraction/restaurant indices and coordinates (0 missing values). Nothing required for the star schema is missing.
2. **Join key** – there is no listing id, URL, host id or date. Matching historical rows to today's Airbnb listings would require guessing (coordinates are perturbed) and would mix a 2020-era snapshot with current data.
3. **Legality** – scraping Airbnb conflicts with its terms of service and its anti-bot protections; bypassing them is out of scope. No personal host data would be collected either way.

**Decision: no scraping, no new columns.** The only external data used are two public-knowledge reference attributes (country and approximate centre coordinates of the 10 cities in `airbnb_dwh/reference.py`), used for `dim_city.country` and a coordinate sanity check; they are labelled as reference data.
