-- Explore for grand-total
-- Metrics:
--   car_retails_orderdetails | sum(car_retails_orderdetails.quantityordered * car_re...
SELECT
  SUM(("car_retails_orderdetails"."quantityordered" * "car_retails_orderdetails"."priceeach")) AS "total_price"
FROM
  "car_retails"."orderdetails" "car_retails_orderdetails"
  LEFT JOIN "car_retails"."orders" "car_retails_orders" ON "car_retails_orderdetails"."ordernumber" = "car_retails_orders"."ordernumber"
  LEFT JOIN "car_retails"."customers" "car_retails_customers" ON "car_retails_orders"."customernumber" = "car_retails_customers"."customernumber"
WHERE
  ("car_retails_customers"."customername" = ('Rovelli Gifts')) AND
  (CAST ( "car_retails_orders"."shippeddate" AS date ) <= CAST ( '2003-12-31' AS date )) AND
  (CAST ( "car_retails_orders"."shippeddate" AS date ) >= CAST ( '2003-01-01' AS date ))
