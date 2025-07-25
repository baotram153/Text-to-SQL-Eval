from typing import Dict, List, Union, Tuple
from enum import Enum
from utils.constants import *

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
    def __init__(self, col_units: List[ColUnit]=[]):
        self.col_units = col_units

    def __str__(self):
        return f"Select(col_units=[{', '.join(str(cu) for cu in self.col_units)}])"

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

    def __eq__(self, other):
        if not isinstance(other, Cond):
            return False
        else:
            # issue ['=', '>', '<', '>=', '<='] - only when col_unit and val1 are of same types
            if type(self.col_unit) != type(self.val1):
                return (self.not_op == other.not_op
                        and self.op_id == other.op_id
                        and self.col_unit == other.col_unit
                        and self.val1 == other.val1)
            if type(other.col_unit) != type(other.val1):
                return False

            equal_op = WHERE_OPS.index('=')
            lt, gt = WHERE_OPS.index('<'), WHERE_OPS.index('>')
            lte, gte = WHERE_OPS.index('<='), WHERE_OPS.index('>=')

            if self.op_id == other.op_id == equal_op:
                return (self.val1 == other.val1 and self.val2 == other.val2
                        or self.val1 == other.val2 and self.val2 == other.val1)

            if self.op_id == lt:
                return (self.not_op == other.not_op and other.op_id == gt and self.val1 == other.val2 and self.val2 == other.val1
                        or self.not_op != other.not_op and other.op_id == gte and self.val1 == other.val1 and self.val2 == other.val2
                        or self.not_op != other.not_op and other.op_id == lte and self.val1 == other.val2 and self.val2 == other.val1)

            if self.op_id == gt:
                return (self.not_op == other.not_op and other.op_id == lt and self.val1 == other.val2 and self.val2 == other.val1
                        or self.not_op != other.not_op and other.op_id == lte and self.val1 == other.val1 and self.val2 == other.val2
                        or self.not_op != other.not_op and other.op_id == gte and self.val1 == other.val2 and self.val2 == other.val1)

            if self.op_id == lte:
                return (self.not_op == other.not_op and other.op_id == gte and self.val1 == other.val2 and self.val2 == other.val1
                        or self.not_op != other.not_op and other.op_id == gt and self.val1 == other.val1 and self.val2 == other.val2
                        or self.not_op != other.not_op and other.op_id == lt and self.val1 == other.val2 and self.val2 == other.val1)

            if self.op_id == gte:
                return (self.not_op == other.not_op and other.op_id == lte and self.val1 == other.val2 and self.val2 == other.val1
                        or self.not_op != other.not_op and other.op_id == lt and self.val1 == other.val1 and self.val2 == other.val2
                        or self.not_op != other.not_op and other.op_id == gt and self.val1 == other.val2 and self.val2 == other.val1)
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

    def __eq__(self, other):
        if not isinstance(other, TableRef):
            return False
        else:
            return (self.id == other.id
                    and self.type == other.type)
class From:
    '''Table unit and list (possibly empty) of Joins'''
    def __init__(self, table_unit: TableUnit=None, joins: List[Join]=[]):
        self.table_unit = table_unit
        self.joins = joins

    def __str__(self):
        joins_str = ', '.join(str(j) for j in self.joins)
        return f"From(table_unit={self.table_unit}, joins=[{joins_str}])"

class Where:
    def __init__(self, conds: List[Cond]=[]):
        self.conds = conds

    def __str__(self):
        return f"Where(conds=[{', '.join(str(cond) for cond in self.conds)}])"

class GroupBy:
    def __init__(self, col_units: List[ColUnit]=[]):
        self.col_units = col_units

    def __str__(self):
        return f"GroupBy(col_units=[{', '.join(str(cu) for cu in self.col_units)}])"

class Having:
    def __init__(self, conds: List[Cond]=[]):
        self.conds = conds

    def __str__(self):
        return f"Having(conds=[{', '.join(str(cond) for cond in self.conds)}])"

class OrderBy:
    def __init__(self, order_cols: List[Tuple[ColUnit, str]]=[]):
        self.order_cols = order_cols

    def __str__(self):
        return f"OrderBy(order_cols=[{', '.join(f'{col} {order}' for col, order in self.order_cols)}])"

class Limit():
    def __init__(self, value=None):
        self.value = value

    def __str__(self):
        return f"Limit(value={self.value})"

    def __eq__(self, other):
        if not isinstance(other, Limit):
            return False
        else:
            return (self.value == other.value)
        
class Sql(TableUnit):
    def __init__(
            self,
            type_: str = 'sql',
            select: Select=Select(), from_: From=From(), where: Where=Where(),
            group_by: GroupBy=GroupBy(), having: Having=Having(), order_by: OrderBy=OrderBy(), limit=Limit(),
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

    def __eq__(self, other):
        if not isinstance(other, ValueUnit):
            return False
        else:
            return (self.type == other.type and self.value == other.value)
class ColRef(ColUnit):
    def __init__(self, col_id, col_name, is_distinct=False):
        super().__init__(is_distinct)
        self.col_id = col_id
        self.col_name = col_name

    def __str__(self):
        return f"ColRef(id={self.col_id}, name={self.col_name}, distinct={self.is_distinct})"

    def __eq__(self, other):
        if not isinstance(other, ColRef):
            return False
        else:
            return (self.col_id == other.col_id and self.is_distinct == other.is_distinct)
class Arith (ColUnit):
    def __init__(self, unit_op, col_unit1: ColUnit, col_unit2: ColUnit, is_distinct=False):
        super().__init__(is_distinct)
        self.unit_op = unit_op
        self.col_unit1 = col_unit1
        self.col_unit2 = col_unit2

    def __str__(self):
        return f"Arith(unit_op={self.unit_op}, col_unit1={self.col_unit1}, col_unit2={self.col_unit2}, distinct={self.is_distinct})"

    def __eq__(self, other):
        if not isinstance(other, Arith):
            return False
        else:
            return (self.unit_op == other.unit_op
                    and self.col_unit1 == other.col_unit1
                    and self.col_unit2 == other.col_unit2
                    and self.is_distinct == other.is_distinct)
class Agg (ColUnit):
    def __init__(self, agg_id, col_unit, is_distinct=False):
        ColUnit.__init__(self, is_distinct)
        self.agg_id = agg_id
        self.col_unit = col_unit

    def __eq__(self, other):
        if not isinstance(other, Agg):
            return False
        else:
            return (self.agg_id == other.agg_id
                    and self.col_unit == other.col_unit
                    and self.is_distinct == other.is_distinct)

    def __str__(self):
        return f"Agg(agg_id={self.agg_id}, col_unit={self.col_unit}, distinct={self.is_distinct})"