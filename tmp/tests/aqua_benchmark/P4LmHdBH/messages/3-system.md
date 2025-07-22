You have found these documents that are useful to perform the user's analytic calculation:
<documents>

 <document index="1" title="window_sum" url="https://docs.holistics.io/as-code/reference/window_sum">
  ## Definition
A window aggregation function that returns the sum of rows in a range relative to the current row.

**Syntax**
```jsx
window_sum(agg_expr)
window_sum(agg_expr, order: order_expr, ...)
window_sum(agg_expr, range, order: order_expr, ...)
window_sum(agg_expr, range, order: order_expr, ..., reset: partition_expr, ...)
window_sum(agg_expr, range, order: order_expr, ..., partition: partition_expr, ...)
```

```jsx title="Examples"
window_sum(count(users.id))
window_sum(count(users.id), order: count(users.id) | desc())
window_sum(count(users.id), -2..2, order: users.created_at | month())
window_sum(count(users.id), order: users.created_at | month(), reset: users.gender)
```


**Input**
- `agg_expr` (**required**): An aggregation expression to be summed.
- `range` (**optional**): A range of rows to include in the sum. Negative values indicate rows before the current row, and positive values indicate rows after the current row, while 0 indicates the current row. If the beginning or end of the range is not specified, the range will include all rows from the beginning or end of the table. By default, if the range is not specified:
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

The sum of the current row and the rows within the specified range.

## Sample Usages {#sample-usages}

import SampleCode from '@site/src/components/SampleCode'

import { example1 } from './window_sum.js'

<SampleCode title="Running Sum of Count over Order Status" rawResult={example1} />

Notice that it automatically resets the sum when the gender changes. This is because we only specify `order` and thus `reset` defaults to `gender`. If you want it to not reset, you can order by both `gender` and `status`.

import { example2 } from './window_sum.js'

<SampleCode title="Running Sum of Count over Gender and Order Status" rawResult={example2} />

By default, the range is `..0` (from the first row to the current row). Thus if we want to sum all rows, we can use `..` for the range. And since we are not using relative range, we can omit the `order:` parameter.

import { example3 } from './window_sum.js'

<SampleCode title="Total Count of Users with percentage" rawResult={example3} />
  </document>

 <document index="2" title="sum" url="https://docs.holistics.io/as-code/reference/aggregator-functions#sum">
  ## Description

Sums the values in a Number column expression, not including NULL values.

## Syntax

```aql
table | sum(column)
```

### Input
* `table`: Source Table
* `column`: A **number** column expression on the given table

### Output
`Scalar(number)`

### Examples
```aql
products | sum(products.price)
order_items | sum(order_items.quantity * products.price)
```
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