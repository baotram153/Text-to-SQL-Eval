-- Explore for cells
-- Dimensions:
--   car_retails_offices.city (car_retails_employees->car_retails_offices)
-- Metrics:
--   car_retails_employees | count_distinct(car_retails_employees.employeenumber)
SELECT
  "car_retails_offices"."city" AS "cro_c_8a8b29",
  COUNT(DISTINCT "car_retails_employees"."employeenumber") AS "employee_count"
FROM
  "car_retails"."employees" "car_retails_employees"
  LEFT JOIN "car_retails"."offices" "car_retails_offices" ON "car_retails_employees"."officecode" = "car_retails_offices"."officecode"
WHERE
  "car_retails_offices"."city" = 'Sydney'
GROUP BY
  1
ORDER BY
  1 ASC
