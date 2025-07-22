from lexer import Lexer
from utils.schema import Schema
from typing import Dict, List, Union
from utils.constants import *
from .nodes import *
import logging

logger = logging.getLogger(__name__)

class Parser:
    def __init__(
        self,
        lexer: Lexer,
        schema: Schema
    ):
        self._lexer: Lexer = lexer
        self._schema: Schema = schema
        self._alias_tables: Dict[str, str] = self._lexer.get_merged_alias_table(self._schema)   # TODO: Can we construct this table on the go? -> reduce 1 pass through the sql string
        self._toks: List[str] = self._lexer.toks
        self._pos: int = 0
        self._sql: Sql

    def parse(self):
        """Parse the SQL query from the lexer tokens."""
        sql = self._parse_sql()
        self._expect_end()
        return sql

    # HELPER METHODS ======================================================
    def _peek(self, n: int = 0):
        """Peek at the next token without consuming it."""
        if self._pos + n < len(self._toks):
            return self._toks[self._pos + n]
        return None

    def _pop(self):
        """Pop the next token and advance the position."""
        if self._pos < len(self._toks):
            tok = self._toks[self._pos]
            self._advance()
            return tok
        raise ValueError("No more tokens to pop.")
    
    def _advance(self, n: int = 1):
        """Advance the position by n tokens."""
        self._pos += n
        if self._pos > len(self._toks):
            raise ValueError("Advanced beyond the end of tokens.")
        
    def _jump(self, idx: int):
        """Jump to a specific index in the tokens."""
        if 0 <= idx <= len(self._toks):
            self._pos = idx
        else:
            raise ValueError(f"Index {idx} is out of bounds for tokens of length {len(self._toks)}.")
        
    def _consume(self, expected_token: str):
        """Consume the next token if it matches the expected token."""
        if self._peek() == expected_token:
            self._advance()
        else:
            raise ValueError(f"Expected token '{expected_token}', but found '{self._peek()}'.")
        
    def _find(self, start_idx: int, expected_token: str):
        """Find the index of the expected token starting from start_idx."""
        for idx in range(start_idx, len(self._toks)):
            if self._toks[idx] == expected_token:
                return idx
        return None
               
    def _expect_end(self):
        """Ensure that the parser has reached the end of the tokens."""
        if self._pos != len(self._toks):
            raise ValueError("Trailing tokens after SQL query: {}".format(self._toks[self._pos:]))

    # MAIN METHODS ======================================================
    def _parse_sql(self):
        self._sql = Sql()
        isBlock = False
        select_idx = self._pos  # save the position of 'select'

        if self._peek() == '(':  # handle block
            isBlock = True
            self._advance()

        # parse 'from' first to get default_tables
        from_idx = self._find(self._pos, 'from')
        assert from_idx is not None, f"'from' not found {self._toks}"
        self._jump(from_idx)
        from_, default_tables = self.parse_from()
        self._sql.from_ = from_
        after_from_pos = self._pos  # save position after 'from'

        # jump back to 'select' and parse it using default_tables
        self._jump(select_idx)
        # breakpoint()
        select = self.parse_select(default_tables)
        self._sql.select = select

        # jump forward to after 'from' to continue parsing
        self._jump(after_from_pos)

        self._sql.where = self.parse_where(default_tables)
        self._sql.group_by = self.parse_group_by(default_tables)
        self._sql.having = self.parse_having(default_tables)
        self._sql.order_by = self.parse_order_by(default_tables)
        self._sql.limit = self.parse_limit()

        # skip semicolon if present
        while self._peek() == ';':
            self._advance()

        # if this is a block, we should consume the closing parenthesis
        if isBlock:
            self._consume(')')

        if self._peek() in SQL_OPS:
            sql_op = self._pop()
            IUE_sql = self.parse_sql()
            setattr(self._sql, sql_op, IUE_sql)
        return self._sql

    def parse_from(self) -> From:
        """
        Assume in the from clause, all table units are combined with join
        """
        from_idx = self._find(self._pos, 'from')
        assert from_idx != None, "'from' not found"
        self._jump(from_idx + 1)  # skip 'from'

        default_tables = []
        joins = []
        table_unit = None

        isBlock = False
        if self._peek() == '(':
            isBlock = True
            self._advance()  # skip '('

        if self._peek() == 'select':
            sql = self._parse_sql()
            table_unit = sql
        else:
            table_unit, table_name = self.parse_table_ref()
            default_tables.append(table_name)

        while True:
            if self._peek() in ('join', 'inner', 'outer', 'natural', 'left', 'right', ','):
                joins.append(self.parse_join(default_tables))
            else:
                break

        if isBlock:
            self._consume(')')

        return From(table_unit, joins), default_tables

    def parse_join(self, default_tables: List[str]) -> Join:
        # breakpoint()
        assert self._peek() in ('join', 'inner', 'outer', 'natural', 'left',  'right', ','), "Expected 'join' or ',' keyword"
        join_type = self._pop()
        join_type = join_type if join_type != ',' else 'decartes'
        if self._peek() == 'join': self._advance()  # skip 'join'

        is_block = False
        if self._peek() == '(':
            is_block = True
            self._advance()

        if self._peek() == 'select':
            sql = self._parse_sql()
            table_unit = sql
        else:
            table_unit, table_name = self.parse_table_ref()
            default_tables.append(table_name)

        conds = []
        if self._peek() == 'on':
            self._advance()
            conds = self.parse_condition(default_tables)

        if is_block:
            self._consume(')')

        return Join(join_type=join_type, table_unit=table_unit, on_condition=conds)


    def parse_select(self, default_tables):
        logger.debug(f"Parsing select statement, current position: {self._pos}, next token: {self._peek()}")
        logger.debug(f"Clause keywords: {CLAUSE_KEYWORDS}")
        select_tok = self._pop()
        assert select_tok == 'select', "'select' not found"

        is_distinct = False
        if self._peek() == 'distinct':
            self._advance()
            is_distinct = True

        col_units = []
        while True:
            col_unit = self.parse_col_unit(default_tables)
            col_units.append(col_unit)
            if self._peek() == ',':
                self._advance()  # skip ','
            elif self._peek() == 'as':  # skip 'as id ,'
                if self._peek(2) == ',':
                    self._advance(3)
                else:
                    self._advance(2)
            else:
                break
            if self._peek() in CLAUSE_KEYWORDS or self._peek() in (")", ";", None):
                break

        return Select(is_distinct=is_distinct, col_units=col_units)
    
    def parse_table_ref(self):
        """Return table id, table real name, advance the position."""
        table_name = self._pop()

        # get table real name
        actual_table_name = self._alias_tables.get(table_name, table_name)
        
        # advance the posion if needed
        if self._peek() == 'as':
            self._advance(n=2)  # skip 'as' and the alias token
        try:
            self._schema.idMap[actual_table_name]
        except:
            raise Exception(f"Table {actual_table_name} not found in idMap, Schema: {self._schema.idMap}")
        return TableRef(self._schema.idMap[actual_table_name], actual_table_name), table_name

    def parse_condition(self, default_tables) -> List[Cond]:
        '''
            :returns conds: list of conditions in the form:
            [condition1, 'and', condition2, 'or', condition3, ...]
            where condition is a tuple of the form: (not_op, op_id, val_unit, val1, val2)
        '''
        logger.debug(f"In parse_condition, current position: {self._pos}, next token: {self._peek()}")
        conds = []
        # breakpoint()
        while self._pos < len(self._toks):
            col_unit = self.parse_col_unit(default_tables)
            not_op = False
            if self._peek() == 'not':
                not_op = True
                self._advance()
            
            op_tok = self._peek()
            assert op_tok in WHERE_OPS, f"Error condition: pos: {self._pos}, tok: {op_tok}"
            op_id = WHERE_OPS.index(op_tok)
            self._advance()

            # breakpoint()
            print(f"In parse_condition, current position: {self._pos}, next token: {self._peek()}")
            val1 = val2 = None
            if op_id == WHERE_OPS.index('between'):
                val1 = self.parse_value(default_tables)
                assert self._peek() == 'and', f"Expected 'and' after 'between', got {self._peek()}"
                self._advance()
                val2 = self.parse_value(default_tables)
            else:
                val1 = self.parse_value(default_tables)
                val2 = None
            conds.append(Cond(not_op, op_id, col_unit, val1, val2))     # append the condition tuple

            # check for clause/join/ending
            if self._peek() in CLAUSE_KEYWORDS+JOIN_KEYWORDS or self._peek() in (")", ";"):
                break

            # check for AND/OR
            if self._peek() in COND_OPS:
                conds.append(self._pop())   # append the AND/OR operator (connector)
        return conds
    
    def parse_col_unit(self, default_tables=None) -> ColUnit:
        """
        Parse a value unit. Which can be a column unit, or an expression with unit operations.

        :param default_tables: List of default tables to resolve column names.
        :returns: (unit_op, col_unit1, col_unit2), if unit_op is 'none', the tuple would be (0, col_unit1, None).
        """
        print(f"In parse_col_unit, current position: {self._pos}, next token: {self._peek()}")
        isDistinct = False
        agg = None
        col_unit1, col_unit2, unit_op = None, None, UNIT_OPS.index('none')

        isBlock = False
        if self._peek() == '(':
            isBlock = True
            self._advance()
        
        if self._peek() == 'distinct':
            isDistinct = True
            self._advance()

        if self._peek() in AGG_OPS:
            agg = self.parse_agg(default_tables)

        else:
            col_unit1 = self.parse_col_ref(default_tables)

        if self._peek() in UNIT_OPS:
            unit_op = UNIT_OPS.index(self._pop())
            col_unit2 = self.parse_col_unit(default_tables)


        if isBlock:
            self._consume(')')
        if unit_op != UNIT_OPS.index('none'):
            if agg is not None:
                return Agg(agg[0], col_unit1, isDistinct)
            return Arith(unit_op, col_unit1, col_unit2, isDistinct)
        else:
            if agg:
                return agg
            return col_unit1

    def parse_col_ref(self, default_tables):
        """
            :returns column id , column name
        """
        # breakpoint()
        print(f"In parse_col_ref, current position: {self._pos}, next token: {self._peek()}")
        isBlock = False
        if self._peek() == '(':
            isBlock = True
            self._advance()

        col_tok = self._peek()
        if col_tok == "*":
            self._advance()
            return ColRef(self._schema.idMap[col_tok],col_tok)

        if '.' in col_tok:  # if token is a composite - e.g. table_a.col_b
            alias, col = col_tok.split('.')
            key = self._alias_tables[alias] + "." + col
            self._advance()
            return ColRef(self._schema.idMap[key], key)

        assert default_tables is not None and len(default_tables) > 0, "Default tables should not be None or empty"

        for alias in default_tables:
            table = self._alias_tables[alias]
            if col_tok in self._schema.schema_dict[table]:   # find in each table's columns
                key = table + "." + col_tok
                self._advance()
                return ColRef(self._schema.idMap[key], key)

        # aggregation, arithmetic ops
        try:
            agg_op = self._alias_tables[col_tok]
            if agg_op in AGG_OPS:
                self._advance()
                return ColRef(agg_op, self._schema.idMap[agg_op])
        except:
            assert False, "Error col: {}".format(col_tok)
        
        if isBlock:
            self._consume(')')

    def parse_agg(self, default_tables):
        """
        :returns Agg(agg_id, col_unit)
        """
        agg_id = AGG_OPS.index(self._pop())
        col_unit = self.parse_col_unit(default_tables)
        return Agg(agg_id, col_unit)

    def parse_value(self, default_tables):
        value_tok = self._peek()
        logger.debug(f"Current position: {self._pos}, next token: {value_tok}")
        # case value is a literal string
        if (value_tok.startswith('"') and value_tok.endswith('"')) or (value_tok.startswith("'") and value_tok.endswith("'")):
            val = self._pop()
            return ValueUnit(type="string", value=val)
        # case value is a number
        try:
            val = float(self._peek())
            self._advance()
            return ValueUnit(type="number", value=val)
        except (ValueError, TypeError):
            # case value is a column unit or expression
            val = self.parse_col_unit(default_tables)
            return ValueUnit(type='col', value=val)

    def parse_where(self, default_tables):
        """
        :returns: a list of conditions
        """
        if self._peek() != 'where':
            return Where([])
        self._advance()  # skip 'where'
        conds = self.parse_condition(default_tables)
        return Where(conds)

    def parse_group_by(self, default_tables):
        """
        :returns: a tuple (col_units, column_group_units), where one is always empty.
        """
        if self._peek() != 'group':
            return GroupBy([])
        self._advance(2)  # skip 'group by'
        col_units = []
        while True:
            try:
                next_tok = int(self._peek())
                self._advance()
                col_unit = self._sql.select.col_units[next_tok]
                col_units.append(col_unit)
            except (ValueError, TypeError):
                col_unit = self.parse_col_unit(default_tables)
                col_units.append(col_unit)
            if self._peek() == ',':
                self._advance()  # skip ','
            else:
                break
            if self._peek() in CLAUSE_KEYWORDS or self._peek() in (")", ";", None):
                break
        # only one of col_units or column_group_units should be non-empty
        return GroupBy(col_units)

    def parse_having(self, default_tables):
        """
        :returns: a list of conditions in the HAVING clause.
        """
        if self._peek() != 'having':
            return Having([])
        self._advance()  # skip 'having'
        conds = self.parse_condition(default_tables)
        return Having(conds)

    def parse_order_by(self, default_tables):
        """
        Returns: a tuple (order_type, val_units) where order_type is 'asc' or 'desc',
        and val_units is a list of value units to order by.
        """
        print(f"In parse_order_by, current position: {self._pos}, next token: {self._peek()}")
        order_cols = []

        if self._peek() != 'order':
            return OrderBy([])
        self._advance(2) # skip 'order by'

        while True:
            # breakpoint()
            # check if the next token is a number
            try:
                next_tok = int(self._peek())
                self._advance()
                col_unit = self._sql.select.col_units[next_tok]
                if self._peek() in ORDER_OPS:
                    order_cols.append((col_unit, self._pop()))
            except ValueError:
                col_unit = self.parse_col_unit(default_tables)
                if self._peek() in ORDER_OPS:
                    order_cols.append((col_unit, self._pop()))
                # breakpoint()
            if self._peek() == ',':
                self._advance()  # skip ','
            else:
                break
            if self._peek() in CLAUSE_KEYWORDS or self._peek() in (")", ";", None):
                break
        return OrderBy(order_cols)

    def parse_limit(self):
        """
        :returns: an integer limit value if 'limit' is present, otherwise None.
        """
        if self._peek() != 'limit':
            return None
        self._advance()  # skip 'limit'
        limit_val = self._pop()
        try:
            return int(limit_val)
        except ValueError:
            raise ValueError(f"Invalid LIMIT value: {limit_val}")