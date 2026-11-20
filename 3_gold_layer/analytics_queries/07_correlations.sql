SELECT round(corr(two_night_total_eur, dist_city_center_km)::numeric,3) price_vs_dist_center,
       round(corr(two_night_total_eur, dist_metro_km)::numeric,3) price_vs_dist_metro,
       round(corr(two_night_total_eur, guest_satisfaction_overall)::numeric,3) price_vs_satisfaction,
       round(corr(two_night_total_eur, cleanliness_rating)::numeric,3) price_vs_cleanliness,
       round(corr(two_night_total_eur, person_capacity)::numeric,3) price_vs_capacity,
       round(corr(two_night_total_eur, bedrooms)::numeric,3) price_vs_bedrooms,
       round(corr(two_night_total_eur, attr_index_norm)::numeric,3) price_vs_attraction_idx
FROM gold.fact_offer_observation;
