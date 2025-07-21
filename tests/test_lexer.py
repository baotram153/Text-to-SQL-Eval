import pytest
# from unittest.mock import MagicMock, patch
from lexer import Lexer
import sys
from utils.schema import get_schema_from_json

# Mock KEYWORDS for testing
# sys.modules['utils.constants'] = MagicMock()
# import utils.constants
# utils.constants.KEYWORDS = {'select', 'from', 'where', 'as'}

# Mock Schema for testing
class MockSchema:
    def __init__(self, name='test', schema_dict=None):
        self._name = name
        self.schema_dict = schema_dict or {'city': {}, 'country': {}}

@pytest.fixture(scope='function')
def mock_schema():
    schema_name, schema = get_schema_from_json('mocked_data/tables.json')
    return MockSchema(name=schema_name, schema_dict=schema)

def test_tokenize_basic_sql(mock_schema):
    sql = "SELECT name FROM city"
    lexer = Lexer(sql, mock_schema)
    assert lexer.toks == ['select', 'name', 'from', 'city']

def test_tokenize_with_quotes(mock_schema):
    sql = "SELECT name FROM city WHERE name = 'New York'"
    lexer = Lexer(sql, mock_schema)
    assert '"New York"' in lexer.toks

def test_tokenize_with_operators(mock_schema):
    sql = "SELECT age FROM person WHERE age != 30 AND age >= 18"
    lexer = Lexer(sql, mock_schema)
    assert '!=' in lexer.toks
    assert '>=' in lexer.toks

def test_tokenize_with_schema_prefix(mock_schema):
    sql = "SELECT car_retails.employees.firstname FROM car_retails.employees"
    lexer = Lexer(sql, mock_schema)
    assert 'employees.firstname' in lexer.toks
    assert 'employees' in lexer.toks

def test_scan_alias_as_keyword(mock_schema):
    sql = "SELECT name AS n FROM city AS c"
    lexer = Lexer(sql, mock_schema)
    assert lexer._alias_tables['n'] == 'name'
    assert lexer._alias_tables['c'] == 'city'

def test_scan_alias_without_as(mock_schema):
    sql = "SELECT name n FROM city c"
    lexer = Lexer(sql, mock_schema)
    assert lexer._alias_tables['n'] == 'name'
    assert lexer._alias_tables['c'] == 'city'

def test_get_merged_alias_table(mock_schema):
    sql = "SELECT country as ct from offices as o"
    lexer = Lexer(sql, mock_schema)
    merged = lexer.get_merged_alias_table(mock_schema)
    assert merged['offices'] == 'offices'
    assert merged['o'] == 'offices'
    assert merged['ct'] == 'country'

def test_unexpected_quote_raises(mock_schema):
    sql = "SELECT name FROM city WHERE name = 'New York"
    with pytest.raises(AssertionError):
        Lexer(sql, mock_schema)

def test_count(mock_schema):
    sql = "SELECT COUNT(e.employeenumber) FROM car_retails.employees as e"
    lexer = Lexer(sql, mock_schema)
    assert lexer.toks == ['select', 'count', '(', 'e.employeenumber', ')', 'from', 'employees', 'as', 'e']

def test_multiple_aliases(mock_schema):
    sql = "SELECT avg_price FROM (SELECT AVG(p.buyprice) AS avg_price FROM car_retails.products AS p)"
    lexer = Lexer(sql, mock_schema)
    assert lexer.toks == ['select', 'avg_price', 'from', '(', 'select', 'avg', '(', 'p.buyprice', ')', 'as', 'avg_price', 'from', 'products', 'as', 'p', ')']