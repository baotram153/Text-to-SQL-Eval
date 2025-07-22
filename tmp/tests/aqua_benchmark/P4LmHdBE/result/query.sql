-- Explore for cells
-- Dimensions:
--   car_retails_customers.country
-- Metrics:
--   car_retails_customers | count(car_retails_customers.customernumber)
SELECT
  "car_retails_customers"."country" AS "crc_c_6538d5",
  COUNT("car_retails_customers"."customernumber") AS "customer_count"
FROM
  "car_retails"."customers" "car_retails_customers"
GROUP BY
  1
ORDER BY
  1 ASC
