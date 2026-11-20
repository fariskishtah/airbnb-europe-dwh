-- Semantic layer: analytical views (metric definitions documented in docs/KPI_DEFINITIONS.md).
CREATE OR REPLACE VIEW gold.vw_offers_enriched AS
SELECT f.offer_key, f.offer_id, c.city_name AS city, c.country, d.day_type, r.room_type, r.is_shared, r.is_private,
       h.is_superhost, h.multi_listing_host, h.business_host, h.host_status_label, s.source_file,
       f.source_row_index, f.two_night_total_eur, f.nightly_equivalent_eur, f.person_capacity, f.bedrooms,
       f.cleanliness_rating, f.guest_satisfaction_overall, f.dist_city_center_km, f.dist_metro_km,
       f.attr_index, f.attr_index_norm, f.rest_index, f.rest_index_norm, f.lat, f.lng, f.is_studio, f.price_outlier_iqr
FROM gold.fact_offer_observation f
JOIN gold.dim_city c USING (city_key) JOIN gold.dim_day_type d USING (day_type_key)
JOIN gold.dim_room_type r USING (room_type_key) JOIN gold.dim_host_status h USING (host_status_key)
JOIN gold.dim_source_file s USING (source_file_key);

CREATE OR REPLACE VIEW gold.vw_city_kpis AS
SELECT city, country, count(*) AS observations,
       avg(two_night_total_eur) AS avg_two_night_total_eur,
       percentile_cont(0.5) WITHIN GROUP (ORDER BY two_night_total_eur) AS median_two_night_total_eur,
       avg(nightly_equivalent_eur) AS avg_nightly_equivalent_eur,
       avg(guest_satisfaction_overall) AS avg_guest_satisfaction, avg(cleanliness_rating) AS avg_cleanliness,
       avg(dist_city_center_km) AS avg_dist_city_center_km, avg(dist_metro_km) AS avg_dist_metro_km,
       avg(person_capacity) AS avg_person_capacity
FROM gold.vw_offers_enriched GROUP BY city, country;

CREATE OR REPLACE VIEW gold.vw_city_daytype_kpis AS
SELECT city, day_type, count(*) AS observations, avg(two_night_total_eur) AS avg_two_night_total_eur,
       percentile_cont(0.5) WITHIN GROUP (ORDER BY two_night_total_eur) AS median_two_night_total_eur
FROM gold.vw_offers_enriched GROUP BY city, day_type;

CREATE OR REPLACE VIEW gold.vw_weekend_premium AS
SELECT city,
       max(avg_two_night_total_eur) FILTER (WHERE day_type='weekend') AS avg_weekend_eur,
       max(avg_two_night_total_eur) FILTER (WHERE day_type='weekday') AS avg_weekday_eur,
       max(median_two_night_total_eur) FILTER (WHERE day_type='weekend') AS median_weekend_eur,
       max(median_two_night_total_eur) FILTER (WHERE day_type='weekday') AS median_weekday_eur,
       100.0 * (max(avg_two_night_total_eur) FILTER (WHERE day_type='weekend')
              / max(avg_two_night_total_eur) FILTER (WHERE day_type='weekday') - 1) AS avg_weekend_diff_pct,
       100.0 * (max(median_two_night_total_eur) FILTER (WHERE day_type='weekend')
              / max(median_two_night_total_eur) FILTER (WHERE day_type='weekday') - 1) AS median_weekend_diff_pct
FROM gold.vw_city_daytype_kpis GROUP BY city;

CREATE OR REPLACE VIEW gold.vw_room_type_stats AS
SELECT room_type, count(*) AS observations, avg(two_night_total_eur) AS avg_two_night_total_eur,
       percentile_cont(0.5) WITHIN GROUP (ORDER BY two_night_total_eur) AS median_two_night_total_eur,
       avg(guest_satisfaction_overall) AS avg_guest_satisfaction, avg(person_capacity) AS avg_person_capacity
FROM gold.vw_offers_enriched GROUP BY room_type;

CREATE OR REPLACE VIEW gold.vw_superhost_stats AS
SELECT is_superhost, count(*) AS observations, avg(two_night_total_eur) AS avg_two_night_total_eur,
       percentile_cont(0.5) WITHIN GROUP (ORDER BY two_night_total_eur) AS median_two_night_total_eur,
       avg(guest_satisfaction_overall) AS avg_guest_satisfaction, avg(cleanliness_rating) AS avg_cleanliness
FROM gold.vw_offers_enriched GROUP BY is_superhost;

CREATE OR REPLACE VIEW gold.vw_capacity_stats AS
SELECT person_capacity, count(*) AS observations, avg(two_night_total_eur) AS avg_two_night_total_eur,
       percentile_cont(0.5) WITHIN GROUP (ORDER BY two_night_total_eur) AS median_two_night_total_eur
FROM gold.vw_offers_enriched GROUP BY person_capacity;

-- Row-count reconciliation across layers (used by the data-quality page).
CREATE OR REPLACE VIEW gold.vw_layer_reconciliation AS
SELECT 'bronze.raw_offers' AS object, count(*)::bigint AS row_count FROM bronze.raw_offers
UNION ALL SELECT 'silver.airbnb_europe_master', count(*) FROM silver.airbnb_europe_master
UNION ALL SELECT 'gold.fact_offer_observation', count(*) FROM gold.fact_offer_observation;
