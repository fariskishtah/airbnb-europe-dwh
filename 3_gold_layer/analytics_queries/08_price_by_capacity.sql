SELECT person_capacity, observations, round(avg_two_night_total_eur::numeric,2) avg_eur, round(median_two_night_total_eur::numeric,2) median_eur FROM gold.vw_capacity_stats ORDER BY 1;
