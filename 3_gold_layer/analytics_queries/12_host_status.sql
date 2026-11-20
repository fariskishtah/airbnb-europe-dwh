SELECT host_status_label, count(*) observations, round(avg(two_night_total_eur)::numeric,2) avg_eur FROM gold.vw_offers_enriched GROUP BY 1 ORDER BY 2 DESC;
