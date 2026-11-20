-- Price by distance band to city centre (km) and Pearson correlations (association, not causation).
SELECT CASE WHEN dist_city_center_km < 1 THEN '0-1 km' WHEN dist_city_center_km < 3 THEN '1-3 km' WHEN dist_city_center_km < 5 THEN '3-5 km' ELSE '5+ km' END AS dist_band,
       count(*) observations, round(avg(two_night_total_eur)::numeric,2) avg_eur,
       round((percentile_cont(0.5) WITHIN GROUP (ORDER BY two_night_total_eur))::numeric,2) median_eur
FROM gold.fact_offer_observation GROUP BY 1 ORDER BY min(dist_city_center_km);
