from sqlglot import parse_one

sql = 'SELECT avg(profit + revenue) AS total FROM sales'

parsed = parse_one(sql)
print(repr(parsed))