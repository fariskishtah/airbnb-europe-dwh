SELECT city, round(avg_guest_satisfaction::numeric,2) avg_satisfaction, round(avg_cleanliness::numeric,2) avg_cleanliness FROM gold.vw_city_kpis ORDER BY avg_satisfaction DESC;
