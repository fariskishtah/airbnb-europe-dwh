SELECT * FROM (SELECT room_type, observations, round(avg_two_night_total_eur::numeric,2) avg_eur,
 round(median_two_night_total_eur::numeric,2) median_eur, round(avg_guest_satisfaction::numeric,2) avg_satisfaction FROM gold.vw_room_type_stats) t ORDER BY avg_eur DESC;
