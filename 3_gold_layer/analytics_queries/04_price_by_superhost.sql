-- Association only: superhosts may differ systematically (room type, city, location); no causal claim.
SELECT is_superhost, observations, round(avg_two_night_total_eur::numeric,2) avg_eur, round(median_two_night_total_eur::numeric,2) median_eur,
       round(avg_guest_satisfaction::numeric,2) avg_satisfaction, round(avg_cleanliness::numeric,2) avg_cleanliness FROM gold.vw_superhost_stats ORDER BY is_superhost;
