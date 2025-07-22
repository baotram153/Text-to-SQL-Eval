```markdown
# Relevant functions
* count
* sum
* max
```### Understanding
I believe you want to find which **product vendor** has the **most orders** (i.e., the vendor whose products have been ordered the most times), and then calculate the **total estimated earnings** for that vendor (using the sum of quantity ordered × price for their products).

### Analysis
To answer this, I'll use the following models and fields:
- **car_retails_products.productvendor**: The vendor name for each product.
- **car_retails_orderdetails.productcode**: To link orders to products.
- **car_retails_orderdetails.ordernumber**: To count the number of orders per vendor.
- **car_retails_orderdetails.quantityordered** and **car_retails_orderdetails.priceeach**: To estimate earnings per order line.

Metrics and steps:
1. **Metric `order_count`**: Count of orders per vendor (count of orderdetails rows per vendor).
2. **Metric `total_earnings`**: Sum of (quantityordered × priceeach) per vendor.
3. **Metric `vendor_rank_by_orders`**: Rank vendors by order count (descending).
4. **Dimension `car_retails_products.productvendor`**: The vendor name.

### References
- [Aggregate Functions: count, sum](https://docs.holistics.io/as-code/reference/aggregator-functions)
- [window functions: rank](https://docs.holistics.io/as-code/reference/window-function)

### AQL
```aql
metric order_count = car_retails_orderdetails | count(car_retails_orderdetails.ordernumber);
metric total_earnings = car_retails_orderdetails | sum(car_retails_orderdetails.quantityordered * car_retails_orderdetails.priceeach);
metric vendor_rank_by_orders = rank(order: order_count | desc());

explore {
  dimensions {
    vendor_name: car_retails_products.productvendor,
  }
  measures {
    order_count: order_count,
    total_estimated_earnings: total_earnings,
    vendor_rank_by_orders: vendor_rank_by_orders,
  }
  filters {
    vendor_rank_by_orders == 1,
  }
  sorts {
    order_count DESC,
    vendor_name ASC,
  }
}
```

### Summary
Finds the **vendor with the most orders** and calculates their **total estimated earnings** (sum of quantity × price for all their order lines). Uses metrics for order count, total earnings, and vendor ranking.