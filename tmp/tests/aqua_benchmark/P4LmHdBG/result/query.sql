-- Explore for cells
-- Dimensions:
--   car_retails_employees.employeenumber (car_retails_payments->car_retails_customers->car_retails_employees)
--   car_retails_employees.firstname (car_retails_payments->car_retails_customers->car_retails_employees)
--   car_retails_employees.lastname (car_retails_payments->car_retails_customers->car_retails_employees)
-- Metrics:
--   car_retails_payments | sum(car_retails_payments.amount)
SELECT
  "car_retails_employees"."employeenumber" AS "cre_e_0b2f9b",
  "car_retails_employees"."firstname" AS "cre_f_76292b",
  "car_retails_employees"."lastname" AS "cre_l_eebe4a",
  SUM("car_retails_payments"."amount") AS "total_payment_revenue"
FROM
  "car_retails"."payments" "car_retails_payments"
  LEFT JOIN "car_retails"."customers" "car_retails_customers" ON "car_retails_payments"."customernumber" = "car_retails_customers"."customernumber"
  LEFT JOIN "car_retails"."employees" "car_retails_employees" ON "car_retails_customers"."salesrepemployeenumber" = "car_retails_employees"."employeenumber"
WHERE
  (CAST ( "car_retails_payments"."paymentdate" AS date ) >= CAST ( '2004-01-01' AS date )) AND
  (CAST ( "car_retails_payments"."paymentdate" AS date ) < CAST ( '2005-01-01' AS date ))
GROUP BY
  1,
  2,
  3
ORDER BY
  4 DESC,
  1 ASC
