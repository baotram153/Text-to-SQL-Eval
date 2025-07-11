from lexer import Lexer
from utils.schema import Schema
from typing import Dict, List, Union
from utils.constants import *

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
        self._sql = {}
        
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
        isBlock = False  # indicate whether this is a block of sql/sub-sql
        select_idx = self._pos  # Save the position of 'select'

        self._sql = {}
        if self._peek() == '(':  # handle block
            isBlock = True
            self._advance()

        # Parse 'from' first to get default_tables
        from_idx = self._find(self._pos, 'from')
        assert from_idx is not None, f"'from' not found {self._toks}"
        self._jump(from_idx)
        table_units, conds, default_tables = self.parse_from()
        self._sql['from'] = {'table_units': table_units, 'conds': conds}
        after_from_pos = self._pos  # Save position after 'from'

        # Jump back to 'select' and parse it using default_tables
        self._jump(select_idx)
        _, select_col_units = self.parse_select(default_tables)
        self._sql['select'] = select_col_units

        # Jump forward to after 'from' to continue parsing
        self._jump(after_from_pos)

        self._sql['where'] = self.parse_where(default_tables)
        self._sql['groupBy'] = self.parse_group_by(default_tables)
        self._sql['having'] = self.parse_having(default_tables)
        self._sql['orderBy'] = self.parse_order_by(default_tables)
        self._sql['limit'] = self.parse_limit()

        # skip semicolon if present
        while self._peek() == ';':
            self._advance()
            
        # if this is a block, we should consume the closing parenthesis
        if isBlock:
            self._consume(')')

        for op in SQL_OPS:
            self._sql[op] = None
        if self._peek() in SQL_OPS:
            sql_op = self._pop()
            IUE_sql = self.parse_sql()
            self._sql[sql_op] = IUE_sql
        return self._sql
    
    def parse_from(self):
        """
        Assume in the from clause, all table units are combined with join
        """
        from_idx = self._find(self._pos, 'from')
        assert from_idx != None, "'from' not found"
        self._jump(from_idx + 1)  # skip 'from'
        
        default_tables = []
        table_units = []
        conds = []

        while self._pos < len(self._toks):
            isBlock = False
            if self._peek() == '(':
                isBlock = True
                self._advance()  # skip '('

            if self._peek() == 'select':
                sql = self._parse_sql()
                table_units.append((TABLE_TYPE['sql'], sql))
            else:
                if self._peek() == 'join':
                    self._advance()  # skip join
                table_unit, table_name = self.parse_table_unit()
                table_units.append((TABLE_TYPE['table_unit'], table_unit))
                default_tables.append(table_name)
                
            if self._peek() == "on":
                self._advance()  # skip on
                this_conds = self.parse_condition(default_tables)
                if len(conds) > 0:
                    conds.append('and')
                conds.extend(this_conds)

            if isBlock:
                self._consume(')')
                
            if self._peek() in CLAUSE_KEYWORDS or self._peek() in (")", ";"):
                break

        return table_units, conds, default_tables
    
    def parse_select(self, default_tables):
        select_tok = self._pop()
        assert select_tok == 'select', "'select' not found"

        isDistinct = False
        if self._peek() == 'distinct':
            self._advance()
            isDistinct = True

        val_units = []
        while True:
            print(f"In select: {self._peek()}")
            agg_id = AGG_OPS.index("none")
            if self._peek() in AGG_OPS:
                agg_id = AGG_OPS.index(self._pop())
            val_unit = self.parse_val_unit(default_tables)
            val_units.append((agg_id, val_unit))
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

        return None, (isDistinct, val_units)
    
    def parse_table_unit(self):
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
        return self._schema.idMap[actual_table_name], actual_table_name

    def parse_condition(self, default_tables):
        '''
            :returns conds: list of conditions in the form:
            [condition1, 'and', condition2, 'or', condition3, ...]
            where condition is a tuple of the form: (not_op, op_id, val_unit, val1, val2)
        '''
        conds = []

        while self._pos < len(self._toks):
            val_unit = self.parse_val_unit(default_tables)
            not_op = False
            if self._peek() == 'not':
                not_op = True
                self._advance()

            op_tok = self._peek()
            assert op_tok in WHERE_OPS, f"Error condition: pos: {self._pos}, tok: {op_tok}"
            op_id = WHERE_OPS.index(op_tok)
            self._advance()
            
            val1 = val2 = None
            if op_id == WHERE_OPS.index('between'):
                val1 = self.parse_value(default_tables)
                assert self._peek() == 'and', f"Expected 'and' after 'between', got {self._peek()}"
                self._advance()
                val2 = self.parse_value(default_tables)
            else:
                val1 = self.parse_value(default_tables)
                val2 = None
            conds.append((not_op, op_id, val_unit, val1, val2))     # append the condition tuple

            # check for clause/join/ending
            if self._peek() in CLAUSE_KEYWORDS or self._peek() in (")", ";") or self._peek() in JOIN_KEYWORDS:
                break
            
            # check for AND/OR
            if self._peek() in COND_OPS:
                conds.append(self._pop())   # append the AND/OR operator (connector)
        return conds
    
    def parse_val_unit(self, default_tables=None):
        """
        Parse a value unit. Which can be a column unit, or an expression with unit operations.

        :param default_tables: List of default tables to resolve column names.
        :returns: (unit_op, col_unit1, col_unit2), if unit_op is 'none', the tuple would be (0, col_unit1, None).
        """
        isBlock = False
        if self._peek() == '(':
            isBlock = True
            self._advance()

        col_unit1 = self.parse_col_unit(default_tables)
        col_unit2 = None
        unit_op = UNIT_OPS.index('none')

        if self._peek() in UNIT_OPS:
            unit_op = UNIT_OPS.index(self._pop())
            col_unit2 = self.parse_col_unit(default_tables)

        if isBlock:
            self._consume(')')

        return (unit_op, col_unit1, col_unit2)
    
    def parse_value(self, default_tables):
        value_tok = self._peek()
        # case value is a literal string
        if (value_tok.startswith('"') and value_tok.endswith('"')) or (value_tok.startswith("'") and value_tok.endswith("'")):
            val = self._pop()
            return val
        # case value is a number
        try:
            val = float(self._pop())
            return val
        except (ValueError, TypeError):
            # case value is a column unit or expression
            val = self.parse_col_unit(default_tables)
            return val

    def parse_col_unit(self, default_tables):
        """
        Parse a column unit, handle the possibility of aggregation and/or distinct.

        :returns: a tuple (agg_op id, col_id, isDistinct)
        """
        isBlock = False
        isDistinct = False

        if self._peek() == '(':  # handle block
            isBlock = True
            self._advance()

        # aggregation operator
        agg_id = AGG_OPS.index("none")
        if self._peek() in AGG_OPS:
            agg_id = AGG_OPS.index(self._pop())
            self._consume('(')
            if self._peek() == "distinct":
                self._advance()
                isDistinct = True
            col_id = self.parse_col(default_tables)
            self._consume(')')
            if isBlock:
                self._consume(')')
            return (agg_id, col_id, isDistinct)

        if self._peek() == "distinct":
            self._advance()
            isDistinct = True

        col_id = self.parse_col(default_tables)
        if isBlock:
            self._consume(')')
            
        return (agg_id, col_id, isDistinct)
    
    def parse_col(self, default_tables):
        """
            :returns column id advance the position.
        """
        col_tok = self._peek()
        print(f"col_tok: {col_tok}")
        # print(self._lexer.toks)
        if col_tok == "*":
            self._advance()
            return self._schema.idMap[col_tok]

        if '.' in col_tok:  # if token is a composite - e.g. table_a.col_b
            alias, col = col_tok.split('.')
            key = self._alias_tables[alias] + "." + col
            self._advance()
            return self._schema.idMap[key]

        assert default_tables is not None and len(default_tables) > 0, "Default tables should not be None or empty"

        for alias in default_tables:
            table = self._alias_tables[alias]
            if col_tok in self._schema.schema_dict[table]:   # find in each table's columns
                key = table + "." + col_tok
                self._advance()
                return self._schema.idMap[key]

        assert False, "Error col: {}".format(col_tok)

    def parse_where(self, default_tables):
        """
        :returns: a list of conditions
        """
        if self._peek() != 'where':
            return []
        self._advance()  # skip 'where'
        return self.parse_condition(default_tables)

    def parse_group_by(self, default_tables):
        """
        :returns: a tuple (col_units, column_group_units), where one is always empty.
        """
        if self._peek() != 'group':
            return []
        self._advance()  # skip 'group'
        self._consume('by')
        col_units = []
        print(self._sql['select'])
        while True:
            try:
                next_tok = int(self._peek())
                self._advance()
                col_unit = self._sql['select'][1][next_tok-1][1][1]  # get the column unit from select
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
        return col_units

    def parse_having(self, default_tables):
        """
        :returns: a list of conditions in the HAVING clause.
        """
        if self._peek() != 'having':
            return []
        self._advance()  # skip 'having'
        return self.parse_condition(default_tables)

    def parse_order_by(self, default_tables):
        """
        Returns: a tuple (order_type, val_units) where order_type is 'asc' or 'desc',
        and val_units is a list of value units to order by.
        """
        val_units = []

        order_types = []  # default type is 'asc'

        if self._peek() != 'order':
            return val_units
        self._advance()  # skip 'order'
        self._consume('by')
        
        print(self._lexer.toks)

        while True:
            print(self._peek())
            # check if the next token is a number
            try:
                next_tok = int(self._peek())
                self._advance()
                print(f"next_tok: {next_tok}")
                print(f"self._sql['select'][1]: {self._sql['select'][1]}")
                val_unit = list(self._sql['select'][1][next_tok-1][1])  # get the value unit from select
                val_unit_1_list = list(val_unit[1])
                val_unit_1_list[0] = self._sql['select'][1][next_tok-1][0]
                val_unit[1] = tuple(val_unit_1_list)
                val_unit = tuple(val_unit)
                val_units.append(tuple(val_unit))
                if self._peek() in ORDER_OPS:
                    order_types.append(self._pop())
            except ValueError:
                val_unit = self.parse_val_unit(default_tables)
                val_units.append(val_unit)
                if self._peek() in ORDER_OPS:
                    order_types.append(self._pop())
            if self._peek() == ',':
                self._advance()  # skip ','
            else:
                break
            if self._peek() in CLAUSE_KEYWORDS or self._peek() in (")", ";", None):
                break
        return (order_types, val_units)

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