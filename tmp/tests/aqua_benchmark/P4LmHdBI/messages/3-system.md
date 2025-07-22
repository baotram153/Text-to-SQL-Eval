You have found these documents that are useful to perform the user's analytic calculation:
<documents>

 <document index="1" title="Aggregate Functions (Aggregators)" url="https://docs.holistics.io/as-code/reference/aggregator-functions">
  Aggregate Functions are functions that group values of multiple rows into a single summary value. They are equivalent to aggregate functions that SQL supports (SUM, COUNT, AVG, MAX, MIN,...). For more information about how to use them, please refer to their [concept](/as-code/amql/aql-concepts-grouping) page.

---
### count

```jsx
count(field)
count(table, field)
```

```jsx title="Examples"
count(orders.id)
count(orders, orders.id)

// with pipe
orders | count(orders.id)
```

**Description**

Counts the total number of items in a group, not including NULL values.

**Return type**

Whole number

---
### count_if

```jsx
count_if(truefalse_field)
count_if(table, condition)
```

```jsx title="Examples"
count_if(orders.country == 'Vietnam')

// with pipe
orders | count_if(orders.country == 'Vietnam')
```

**Description**

Counts total rows from one table that satisfy the given condition.

**Return type**

Whole number

---

### count_distinct

```jsx
count_distinct(field)
count_distinct(table, field)
```

```jsx title="Examples"
count_distinct(orders.id)
count_distinct(orders, orders.id)

// with pipe
orders | count_distinct(orders.id)
```

**Description**

Counts the total number of distinct items in a group, not including NULL values.

**Return type**

Whole number

---

### average (alias: avg)

```jsx
average(field)
average(table, field)
```

```jsx
average(orders.value)
average(orders, orders.value)

// with pipe
orders | average(orders.value)
```

**Description**

Averages the values of items in a group, not including NULL values.

**Return type**

Number

---

### min

```jsx
min(field)
min(table, field)
```

```jsx title="Examples"
min(orders.quantity)
min(orders, orders.quantity)

// with pipe
orders | min(orders.quantity)
```

**Description**

Return the item in the group with the smallest value, not including NULL values.

**Return type**

Vary

---

### max

```jsx
max(field)
max(table, field)
```

```jsx
max(order_item.quantity)
max(orders, order_item.quantity)

// with pipe
orders | max(order_item.quantity)
```

**Description**

Returns the item in the group with the largest value, not including NULL values.

**Return type**

Varies

---

### sum

```jsx
sum(field)
sum(table, field)
```

```jsx
sum(order_item.quantity)
sum(order_items, order_item.quantity)

// with pipe
order_items | sum(order_item.quantity)
```

**Description**

Sums the value in the group, not including NULL values.

**Return type**

Number

---

### median

```jsx
median(field)
median(table, field)
```

```jsx title="Examples"
median(orders.quantity)
median(orders, orders.quantity)

// with pipe
orders | median(orders.quantity)
```

**Description**

Computes the median of the values in the group, not including NULL values.

**Return type**

Number

---

### stdev

```jsx
stdev(field)
stdev(table, field)
```

```jsx title="Examples"
stdev(orders.id)
stdev(orders, orders.id)

// with pipe
orders | stdev(orders.id)
```

**Description**

Computes the standard deviation (sample) of the values in the group, not including NULL values.

**Return type**

Number

---

### stdevp

```jsx
stdevp(field)
stdevp(table, field)
```

```jsx title="Examples"
stdevp(orders.id)
stdevp(orders, orders.id)

// with pipe
orders | stdevp(orders.id)
```

**Description**

Computes the standard deviation (population) of the values in the group, not including NULL values.

**Return type**

Number

---

### var

```jsx
var(field)
var(table, field)
```

```jsx title="Examples"
var(orders.id)
var(orders, orders.id)

// with pipe
orders | var(orders.id)
```

**Description**

Returns the variance (sample) of the values in the group, not including NULL values.

**Return type**

Number

---

### varp

```jsx
varp(field)
varp(table, field)
```

```jsx title="Examples"
varp(orders.id)
varp(orders, orders.id)

// with pipe
orders | varp(orders.id)
```

**Description**

Returns the variance (population) of the values in the group, not including NULL values.

**Return type**

Number

---
  </document>

 <document index="2" title="window_count" url="https://docs.holistics.io/as-code/reference/window_count">
  :::tip Knowledge Checkpoint
Readings that will help you understand this documentation better:
- [Window Functions Overview](/as-code/reference/window-function)
:::

## Definition
A window aggregation function that returns the count of rows in a range relative to the current row.

**Syntax**
```jsx
window_count(agg_expr)
window_count(agg_expr, order: order_expr, ...)
window_count(agg_expr, range, order: order_expr, ...)
window_count(agg_expr, range, order: order_expr, ..., reset: partition_expr, ...)
window_count(agg_expr, range, order: order_expr, ..., partition: partition_expr, ...)
```

```jsx title="Examples"
window_count(count(users.id))
window_count(count(users.id), order: count(users.id) | desc())
window_count(count(users.id), -2..2, order: users.created_at | month())
window_count(count(users.id), order: users.created_at | month(), reset: users.gender)
```


**Input**
- `agg_expr` (**required**): An aggregation expression that we want to count.
- `range` (**optional**): A range of rows to include in the count. Negative values indicate rows before the current row, and positive values indicate rows after the current row, while 0 indicates the current row. If the beginning or end of the range is not specified, the range will include all rows from the beginning or end of the table. By default, if the range is not specified:
  - If `order` is specified, the range is `..0` (from the first row to the current row).
  - If `order` is not specified, the range is `..` (from the first row to the last row).
- `order` (**required**, **repeatable**): A field that is used for ordering. The order is default to ascending. The order can be set explicitly with `asc()` or `desc()`.
  :::warning
  If the specified order does not uniquely identify rows, the result of the function can be non-deterministic. For example, if you use `order: users.age`, and there are multiple users with the same age in the same partition, the result can be unexpected.
  :::
- `partition` or `reset` (**repeatable**, **optional**): A field that is used for partitioning the table. If partitions are not specified:
  - If `order` is specified, the table will be partitioned by all other grouping columns.
  - If `order` is not specified, the table will be considered as a single partition.

**Output**

The count of the current row and the rows within the specified range.

## Sample Usages

Refer to the sample usages in [window_sum](/as-code/reference/window_sum#sample-usages).
  </document>

</documents>

Now generate the AQL expression to perform the last calculation requested by user.
Answer in Markdown format using the following template (without the XML tags):

<template>
  ### Understanding
  <!-- state your understanding of the question and any assumptions you have made -->
  I believe you want to calculate ...
  ### Analysis
  <!-- break down the solution into metrics, dimensions, filters -->
  To do so, I'm preparing these metrics and dimensions based on the available fields of models `model_1`, `model_2`:
  * Metric `metric_1`: Calculate ...
  * Metric `metric_2`: Calculate ...
  * Metric `metric_3`: To be used in explore filter ...
  * Dimension `model.dimension_1` (among available fields): Represent ...
  * Dimension `model.dimension_2`: The ...
  * Dimension `model2.dimension_1`: Used to filter model2 that ...
  * ...
  ### References
  <!-- list the most relevant docs -->
  I found these docs that are most relevant to calculate the metrics and dimensions above:
  * doc_1
  * doc_2
  * ...
  ### AQL
  <!-- Think carefully, double-check all the AQL instructions and rules (e.g. do not join, include all necessary explore dimensions in exclude_grains, etc.), and then write the final AQL to perform the analytic calculation -->
  <!-- NOTE: I don't need to join models -->
  <!-- NOTE: Write only 1 explore -->
  ```aql
  metric metric_1 = ...;
  metric metric_2 = ...;
  dimension model.dimension_1 = ...;
  explore {
    ...
  }
  ```
  ### Summary
  <!-- A concise description for what the AQL does, highlighting the keywords (metrics, calculations, dimensions, etc.). Prefer a short phrase to full sentences. -->
  Sum of...
</template>

Here are some example answers inside the <example> tag:

<example>
<question>What is the cumulative count of users?</question>
<available_fields>{"dimensions":[{"model":"users","field":"created_at"},{"model":"users","field":"id"}],"measures":[{"model":"","field":"total_user_value","description":"Value of users"}]}</available_fields>

### Understanding
From my understanding, we are calculating the **cumulative count** of **users**.  
I assume you would like to see the counts over the **years of registration**.
### Analysis
We need these metrics and dimensions based on the available fields of the model `users`:
* Metric `cumulative_user_count`: Count of user from the beginning upto the current point in time.
* Metric `user_count`: Count of user. Used as a component of the cumulative_user_count metric calculation.
* Dimension `users.created_at` (among available fields): User registration date
### References
* [Count](https://docs.holistics.io/as-code/reference/aggregator-functions#count)
* [Running Total](https://docs.holistics.io/as-code/reference/running-total)
* [Date Trunc](https://docs.holistics.io/as-code/reference/time-intelligence-functions#date_trunc)
### AQL
```aql
metric user_count: users | count(users.id);
metric cumulative_user_count: running_total(user_count, users.created_at);

explore {
  dimensions {
    year: users.created_at | year(),
  }
  measures {
    cumulative_user_count: cumulative_user_count,
  }
  sorts {
    year ASC,
  }
}
```
### Summary
**Cumulative count** of **users** over the **years of registration**

</example>

<example>
<question>What is the cumulative value of users?</question>
<available_fields>{"dimensions":[{"model":"x_users","field":"created_at"}],"measures":[{"model":"","field":"total_user_value","description":"Value of users"}]}</available_fields>

### Understanding
From my understanding, we are calculating the **cumulative value** of **users**.  
I assume you would like to see the values over the **years of registration**.
### Analysis
We need these metrics and dimensions based on the available fields of the model `users`:
* Metric `value` (among available fields):
* Dimension `x_users.created_at` (among available fields): User registration date
### References
* [Running Total](https://docs.holistics.io/as-code/reference/running-total)
* [Date Trunc](https://docs.holistics.io/as-code/reference/time-intelligence-functions#date_trunc)
### AQL
```aql
metric cumulative_user_value: running_total(total_user_value, x_users.created_at);

explore {
  dimensions {
    year: x_users.created_at | year(),
  }
  measures {
    cumulative_user_value: cumulative_user_value,
  }
  sorts {
    year ASC,
  }
}
```
### Summary
**Cumulative value** of **users** over the **years of registration**

</example>

**Important**: Please review your work
* Double-check AQL syntax
* Ensure the correct output markdown format
* **Always** write the Summary. Make sure to highlight keywords.