WITH start_period AS (
  SELECT county_fips, county_name, population, unemployment_rate
  FROM {table}
  WHERE state_fips = :state AND year = :start_year AND snapshot_id = :snapshot
), end_period AS (
  SELECT county_fips, county_name, population, unemployment_rate
  FROM {table}
  WHERE state_fips = :state AND year = :end_year AND snapshot_id = :snapshot
)
SELECT COALESCE(s.county_fips, e.county_fips) AS county_fips,
       COALESCE(s.county_name, e.county_name) AS county_name,
       s.population AS population_start,
       e.population AS population_end,
       100.0 * (e.population - s.population) / NULLIF(s.population, 0)
         AS population_change,
       s.unemployment_rate AS unemployment_start,
       e.unemployment_rate AS unemployment_end,
       e.unemployment_rate - s.unemployment_rate AS unemployment_change
FROM start_period s
FULL OUTER JOIN end_period e ON s.county_fips = e.county_fips
ORDER BY county_fips
LIMIT 100
