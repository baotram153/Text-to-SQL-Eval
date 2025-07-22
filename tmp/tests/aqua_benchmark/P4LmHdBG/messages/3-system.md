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

 <document index="3" title="AQL Error Reference" url="https://docs.holistics.io/as-code/reference/error-reference">
  ## WARN-300: Should follow group with select or filter {#ERR-300}

**Description**: This warning occurs when an aggregate function directly follows a `group()` function without using `select()` or `filter()` in between.

While you might expect `table | group(dimension) | aggregate_function()` to return grouped results, this pattern isn't valid in AQL.

**Why This Happens**: Aggregate functions (like `count()`, `sum()`, etc.) return single scalar values, not grouped tables.

To maintain the grouping structure while performing aggregations, you must use `select()` or `filter()` to properly apply the aggregation within the grouped context.

**Solutions**:

1. **Consider if grouping is necessary**: Metrics in AQL are automatically sliced by dimensions introduced from explore/visualize without explicit grouping. You typically only need manual grouping for nested aggregations.

  If you really need nested aggregation, you can write:

  ```jsx title="This works but may trigger the lint warning"
  users | group(users.id) | avg(count(orders.id))
  ```

  ```jsx title="More readable alternative that avoids the warning"
  users | group(users.id) | select(count(orders.id)) | avg()
  ```

2. Use `select()` or `filter()` with your aggregations

  ```jsx title="❌ Incorrect usage"
  // This will error
  users | group(users.id) | count(orders.id)
  ```

  ```jsx title="✅ Correct with select()"
  users | group(users.id) | select(count(orders.id))
  ```

  ```jsx title="✅ Correct with named columns"
  users | group(users.id) | select(order_count: count(orders.id))
  ```

  ```jsx title="✅ Correct with filter()"
  users | group(users.id) | filter(count(orders.id) > 5)
  ```

**Key Takeaway**
Always follow `group()` operations with either `select()` or `filter()` when performing aggregations to maintain the proper grouped table structure.
  </document>

 <document index="4" title="group" url="https://docs.holistics.io/as-code/reference/group">
  ## Description
Provide the grouping context for calculating metrics in subsequent `select()` or `filter()`.

## Syntax

```aql
table | group(column, ...)
```

### Input
- `table`: A Source Table
- `column` (repeatable): Column that is reachable from the Source Table (i.e. the column has a one-to-one or one-to-many relationship with the Source Table)

### Output
A Table with applied grouping
  </document>

 <document index="5" title="AQL Error Reference" url="https://docs.holistics.io/as-code/reference/error-reference">
  ## WARN-300: Should follow group with select or filter {#ERR-300}

**Description**: This warning occurs when an aggregate function directly follows a `group()` function without using `select()` or `filter()` in between.

While you might expect `table | group(dimension) | aggregate_function()` to return grouped results, this pattern isn't valid in AQL.

**Why This Happens**: Aggregate functions (like `count()`, `sum()`, etc.) return single scalar values, not grouped tables.

To maintain the grouping structure while performing aggregations, you must use `select()` or `filter()` to properly apply the aggregation within the grouped context.

**Solutions**:

1. **Consider if grouping is necessary**: Metrics in AQL are automatically sliced by dimensions introduced from explore/visualize without explicit grouping. You typically only need manual grouping for nested aggregations.

  If you really need nested aggregation, you can write:

  ```jsx title="This works but may trigger the lint warning"
  users | group(users.id) | avg(count(orders.id))
  ```

  ```jsx title="More readable alternative that avoids the warning"
  users | group(users.id) | select(count(orders.id)) | avg()
  ```

2. Use `select()` or `filter()` with your aggregations

  ```jsx title="❌ Incorrect usage"
  // This will error
  users | group(users.id) | count(orders.id)
  ```

  ```jsx title="✅ Correct with select()"
  users | group(users.id) | select(count(orders.id))
  ```

  ```jsx title="✅ Correct with named columns"
  users | group(users.id) | select(order_count: count(orders.id))
  ```

  ```jsx title="✅ Correct with filter()"
  users | group(users.id) | filter(count(orders.id) > 5)
  ```

**Key Takeaway**
Always follow `group()` operations with either `select()` or `filter()` when performing aggregations to maintain the proper grouped table structure.
  </document>

 <document index="6" title="select" url="https://docs.holistics.io/as-code/reference/select">
  import SampleCode from '@site/src/components/SampleCode';

### Definition
Run one expression or multiple expression over each row of a table and use the output to return a new table with the same number of row. In AQL, the [select](#) function serves as an intermediate step for subsequent transformations.

**Syntax**
```jsx
select(table, expr1, expr2, ...)
select(table, col_name: expr1, ...)
```

```jsx title="Examples"
select(orders, orders.id, orders.status) // -> Table(orders.id, orders.status)

// with pipe
orders | select(orders.id, orders.status) | select(orders.id) // -> Table(orders.id)

// named column
orders | select(orders.status, formatted_status: concat('Status: ', orders.status))
```

**Input**

- `table`: A model reference or the returned table from a previous expression.
- `expr` (**repeatable**): An expression to evaluate for each row of `table`.
:::caution
You need to name the column in the output table (e.g. `formatted_status: concat('Status: ', orders.status)`). Only expression that has clear fully-qualified column name (e.g. `orders.id`) can be used directly and reference as-is in the output table.
:::

**Output**

A table with the same number of rows as the input table, but with only the specified columns. E.g. `select(orders, orders.id, formatted_status: concat('Status: ', orders.status)` will return a table with 2 columns: `orders.id` and `formatted_status`.

| orders.status | formatted_status |
|---------------|------------------|
| pending       | Status: pending  |
| cancelled     | Status: cancelled|
| pending       | Status: pending  |

### Sample Usages

import { example1 } from './select.js';

<SampleCode
  title="List all order items and their value"
  rawResult={example1}
/>

import { example2 } from './select.js';

<SampleCode
  title="Use select to create an intermediate table for a metric"
  rawResult={example2}
/>
  </document>

 <document index="7" title="Aggregate Functions (Aggregators)" url="https://docs.holistics.io/as-code/reference/aggregator-functions">
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

 <document index="8" title="window_count" url="https://docs.holistics.io/as-code/reference/window_count">
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

 <document index="9" title="where vs. filter" url="https://docs.holistics.io/as-code/reference/where-vs-filter">
  :::tip Knowledge Checkpoint
This documentation assumes that you are familiar with the following functions:
- [where](/as-code/reference/where)
- [filter](/as-code/reference/filter)
:::

In AQL, we have the `where()` and the `filter()` functions that perform roughly the same function (apply a filtering condition onto an object), so you may wonder which one to use in a particular situation. In this document, we will explain when and where you should use which function.

### Quick comparison

A quick rule-of-thumb to follow when deciding between `where()` and `filter()`:

| Function | <div width="200">Target</div> | Valid filtering condition | When to use |
| :------- | :--------------------- | :------------------------ | :---------- |
| where() | Measure | <ul class=""><li><code>dimension operator value</code>. E.g. <code>orders.status == 'delivered'</code>, <code>orders.created_at matches @(last 7 days)</code></li><li><code>dimension in [value1, value2, ...]</code>. E.g. <code>orders.status in ['delivered', 'cancelled']</code></li><li><code>dimension in table</code>. E.g. <code>orders.status in unique(orders.status)</code></li><li><code>dimension operator measure</code>. E.g. <code>users.age &gt; avg(users.age)</code></li></ul> | Apply filters to a Measure |
| filter() | Table | Any expression that returns [truefalse](/as-code/reference/type-truefalse) and is valid in the context of the table row | Filter a Table


### Examples

Suppose that you have an Ecommerce dataset with the following models:

```jsx
Model orders {
	dimension id {}
	dimension status {}
	dimension country {}
	dimension user_id {}
	dimension value {}
}
```

In the examples below, we will demonstrate the difference on how `where()` and `filter()` are used.

#### Only `where()` can be used

Suppose you have defined the `total_orders` measure inside `orders` model:

```jsx
Model orders {
	...

	measure total_orders {
		definition: @aql count(orders.id)
	}
}
```

Now you want to calculate **“the total orders which are delivered.”** You can use `where()` to apply filter to the measure:

```jsx
orders.total_orders | where(orders.status == 'delivered') // valid expression

// This will error
orders.total_orders | filter(orders.status == 'delivered') // invalid expression
```

By definition, `filter()` cannot be used here.

#### Only `filter()` can be used

`filter()` can be used when you want to filter by arbitrary expression that haven't been defined as a dimension yet. For example, you want to know which country has at least 100,000 users who have placed at least 1 order:

```jsx
orders
| group(orders.country)
| select(orders.country, users_count: count_distinct(orders.user_id))
// highlight-next-line
| filter(users_count >= 100000) // where here will be invalid
```

In this case, `where()` cannot be used in place of `filter()`, because by definition, `where()` have to filter on an existing dimension of `orders`, while the field `users_count` is an aggregation that has not been defined and calculated before.
  </document>

 <document index="10" title="window_avg" url="https://docs.holistics.io/as-code/reference/window_avg">
  :::tip Knowledge Checkpoint
Readings that will help you understand this documentation better:
- [Window Functions Overview](/as-code/reference/window-function)
:::

## Definition
A window aggregation function that returns the average of rows in a range relative to the current row.

**Syntax**
```jsx
window_avg(agg_expr)
window_avg(agg_expr, order: order_expr, ...)
window_avg(agg_expr, range, order: order_expr, ...)
window_avg(agg_expr, range, order: order_expr, ..., reset: partition_expr, ...)
window_avg(agg_expr, range, order: order_expr, ..., partition: partition_expr, ...)
```

```jsx title="Examples"
window_avg(count(users.id))
window_avg(count(users.id), order: count(users.id) | desc())
window_avg(count(users.id), -2..2, order: users.created_at | month())
window_avg(count(users.id), order: users.created_at | month(), reset: users.gender)
```


**Input**
- `agg_expr` (**required**): An aggregation expression to be averaged.
- `range` (**optional**): A range of rows to include in the average. Negative values indicate rows before the current row, and positive values indicate rows after the current row, while 0 indicates the current row. If the beginning or end of the range is not specified, the range will include all rows from the beginning or end of the table. By default, if the range is not specified:
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

The average of the current row and the rows within the specified range.

## Sample Usages

import SampleCode from '@site/src/components/SampleCode'

import { example1 } from './window_avg.js'

<SampleCode title="Avg of Count" rawResult={example1} />

The most common use case for `window_avg` is to calculate the average of a column. In this example, we calculate the average of the count of users.

---

import { example2 } from './window_avg.js'

<SampleCode title="Avg of Count with Moving Average" rawResult={example2} />

We can also use it to calculate the moving average of a column. In this example, we calculate the moving average of the count of users, ordered by the year they were created. Notice that we are using the `range` parameter to specify the range of rows to include in the average. In this case, we are calculating the average of the current row and the two rows before and after it (i.e. a total of 5 rows) with the range `-2..2`.
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