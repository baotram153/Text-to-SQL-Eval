from utils.constants import TABLE_TYPE
import json

class Rebuilder:
    def __init__(self, disable_value=False, disable_distinct=False):
        self.DISABLE_VALUE = disable_value
        self.DISABLE_DISTINCT = disable_distinct

    def rebuild_cond_unit_val(self, cond_unit):
        if cond_unit is None or not self.DISABLE_VALUE:
            return cond_unit

        not_op, op_id, val_unit, val1, val2 = cond_unit
        if type(val1) is not dict:
            val1 = None
        else:
            val1 = self.rebuild_sql_val(val1)
        if type(val2) is not dict:
            val2 = None
        else:
            val2 = self.rebuild_sql_val(val2)
        return not_op, op_id, val_unit, val1, val2


    def rebuild_condition_val(self, condition):
        if condition is None or not self.DISABLE_VALUE:
            return condition

        res = []
        for idx, it in enumerate(condition):
            if idx % 2 == 0:
                res.append(self.rebuild_cond_unit_val(it))
            else:
                res.append(it)
        return res


    def rebuild_sql_val(self, sql):
        '''
        If DISABLE_VALUE is True, return sql where values = None
        '''
        if sql is None or not self.DISABLE_VALUE:
            return sql

        sql['from']['conds'] = self.rebuild_condition_val(sql['from']['conds'])
        sql['having'] = self.rebuild_condition_val(sql['having'])
        sql['where'] = self.rebuild_condition_val(sql['where'])
        sql['intersect'] = self.rebuild_sql_val(sql['intersect'])
        sql['except'] = self.rebuild_sql_val(sql['except'])
        sql['union'] = self.rebuild_sql_val(sql['union'])

        return sql


    # Rebuild SQL functions for foreign key evaluation
    def build_valid_col_units(self, table_units, schema):
        col_ids = [table_unit[1] for table_unit in table_units if table_unit[0] == TABLE_TYPE['table_unit']]
        prefixs = [col_id[:-2] for col_id in col_ids]
        valid_col_units= []
        for value in schema.idMap.values():
            if '.' in value and value[:value.index('.')] in prefixs:
                valid_col_units.append(value)
        return valid_col_units


    def rebuild_col_unit_col(self, valid_col_units, col_unit, kmap):
        if col_unit is None:
            return col_unit

        agg_id, col_id, distinct = col_unit
        if col_id in kmap and col_id in valid_col_units:
            col_id = kmap[col_id]
        if self.DISABLE_DISTINCT:
            distinct = None
        return agg_id, col_id, distinct


    def rebuild_val_unit_col(self, valid_col_units, val_unit, kmap):
        if val_unit is None:
            return val_unit

        unit_op, col_unit1, col_unit2 = val_unit
        col_unit1 = self.rebuild_col_unit_col(valid_col_units, col_unit1, kmap)
        col_unit2 = self.rebuild_col_unit_col(valid_col_units, col_unit2, kmap)
        return unit_op, col_unit1, col_unit2


    def rebuild_table_unit_col(self, valid_col_units, table_unit, kmap):
        if table_unit is None:
            return table_unit

        table_type, col_unit_or_sql = table_unit
        if isinstance(col_unit_or_sql, tuple):
            col_unit_or_sql = self.rebuild_col_unit_col(valid_col_units, col_unit_or_sql, kmap)
        return table_type, col_unit_or_sql


    def rebuild_cond_unit_col(self, valid_col_units, cond_unit, kmap):
        if cond_unit is None:
            return cond_unit

        not_op, op_id, val_unit, val1, val2 = cond_unit
        val_unit = self.rebuild_val_unit_col(valid_col_units, val_unit, kmap)
        return not_op, op_id, val_unit, val1, val2


    def rebuild_condition_col(self, valid_col_units, condition, kmap):
        if condition is None:
            return condition

        for idx in range(len(condition)):
            if idx % 2 == 0:
                condition[idx] = self.rebuild_cond_unit_col(valid_col_units, condition[idx], kmap)
        return condition


    def rebuild_select_col(self, valid_col_units, sel, kmap):
        if sel is None:
            return sel
        distinct, _list = sel
        new_list = []
        for it in _list:
            agg_id, val_unit = it
            new_list.append((agg_id, self.rebuild_val_unit_col(valid_col_units, val_unit, kmap)))
        if self.DISABLE_DISTINCT:
            distinct = None
        return distinct, new_list


    def rebuild_from_col(self, valid_col_units, from_, kmap):
        if from_ is None:
            return from_

        from_['table_units'] = [self.rebuild_table_unit_col(valid_col_units, table_unit, kmap) for table_unit in from_['table_units']]
        from_['conds'] = self.rebuild_condition_col(valid_col_units, from_['conds'], kmap)
        return from_


    def rebuild_group_by_col(self, valid_col_units, group_by, kmap):
        if group_by is None:
            return group_by

        return [self.rebuild_col_unit_col(valid_col_units, col_unit, kmap) for col_unit in group_by]


    def rebuild_order_by_col(self, valid_col_units, order_by, kmap):
        if order_by is None or len(order_by) == 0:
            return order_by

        direction, val_units = order_by
        new_val_units = [self.rebuild_val_unit_col(valid_col_units, val_unit, kmap) for val_unit in val_units]
        return direction, new_val_units


    def rebuild_sql_col(self, valid_col_units, sql, kmap):
        if sql is None:
            return sql

        sql['select'] = self.rebuild_select_col(valid_col_units, sql['select'], kmap)
        sql['from'] = self.rebuild_from_col(valid_col_units, sql['from'], kmap)
        sql['where'] = self.rebuild_condition_col(valid_col_units, sql['where'], kmap)
        sql['groupBy'] = self.rebuild_group_by_col(valid_col_units, sql['groupBy'], kmap)
        sql['orderBy'] = self.rebuild_order_by_col(valid_col_units, sql['orderBy'], kmap)
        sql['having'] = self.rebuild_condition_col(valid_col_units, sql['having'], kmap)
        sql['intersect'] = self.rebuild_sql_col(valid_col_units, sql['intersect'], kmap)
        sql['except'] = self.rebuild_sql_col(valid_col_units, sql['except'], kmap)
        sql['union'] = self.rebuild_sql_col(valid_col_units, sql['union'], kmap)

        return sql

    def build_foreign_key_map(self, entry):
        '''
        Return a dictionary with the primary key as key and the foreign keys as values.
        The keys are in the format "__table.column__" or "__all__" for all
            e.g.
            {
                "__table1.column1__": "__table1.column1__",
                "__table2.column2__": "__table1.column1__",
                ...
            }
        '''
        cols_orig = entry["column_names_original"]
        tables_orig = entry["table_names_original"]
        cols = []
        for col_orig in cols_orig:
            if col_orig[0] >= 0:
                t = tables_orig[col_orig[0]]
                c = col_orig[1]
                cols.append("__" + t.lower() + "." + c.lower() + "__")
            else:
                cols.append("__all__")

        def keyset_in_list(k1, k2, k_list):
            '''
            :params k_list: a list of sets, each set contains the primary key and its foreign keys

            If k1 or k2 is already in the list, return the set containing it.
            If not, create a new set, add it to the list and return it.
            '''
            for k_set in k_list:
                if k1 in k_set or k2 in k_set:
                    return k_set
            new_k_set = set()
            k_list.append(new_k_set)
            return new_k_set

        foreign_key_list = []
        foreign_keys = entry["foreign_keys"]
        for fkey in foreign_keys:
            key1, key2 = fkey
            key_set = keyset_in_list(key1, key2, foreign_key_list)
            key_set.add(key1)
            key_set.add(key2)

        foreign_key_map = {}
        for key_set in foreign_key_list:
            sorted_list = sorted(list(key_set))
            midx = sorted_list[0]
            for idx in sorted_list:
                foreign_key_map[cols[idx]] = cols[midx]
        return foreign_key_map

    def build_foreign_key_map_from_json(self, table):
        '''
        Returns a dictionary mapping db_id to foreign key map
        '''
        with open(table) as f:
            data = json.load(f)
        tables = {}
        for entry in data:
            tables[entry['db_id']] = self.build_foreign_key_map(entry)
        return tables