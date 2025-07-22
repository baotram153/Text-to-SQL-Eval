WITH "aql__t1" AS (
  -- Dimensions:
  --   car_retails_products.productvendor (car_retails_orderdetails->car_retails_products)
  -- Metrics:
  --   car_retails_orderdetails | count(car_retails_orderdetails.ordernumber)
  --   car_retails_orderdetails | sum(car_retails_orderdetails.quantityordered * car_re...
  SELECT
    "car_retails_products"."productvendor" AS "car_retails_products->productvendor",
    COUNT("car_retails_orderdetails"."ordernumber") AS "count_car_retails_orderdetails->ordernumber",
    SUM(("car_retails_orderdetails"."quantityordered" * "car_retails_orderdetails"."priceeach")) AS "sum_5eaa1"
  FROM
    "car_retails"."orderdetails" "car_retails_orderdetails"
    LEFT JOIN "car_retails"."products" "car_retails_products" ON "car_retails_orderdetails"."productcode" = "car_retails_products"."productcode"
  GROUP BY
    1
), "aql__t4" AS (
  -- Explore for cells
  -- Dimensions:
  --   car_retails_products.productvendor
  -- Metrics:
  --   car_retails_orderdetails | count(car_retails_orderdetails.ordernumber)
  --   car_retails_orderdetails | sum(car_retails_orderdetails.quantityordered * car_re...
  --   rank(order: order_count | desc())
  SELECT
    "aql__t1"."car_retails_products->productvendor" AS "crp_p_0aa5b5",
    "aql__t1"."count_car_retails_orderdetails->ordernumber" AS "order_count",
    "aql__t1"."sum_5eaa1" AS "total_earnings",
    CAST ( NULL AS numeric ) AS "vendor_rank_by_orders"
  FROM
    "aql__t1"
  WHERE
    CAST ( NULL AS numeric ) = 1.0
)
SELECT
  "aql__t4"."crp_p_0aa5b5" AS "crp_p_0aa5b5",
  "aql__t4"."order_count" AS "order_count",
  "aql__t4"."total_earnings" AS "total_earnings",
  "aql__t4"."vendor_rank_by_orders" AS "vendor_rank_by_orders"
FROM
  "aql__t4"
WHERE
  "aql__t4"."vendor_rank_by_orders" = 1.0
ORDER BY
  2 DESC,
  1 ASC
