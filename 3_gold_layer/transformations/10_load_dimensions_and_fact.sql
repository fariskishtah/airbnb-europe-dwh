-- Load Gold from Silver (+ Bronze file metadata). Surrogate keys are assigned by ORDER BY natural key => stable across rebuilds.
INSERT INTO gold.dim_city(city_key, city_name, country, ref_lat, ref_lng)
SELECT row_number() OVER (ORDER BY s.city)::smallint, s.city, r.country, r.lat, r.lng
FROM (SELECT DISTINCT city FROM silver.airbnb_europe_master) s
JOIN gold_ref.city_reference r ON r.display_name = s.city;

INSERT INTO gold.dim_day_type(day_type_key, day_type, source_label)
SELECT row_number() OVER (ORDER BY day_type)::smallint, day_type, day_type || 's'
FROM (SELECT DISTINCT day_type FROM silver.airbnb_europe_master) d;

INSERT INTO gold.dim_room_type(room_type_key, room_type, is_shared, is_private, is_entire)
SELECT row_number() OVER (ORDER BY room_type)::smallint, room_type,
       bool_and(room_shared), bool_and(room_private), room_type = 'Entire home/apt'
FROM silver.airbnb_europe_master GROUP BY room_type;

INSERT INTO gold.dim_host_status(host_status_key, is_superhost, multi_listing_host, business_host, host_status_label)
SELECT row_number() OVER (ORDER BY is_superhost, multi_listing_host, business_host)::smallint,
       is_superhost, multi_listing_host, business_host,
       (CASE WHEN is_superhost THEN 'Superhost' ELSE 'Regular host' END)
       || (CASE WHEN multi_listing_host THEN ' / multi-listing' ELSE '' END)
       || (CASE WHEN business_host THEN ' / business' ELSE '' END)
FROM (SELECT DISTINCT host_is_superhost AS is_superhost, multi_listing_host, business_host FROM silver.airbnb_europe_master) h;

INSERT INTO gold.dim_source_file(source_file_key, source_file, city_key, day_type_key, sha256, md5_verified, size_bytes, source_row_count)
SELECT row_number() OVER (ORDER BY l.source_file)::smallint, l.source_file, c.city_key, d.day_type_key,
       l.sha256, l.md5_verified, l.size_bytes, l.row_count
FROM bronze.ingestion_log l
JOIN gold.dim_city c ON lower(c.city_name) = l.city
JOIN gold.dim_day_type d ON d.source_label = l.day_type;

INSERT INTO gold.fact_offer_observation
SELECT row_number() OVER (ORDER BY s.offer_id)::integer, s.offer_id, c.city_key, d.day_type_key, r.room_type_key,
       h.host_status_key, f.source_file_key, s.source_row_index, s.two_night_total_eur, s.nightly_equivalent_eur,
       s.person_capacity, s.bedrooms, s.cleanliness_rating, s.guest_satisfaction_overall, s.dist_city_center_km,
       s.dist_metro_km, s.attr_index, s.attr_index_norm, s.rest_index, s.rest_index_norm, s.lat, s.lng,
       s.is_studio, s.price_outlier_iqr
FROM silver.airbnb_europe_master s
JOIN gold.dim_city c ON c.city_name = s.city
JOIN gold.dim_day_type d ON d.day_type = s.day_type
JOIN gold.dim_room_type r ON r.room_type = s.room_type
JOIN gold.dim_host_status h ON h.is_superhost = s.host_is_superhost AND h.multi_listing_host = s.multi_listing_host
                           AND h.business_host = s.business_host
JOIN gold.dim_source_file f ON f.source_file = s.source_file;
ANALYZE gold.fact_offer_observation;
