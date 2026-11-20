-- Average and median two-night total (2 guests, 2 nights, EUR) by city. Median shown because prices are right-skewed.
SELECT city, observations, round(avg_two_night_total_eur::numeric,2) AS avg_eur, round(median_two_night_total_eur::numeric,2) AS median_eur,
       round(avg_nightly_equivalent_eur::numeric,2) AS avg_nightly_equivalent_eur
FROM gold.vw_city_kpis ORDER BY avg_eur DESC;
