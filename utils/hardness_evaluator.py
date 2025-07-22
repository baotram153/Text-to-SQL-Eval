from .constants import *
HARDNESS = {
    "component1": ('where', 'group', 'order', 'limit', 'join', 'or', 'like'),
    "component2": ('except', 'union', 'intersect')
}

class HardnessEvaluator:
    """
    A class to evaluate the hardness of SQL queries based on their structure and components.
    """

    def __init__(self, query):
        self.sql = query

    def eval_hardness(self):
        count_comp1_ = self.count_component1()
        count_comp2_ = self.count_component2()
        count_others_ = self.count_others()

        if count_comp1_ <= 1 and count_others_ == 0 and count_comp2_ == 0:
            return "easy"
        elif (count_others_ <= 2 and count_comp1_ <= 1 and count_comp2_ == 0) or \
                (count_comp1_ <= 2 and count_others_ < 2 and count_comp2_ == 0):
            return "medium"
        elif (count_others_ > 2 and count_comp1_ <= 2 and count_comp2_ == 0) or \
                (2 < count_comp1_ <= 3 and count_others_ <= 2 and count_comp2_ == 0) or \
                (count_comp1_ <= 1 and count_others_ == 0 and count_comp2_ <= 1):
            return "hard"
        else:
            return "extra"
        
    # HELPER METHODS ============================================
    def count_component1(self):
        """
        Count the number of components in component1 to evaluate hardness.
        """
        count = 0

        # count the number of components in component1.
        if len(self.sql['where']) > 0:
            count += 1
        if len(self.sql['groupBy']) > 0:
            count += 1
        if len(self.sql['orderBy']) > 0:
            count += 1
        if self.sql['limit'] is not None:
            count += 1

        # add 1 for each additional table (beyond the first) in the FROM clause.
        if len(self.sql['from']['table_units']) > 0:  # JOIN
            count += len(self.sql['from']['table_units']) - 1

        # count OR and LIKE operators in the FROM, WHERE, and HAVING clauses.
        ao = self.sql['from']['conds'][1::2] + self.sql['where'][1::2] + self.sql['having'][1::2]
        count += len([token for token in ao if token == 'or'])
        cond_units = self.sql['from']['conds'][::2] + self.sql['where'][::2] + self.sql['having'][::2]
        count += len([cond_unit for cond_unit in cond_units if cond_unit[1] == WHERE_OPS.index('like')])

        return count
    
    def count_component2(self):
        nested = self.get_nestedSQL()
        return len(nested)
    
    def get_nestedSQL(self):
        """
        Extracts nested SQL components from the given SQL structure.

        :returns: a list of nested SQL components (dict).
        """
        nested = []
        for cond_unit in self.sql['from']['conds'][::2] + self.sql['where'][::2] + self.sql['having'][::2]:
            if type(cond_unit[3]) is dict:
                nested.append(cond_unit[3])
            if type(cond_unit[4]) is dict:
                nested.append(cond_unit[4])
        if self.sql['intersect'] is not None:
            nested.append(self.sql['intersect'])
        if self.sql['except'] is not None:
            nested.append(self.sql['except'])
        if self.sql['union'] is not None:
            nested.append(self.sql['union'])
        return nested

    def count_others(self):
        count = 0
        # number of aggregation
        agg_count = self.count_agg(self.sql['select'][1])
        agg_count += self.count_agg(self.sql['where'][::2])
        agg_count += self.count_agg(self.sql['groupBy'])
        if len(self.sql['orderBy']) > 0:
            agg_count += self.count_agg([unit[1] for unit in self.sql['orderBy'][1] if unit[1]] +
                                [unit[2] for unit in self.sql['orderBy'][1] if unit[2]])
        agg_count += self.count_agg(self.sql['having'])
        if agg_count > 1:
            count += 1

        # add 1 for each additional number of select columns
        if len(self.sql['select'][1]) > 1:
            count += 1

        # add 1 for each additional table in the FROM clause
        if len(self.sql['where']) > 1:
            count += 1

        # add 1 for each additional table in the GROUP BY clause
        if len(self.sql['groupBy']) > 1:
            count += 1

        return count

    
    def count_agg(self, units):
        return len([unit for unit in units if self.has_agg(unit)])
    
    def has_agg(self, unit):
        return unit[0] != AGG_OPS.index('none')