```markdown
# Relevant functions
* sum
```### Understanding
I believe you want to calculate the **total price** of products that were shipped to the customer "Rovelli Gifts" between January 1, 2003 and December 31, 2003.

### Analysis
To do this, I'll use these metrics and dimensions from the available fields:
- Metric: Total price = sum of `car_retails_orderdetails.quantityordered * car_retails_orderdetails.priceeach`
- Dimension `car_retails_customers.customername`: To filter for "Rovelli Gifts"
- Dimension `car_retails_orders.shippeddate`: To filter for shipped date between 1/1/2003 and 12/31/2003
- Relationships:
  - `car_retails_orderdetails` links to `car_retails_orders` via `ordernumber`
  - `car_retails_orders` links to `car_retails_customers` via `customernumber`

### References
- [sum](https://docs.holistics.io/as-code/reference/aggregator-functions#sum)

### AQL
```aql
explore {
  measures {
    total_price: car_retails_orderdetails | sum(car_retails_orderdetails.quantityordered * car_retails_orderdetails.priceeach),
  }
  filters {
    car_retails_customers.customername == 'Rovelli Gifts',
    car_retails_orders.shippeddate >= @2003-01-01,
    car_retails_orders.shippeddate <= @2003-12-31,
  }
}
```

### Summary
**Total price** (sum of quantity × price) of products **shipped to "Rovelli Gifts"** between **1/1/2003** and **12/31/2003**.