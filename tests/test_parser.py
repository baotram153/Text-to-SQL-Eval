import pytest
from refactor.parser import Parser
from refactor.nodes import *
from lexer import Lexer
from utils.schema import Schema, get_schema_from_json
from utils.constants import *
import logging

logger = logging.getLogger(__name__)


@pytest.fixture
def mock_schema():
    schema_name, schema = get_schema_from_json('mocked_data/tables.json')
    return Schema(schema, schema_name)

########################### TEST SELECT ##############################
def test_multiple_cols_select(mock_schema):
    sql = "SELECT country, COUNT(customerNumber) AS customer_count FROM customers GROUP BY country"
    lexer = Lexer(sql, mock_schema)
    parser = Parser(lexer, mock_schema)
    result_sql = parser.parse()
    print(f"Parsed SQL: {result_sql}")
    assert isinstance(result_sql.select, Select)

########################### TEST FROM ###############################
def test_normal_from(mock_schema):
    sql = "SELECT firstname FROM employees"
    lexer = Lexer(sql, mock_schema)
    parser = Parser(lexer, mock_schema)
    result_sql = parser.parse()
    print(f"Parsed SQL: {result_sql}")
    assert isinstance(result_sql.from_, From)

def test_from_with_alias(mock_schema):
    sql = "SELECT firstname FROM employees AS e"
    lexer = Lexer(sql, mock_schema)
    parser = Parser(lexer, mock_schema)
    result_sql = parser.parse()
    print(f"Parsed SQL: {result_sql}")
    assert isinstance(result_sql.from_, From)

def test_from_with_join(mock_schema):
    sql = "SELECT firstname FROM employees JOIN offices ON employees.officecode = offices.officecode"
    lexer = Lexer(sql, mock_schema)
    parser = Parser(lexer, mock_schema)
    result_sql = parser.parse()
    print(f"Parsed SQL: {result_sql}")
    assert isinstance(result_sql.from_, From)

def test_inner_join(mock_schema):
    sql = "SELECT priceEach FROM orders INNER JOIN orderdetails ON orders.ordernumber = orderdetails.ordernumber"
    lexer = Lexer(sql, mock_schema)
    parser = Parser(lexer, mock_schema)
    result_sql = parser.parse()
    assert isinstance(result_sql.select, Select)

def test_decartes_join(mock_schema):
    sql = "SELECT * from employees, offices"
    lexer = Lexer(sql, mock_schema)
    parser = Parser(lexer, mock_schema)
    result_sql = parser.parse()
    print(f"Parsed SQL: {result_sql}")
    assert isinstance(result_sql.from_, From)

# def test_parse_where_clause(mock_schema):
#     sql = """
# SELECT
#     c.customerName,
#     pay_summary.total_paid,
#     pay_summary.last_payment_date
# FROM customers AS c
# JOIN (
#         SELECT
#             customerNumber,
#             SUM(amount)      AS total_paid,
#             MAX(paymentDate) AS last_payment_date
#         FROM payments
#         GROUP BY customerNumber
#      ) AS pay_summary
#          (customerNumber,
#           total_paid,
#           last_payment_date)
#   ON c.customerNumber = pay_summary.customerNumber
# ORDER BY pay_summary.total_paid DESC;
# """
#     lexer = Lexer(sql, mock_schema)
#     parser = Parser(lexer, mock_schema)
#     result = parser.parse()
#     assert isinstance(result.where, list)

############################ TEST CONDITIONS #######################
def test_multiple_conditions(mock_schema):
    sql = "SELECT firstname FROM employees WHERE firstname = 'Alex' AND employeenumber < 50000"
    lexer = Lexer(sql, mock_schema)
    parser = Parser(lexer, mock_schema)
    result = parser.parse()
    print(f"Parsed SQL: {result}")
    assert isinstance(result.where.conds, list)
    assert len(result.where.conds) == 3     # 2 conditions + 1 AND

########################### TEST ALIASES ###########################
def test_alias(mock_schema):
    sql = "SELECT e.firstname FROM employees as e"
    lexer = Lexer(sql, mock_schema)
    parser = Parser(lexer, mock_schema)
    result = parser.parse()
    assert result.select.col_units[0].col_name == 'employees.firstname'
    assert result.select.col_units[0].col_id == '__employees.firstname__'

############################ TEST DATASET ###########################
def test_dataset_1(mock_schema):
    sql = "SELECT DISTINCT T1.productVendor, T1.MSRP - T1.buyPrice FROM products AS T1 INNER JOIN orderdetails AS T2 ON T1.productCode = T2.productCode GROUP BY T1.productVendor, T1.MSRP, T1.buyPrice ORDER BY SUM(T2.quantityOrdered) DESC LIMIT 1"
    lexer = Lexer(sql, mock_schema)
    parser = Parser(lexer, mock_schema)
    result = parser.parse()
    print(f"Parsed SQL: {result}")
    assert isinstance(result.from_.table_unit, TableRef)
    expected = Agg(agg_id=AGG_OPS.index('sum'), col_unit=ColRef(col_name='orderdetails.quantityordered', col_id='__orderdetails.quantityordered__'))
    assert str(result.order_by.order_cols[0][0]) == str(expected)

def test_dataset_2(mock_schema):
    sql = "SELECT e.firstName AS first_name, e.lastName AS last_name, SUM(p.amount) AS total_payment FROM payments p LEFT JOIN customers c ON p.customerNumber = c.customerNumber LEFT JOIN employees e ON c.salesRepEmployeeNumber = e.employeeNumber WHERE p.paymentDate >= '2004-01-01' AND p.paymentDate < '2005-01-01' GROUP BY e.firstName, e.lastName ORDER BY total_payment DESC"
    lexer = Lexer(sql, mock_schema)
    parser = Parser(lexer, mock_schema)
    result = parser.parse()
    print(f"Parsed SQL: {result}")
    assert isinstance(result.from_.table_unit, TableRef)

def test_dataset_3(mock_schema):
    sql = """
    SELECT SUM(od.quantityOrdered * od.priceEach) AS total_product_price
    FROM car_retails.orderdetails od
    JOIN car_retails.orders o ON od.orderNumber = o.orderNumber
    JOIN car_retails.customers c ON o.customerNumber = c.customerNumber
    WHERE c.customerName = 'Rovelli Gifts Distributors Ltd.'
        AND o.shippedDate >= '2003-01-01'
        AND o.shippedDate <= '2003-12-31'
    """
    lexer = Lexer(sql, mock_schema)
    parser = Parser(lexer, mock_schema)
    result = parser.parse()
    print(f"Parsed SQL: {result}")
    assert isinstance(result.from_.table_unit, TableRef)

def test_dataset_4(mock_schema):
    sql = """
    SELECT COUNT(*) AS employee_count FROM car_retails.employees
    LEFT JOIN car_retails.offices ON car_retails.employees.officeCode = car_retails.offices.officeCode 
    WHERE city = 'Sydney'
    """
    lexer = Lexer(sql, mock_schema)
    parser = Parser(lexer, mock_schema)
    result = parser.parse()
    print(f"Parsed SQL: {result}")
    assert isinstance(result.from_.table_unit, TableRef)

def test_dataset_5(mock_schema):
    sql = """
    SELECT
    "car_retails_products"."productvendor" AS "crp_p_0aa5b5",
    COUNT("car_retails_orderdetails"."ordernumber") AS "order_count",
    SUM(("car_retails_orderdetails"."quantityordered" * "car_retails_orderdetails"."priceeach")) AS "total_earnings"
    FROM
    "car_retails"."orderdetails" "car_retails_orderdetails"
    LEFT JOIN "car_retails"."products" "car_retails_products" ON "car_retails_orderdetails"."productcode" = "car_retails_products"."productcode"
    GROUP BY
    1
    ORDER BY
    2 DESC,
    1 ASC
    LIMIT 1
    """
    lexer = Lexer(sql, mock_schema)
    parser = Parser(lexer, mock_schema)
    result = parser.parse()
    print(f"Parsed SQL: {result}")
    assert isinstance(result.from_.table_unit, TableRef)

def test_dataset_6(mock_schema):
    sql = """
    SELECT T1.employeeNumber FROM employees AS T1 INNER JOIN offices AS T2 ON T1.officeCode = T2.officeCode WHERE T1.reportsTo = 1143 AND T2.city = 'NYC'
    """
    lexer = Lexer(sql, mock_schema)
    parser = Parser(lexer, mock_schema)
    result = parser.parse()
    print(f"Parsed SQL: {result}")
    assert isinstance(result.from_.table_unit, TableRef)