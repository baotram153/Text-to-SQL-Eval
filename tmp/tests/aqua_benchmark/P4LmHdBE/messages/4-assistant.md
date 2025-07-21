```markdown
# Relevant functions
* count
```### Understanding
I believe you want to list each country and show how many customers are in each country.

### Analysis
To do this, I'll use:
* Dimension `car_retails_customers.country`: The country of each customer.
* Metric: Count of customers per country, using the primary key `car_retails_customers.customernumber`.

### References
* [Aggregate Functions: count()](https://docs.holistics.io/as-code/reference/aggregator-functions)

### AQL
```aql
explore {
  dimensions {
    country: car_retails_customers.country,
  }
  measures {
    customer_count: car_retails_customers | count(car_retails_customers.customernumber),
  }
  sorts {
    country ASC,
  }
}
```

### Summary
**Count of customers** per **country** using `car_retails_customers.country` and counting `car_retails_customers.customernumber`.