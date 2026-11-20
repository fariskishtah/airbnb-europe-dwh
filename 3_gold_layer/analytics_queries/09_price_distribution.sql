-- Price distribution deciles + tail (right-skewed).
SELECT round((percentile_cont(0.1) WITHIN GROUP (ORDER BY two_night_total_eur))::numeric,2) p10,
 round((percentile_cont(0.25) WITHIN GROUP (ORDER BY two_night_total_eur))::numeric,2) p25,
 round((percentile_cont(0.5) WITHIN GROUP (ORDER BY two_night_total_eur))::numeric,2) p50,
 round((percentile_cont(0.75) WITHIN GROUP (ORDER BY two_night_total_eur))::numeric,2) p75,
 round((percentile_cont(0.9) WITHIN GROUP (ORDER BY two_night_total_eur))::numeric,2) p90,
 round((percentile_cont(0.99) WITHIN GROUP (ORDER BY two_night_total_eur))::numeric,2) p99,
 round(max(two_night_total_eur)::numeric,2) max, round(avg(two_night_total_eur)::numeric,2) mean FROM gold.fact_offer_observation;
