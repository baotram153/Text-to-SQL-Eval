```markdown
# Relevant functions
* count
```### Understanding
I believe you want to calculate the total number of employees who are located in Sydney.

### Analysis
To do this, I'll use the following:
* Dimension `car_retails_offices.city` (from available fields): Used to filter for "Sydney".
* Dimension `car_retails_employees.employeenumber` (from available fields): Unique identifier for employees, which we can count to get the number of employees.
* The relationship between `car_retails_employees` and `car_retails_offices` is already defined via `officecode`.

We'll count the number of unique employee numbers where the office city is Sydney.

### References
* [Aggregate Functions: count, count_distinct](https://docs.holistics.io/as-code/reference/aggregator-functions)

### AQL
```aql
explore {
  dimensions {
    office_city: car_retails_offices.city,
  }
  measures {
    employee_count: car_retails_employees | count_distinct(car_retails_employees.employeenumber),
  }
  filters {
    car_retails_offices.city == 'Sydney',
  }
  sorts {
    office_city ASC,
  }
}
```

### Summary
**Count of employees** (by unique employee number) **in Sydney**.