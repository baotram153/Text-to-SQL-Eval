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
        
    def parse(self):
        """Parse the SQL query from the lexer tokens."""
        _, sql = self._parse_sql()
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
        if 0 <= idx < len(self._toks):
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
        isBlock = False # indicate whether this is a block of sql/sub-sql
        idx = self._pos

        sql = {}
        if self._peek() == '(':
            isBlock = True
            self._advance()

        # parse from clause in order to get default tables
        table_units, conds, default_tables = self.parse_from()
        sql['from'] = {'table_units': table_units, 'conds': conds}
        
        # select clause
        _, select_col_units = self.parse_select(default_tables)
        sql['select'] = select_col_units
        
        # where clause
        sql['where'] = self.parse_where(default_tables)
        sql['groupBy'] = self.parse_group_by(default_tables)
        sql['having'] = self.parse_having(default_tables)
        sql['orderBy'] = self.parse_order_by(default_tables)
        sql['limit'] = self.parse_limit()

        # skip semicolon if present
        while self._peek() == ';':
            self._advance()
            
        # if this is a block, we should consume the closing parenthesis
        if isBlock:
            self._consume(')')

        # intersect/union/except clause
        for op in SQL_OPS:  # initialize IUE
            sql[op] = None
        if self._peek() in SQL_OPS:
            sql_op = self._pop()
            IUE_sql = self.parse_sql()
            sql[sql_op] = IUE_sql
        return sql
    
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
        pass
    
    def parse_table_unit(self):
        """Return table id, table real name, advance the position."""
        table_name = self._pop()
        
        # get table real name
        actual_table_name = self._alias_tables.get(table_name, table_name)
        
        # advance the posion if needed
        if self._peek() == 'as':
            self._advance(n=2)  # skip 'as' and the alias token
            
        return self._schema.idMap[actual_table_name], actual_table_name

    def parse_condition(self, default_tables):
        '''
            :returns conds: list of conditions in the form:
            [condition1, 'and', condition2, 'or', condition3, ...]
        '''
        conds = []

        while self._pos < len(self._toks):
            val_unit = self.parse_val_unit()
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
    
    def parse_val_unit(self):
        pass
    
    def parse_value(self, default_tables):
        