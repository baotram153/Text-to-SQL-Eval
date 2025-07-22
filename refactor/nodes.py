from typing import Dict, List, Union, Tuple
from enum import Enum

class TableUnit:
    def __init__(self, type_):
        self.type = type_

    def __str__(self):
        return f"TableUnit(type={self.type})"

class ColUnit:
    def __init__(self, is_distinct):
        self.is_distinct = is_distinct

    def __str__(self):
        return f"ColUnit(distinct={self.is_distinct})"

class Select:
    def __init__(self, is_distinct=False, col_units: List[ColUnit]=[]):
        self.is_distinct = is_distinct
        self.col_units = col_units

    def __str__(self):
        return f"Select(is_distinct={self.is_distinct}, col_units=[{', '.join(str(cu) for cu in self.col_units)}])"

class Cond:
    def __init__(self, not_op, op_id, col_unit, val1, val2):
        self.not_op = not_op
        self.op_id = op_id
        self.col_unit = col_unit
        self.val1 = val1
        self.val2 = val2

    def __str__(self):
        not_str = "NOT " if self.not_op else ""
        return f"Cond(not_op={self.not_op}, op_id={self.op_id}, col_unit={self.col_unit}, val1={self.val1}, val2={self.val2})"

class Join:
    def __init__(self, join_type, table_unit, on_condition: List[Cond]):
        self.join_type = join_type
        self.table_unit = table_unit
        self.on_condition = on_condition

    def __str__(self):
        conds = ', '.join(str(cond) for cond in self.on_condition)
        return f"Join(join_type={self.join_type}, table_unit={self.table_unit}, on_condition=[{conds}])"

class TableRef(TableUnit):
    def __init__(self, id, name=None):
        super().__init__('table')
        self.id = id
        self.name = name

    def __str__(self):
        return f"TableRef(id={self.id}, name={self.name})"

class From:
    '''Table unit and list (possibly empty) of Joins'''
    def __init__(self, table_unit, joins: List[Join]):
        self.table_unit = table_unit
        self.joins = joins

    def __str__(self):
        joins_str = ', '.join(str(j) for j in self.joins)
        return f"From(table_unit={self.table_unit}, joins=[{joins_str}])"

class Where:
    def __init__(self, conds: List[Cond]):
        self.conds = conds

    def __str__(self):
        return f"Where(conds=[{', '.join(str(cond) for cond in self.conds)}])"

class GroupBy:
    def __init__(self, col_units: List[ColUnit]):
        self.col_units = col_units

    def __str__(self):
        return f"GroupBy(col_units=[{', '.join(str(cu) for cu in self.col_units)}])"

class Having:
    def __init__(self, conds: List[Cond]):
        self.conds = conds

    def __str__(self):
        return f"Having(conds=[{', '.join(str(cond) for cond in self.conds)}])"

class OrderBy:
    def __init__(self, order_cols: List[Tuple[ColUnit, str]]):
        self.order_cols = order_cols

    def __str__(self):
        return f"OrderBy(order_cols=[{', '.join(f'{col} {order}' for col, order in self.order_cols)}])"

class Sql(TableUnit):
    def __init__(
            self,
            type_: str = 'sql',
            select: Select=None, from_: From=None, where: Where=None,
            group_by: GroupBy=None, having: Having=None, order_by: OrderBy=None, limit=None,
            intersect=None, union=None, except_=None
        ):
        super().__init__(type_)
        self.select = select
        self.from_ = from_
        self.where = where
        self.group_by = group_by
        self.having = having
        self.order_by = order_by
        self.limit = limit
        self.intersect = intersect
        self.union = union
        self.except_ = except_

    def __str__(self):
        parts = [
            f"Sql(type={self.type}, ",
            f"select={self.select}, ",
            f"from_={self.from_}, ",
            f"where={self.where}, ",
            f"group_by={self.group_by}, ",
            f"having={self.having}, ",
            f"order_by={self.order_by}, ",
            f"limit={self.limit}, ",
            f"intersect={self.intersect}, ",
            f"union={self.union}, ",
            f"except_={self.except_})"
        ]
        return '\n'.join([p for p in parts if p])

class ValueUnit:
    def __init__(self, type, value):
        self.type = type
        self.value = value

    def __str__(self):
        return f"ValueUnit(type={self.type}, value={self.value})"

class ColRef(ColUnit):
    def __init__(self, col_id, col_name, is_distinct=False):
        super().__init__(is_distinct)
        self.col_id = col_id
        self.col_name = col_name

    def __str__(self):
        return f"ColRef(id={self.col_id}, name={self.col_name}, distinct={self.is_distinct})"

class Arith (ColUnit):
    def __init__(self, unit_op, col_unit1: ColUnit, col_unit2: ColUnit, is_distinct=False):
        super().__init__(is_distinct)
        self.unit_op = unit_op
        self.col_unit1 = col_unit1
        self.col_unit2 = col_unit2

    def __str__(self):
        return f"Arith(unit_op={self.unit_op}, col_unit1={self.col_unit1}, col_unit2={self.col_unit2}, distinct={self.is_distinct})"

class Agg (ColUnit):
    def __init__(self, agg_id, col_unit, is_distinct=False):
        ColUnit.__init__(self, is_distinct)
        self.agg_id = agg_id
        self.col_unit = col_unit

    def __str__(self):
        return f"Agg(agg_id={self.agg_id}, col_unit={self.col_unit}, distinct={self.is_distinct})"