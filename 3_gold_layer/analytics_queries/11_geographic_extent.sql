SELECT city, count(*) observations, round(min(lat)::numeric,4) lat_min, round(max(lat)::numeric,4) lat_max, round(min(lng)::numeric,4) lng_min, round(max(lng)::numeric,4) lng_max
FROM gold.vw_offers_enriched GROUP BY city ORDER BY city;
