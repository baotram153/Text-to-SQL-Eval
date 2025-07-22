import pytest
from refactor.parser import Parser
from refactor.nodes import *
from lexer import Lexer
from utils.schema import Schema, get_schema_from_json


@pytest.fixture
def mock_schema():
    schema_name, schema = get_schema_from_json('mocked_data/tables.json')
    return Schema(schema, schema_name)

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
    sql = "SELECT priceforeach FROM orders INNER JOIN orderdetails ON orders.ordernumber = orderdetails.ordernumber"
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

def test_parse_where_clause(mock_schema):
    sql = """
SELECT
    c.customerName,
    pay_summary.total_paid,
    pay_summary.last_payment_date
FROM customers AS c
JOIN (
        SELECT
            customerNumber,
            SUM(amount)      AS total_paid,
            MAX(paymentDate) AS last_payment_date
        FROM payments
        GROUP BY customerNumber
     ) AS pay_summary
         (customerNumber,
          total_paid,
          last_payment_date)
  ON c.customerNumber = pay_summary.customerNumber
ORDER BY pay_summary.total_paid DESC;
"""
    lexer = Lexer(sql, mock_schema)
    parser = Parser(lexer, mock_schema)
    result = parser.parse()
    assert isinstance(result.where, list)

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