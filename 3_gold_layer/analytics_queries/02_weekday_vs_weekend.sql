-- Weekend vs weekday difference per city (separate samples; NOT the same listings observed on both).
SELECT city, round(avg_weekday_eur::numeric,2) avg_weekday, round(avg_weekend_eur::numeric,2) avg_weekend,
       round(avg_weekend_diff_pct::numeric,2) avg_diff_pct, round(median_weekday_eur::numeric,2) med_weekday,
       round(median_weekend_eur::numeric,2) med_weekend, round(median_weekend_diff_pct::numeric,2) median_diff_pct
FROM gold.vw_weekend_premium ORDER BY avg_diff_pct DESC;
