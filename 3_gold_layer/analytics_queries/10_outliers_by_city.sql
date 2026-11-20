-- Upper Tukey-fence outliers per city/day type (flag computed in Silver).
SELECT city, count(*) FILTER (WHERE price_outlier_iqr) outliers, count(*) observations,
       round(100.0*count(*) FILTER (WHERE price_outlier_iqr)/count(*),2) outlier_pct
FROM gold.vw_offers_enriched GROUP BY city ORDER BY outlier_pct DESC;
