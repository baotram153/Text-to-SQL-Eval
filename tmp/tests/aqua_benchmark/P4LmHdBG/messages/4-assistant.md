```markdown
# Relevant functions
* sum
* group
* select
* count
* where
* avg
```### Understanding
I believe you want to find out which sales representatives (employees) generated the highest total payment revenue in the year 2004. This means summing up all payments received from customers in 2004, and attributing those payments to the sales rep (employee) responsible for each customer.

### Analysis
To achieve this, I'll use the following models and fields:
- `car_retails_payments`: Contains payment data, including `amount` and `paymentdate`.
- `car_retails_customers`: Links each payment to a customer and provides the `salesrepemployeenumber` (the employee responsible for the customer).
- `car_retails_employees`: Contains employee details, such as `employeenumber`, `firstname`, and `lastname`.

Metrics and dimensions:
- Metric: Total payment revenue per sales rep in 2004 (`car_retails_payments | sum(car_retails_payments.amount)`).
- Dimension: Sales rep employee number (`car_retails_employees.employeenumber`).
- Dimension: Sales rep first and last name (`car_retails_employees.firstname`, `car_retails_employees.lastname`).
- Filter: Only include payments where `car_retails_payments.paymentdate` is in 2004.

### References
- [sum](https://docs.holistics.io/as-code/reference/aggregator-functions#sum)
- [date_trunc](https://docs.holistics.io/as-code/reference/time-intelligence-functions#date_trunc)
- [Explore Filters](https://docs.holistics.io/as-code/reference/operator)
- [Relationships](https://docs.holistics.io/as-code/reference/model-relationship)

### AQL
```aql
explore {
  dimensions {
    sales_rep_id: car_retails_employees.employeenumber,
    sales_rep_first_name: car_retails_employees.firstname,
    sales_rep_last_name: car_retails_employees.lastname,
  }
  measures {
    total_payment_revenue: car_retails_payments | sum(car_retails_payments.amount),
  }
  filters {
    car_retails_payments.paymentdate is @(2004),
  }
  sorts {
    total_payment_revenue DESC,
    sales_rep_id ASC,
  }
}
```

### Summary
**Total payment revenue** per **sales representative** for payments received in **2004**, sorted by highest revenue.