from utils.constants import *
from utils.evaluation_visitor import SqlVisitor
import logging
import numpy as np
import logging
import sys
from refactor.nodes import *
from typing import List, Tuple, Any
import datetime
from nltk import word_tokenize

logger = logging.getLogger(__name__)

class Evaluator(SqlVisitor):
    def __init__(self):
        self.partial_scores = None

    def eval_exact_match(self, pred, label):
        self.partial_scores = self.eval_partial_match(pred, label)
        for _, score in self.partial_scores.items():
            if score['f1'] != 1:
                return 0
        # Table units comparison
        if hasattr(label.from_, 'table_unit') and label.from_.table_unit:
            label_tables = sorted([str(label.from_.table_unit)])
            pred_tables = sorted([str(pred.from_.table_unit)])
            return label_tables == pred_tables
        return 1

    def eval_partial_match(self, pred: Sql, label: Sql):
        assert isinstance(pred, Sql) and isinstance(label, Sql), "Both pred and label must be Sql instances"
        partial_scores, exact_match = self.visit(pred, label)
        partial_scores['avg'] = {
            'acc': np.mean([score['acc'] for score in partial_scores.values()]),
            'rec': np.mean([score['rec'] for score in partial_scores.values()]),
            'prec': np.mean([score['prec'] for score in partial_scores.values()]),
            'f1': np.mean([score['f1'] for score in partial_scores.values()])
        }
        return partial_scores, exact_match

    def normalize_table(self, table: List[List[Any]],
                *,
                ordered: bool = False,
                epsilon: float = 1e-6) -> List[Any]:
        if not table:                                    # empty result
            return []

        header, rows = table[0], table[1:]
        # column order
        if ordered:
            order = list(range(len(header)))
            new_header = header[:]
        else:
            order = [i for i, _ in sorted(enumerate(header), key=lambda p: p[1])]
            new_header = [header[i] for i in order]

        def norm(val: Any) -> Any:
            '''Normalize a cell value.
            '''
            if val is None or (isinstance(val, str) and val.strip().upper() == "NULL"):
                return "null"
            if isinstance(val, (int, float)):
                return str(round(float(val), 6)) if isinstance(val, float) else str(val)
            if isinstance(val, str):
                # numeric disguised as str
                try:
                    f = float(val)
                    return str(round(f, 6)) if abs(f - int(f)) >= epsilon else str(int(round(f)))
                except ValueError:
                    pass
                # date formats to ISO
                for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%m/%d/%Y"):
                    try:
                        return datetime.datetime.strptime(val.strip(), fmt).date().isoformat()
                    except ValueError:
                        continue
                return val.strip()
            return val

        norm_rows: List[Tuple[Any, ...]] = [
            [norm(row[i]) for i in order] for row in rows
        ]

        if not ordered:
            norm_rows.sort(key=lambda r: tuple("" if x is None else str(x) for x in r))

        return [new_header] + norm_rows
    
    def normalize_tables(self, tables: Dict[str, List[List[Any]]]) -> Dict[str, List[Any]]:
        """
        Normalize a dictionary of predicted and ground truth tables. -> Change to format passable into Pandas
        [['col1', 'col2'],['row11', 'row12'], ['row21', 'row22'], ...] -> { 'col1': ['row11', 'row21', ...], 'col2': ['row12', 'row22', ...] }
        """
        gt_table = tables['gt_res']
        pred_table = tables['pred_res']

        # if not gt_table:
        #     pred_table[1:] = sorted(pred_table[1:], key=lambda x: str(x))
        #     return {
        #         'norm_pred': pred_table,
        #         'norm_gt': gt_table
        #     }
        # if not pred_table:
        #     gt_table[1:] = sorted(gt_table[1:], key=lambda x: str(x))
        #     return {
        #         'norm_pred': pred_table,
        #         'norm_gt': gt_table
        #     }
        def array_to_dict(array):
            if not array or len(array) == 0: return {}
            keys = array[0]
            result = {key: [row[i].strip() if i == 0 else row[i] for row in array[1:]] for i, key in enumerate(keys)}
            print(f"Result: {result}")
            return result
        gt_table_dict = array_to_dict(gt_table)
        pred_table_dict = array_to_dict(pred_table)

        column_match_dict = {}  # pred_col : gt_col
        pred_col_order = []
        gt_col_order = []
        for pred_col in pred_table_dict.keys():
            for gt_col in gt_table_dict.keys():
                if set(pred_table_dict[pred_col]) == set(gt_table_dict[gt_col]):
                    pred_col_idx = np.where(np.array(pred_table[0]) == pred_col)[0][0]
                    gt_col_idx = np.where(np.array(gt_table[0]) == gt_col)[0][0]
                    column_match_dict[pred_col_idx] = gt_col_idx
        
        for k, v in  column_match_dict.items():
            pred_col_order.append(k)
            gt_col_order.append(v)
        
        def arange_order(table, order, original_indices):
            surplus_col = list(set(original_indices) - set(order))
            order.extend(surplus_col)
            new_table = [
                [table[i][j] for j in order] for i in range(len(table))
            ]
            return new_table
        
        # breakpoint()
        norm_pred_table = arange_order(pred_table, pred_col_order, range(len(pred_table[0])))
        norm_gt_table = arange_order(gt_table, gt_col_order, range(len(gt_table[0])))

        # normalize rows
        norm_pred_table[1:] = sorted(norm_pred_table[1:], key=lambda x: str(x))
        norm_gt_table[1:] = sorted(norm_gt_table[1:], key=lambda x: str(x))
        return {
            'norm_pred': norm_pred_table,
            'norm_gt': norm_gt_table
        }



    def check_columns(self, norm_pred, norm_label, nl, info):
        if len(norm_pred[0]) == len(norm_label[0]):
            return True, norm_pred
        elif len(norm_pred[0]) < len(norm_label[0]):
            info.append(f"Number of pred columns is smaller than number of gt columns: {len(norm_pred[0])} vs {len(norm_label[0])}. The model may forget an important column.")
            return False, None
        else:
            # match columns to find surplus one
            col_pairs = []
            for i in range(len(norm_pred[0])):
                for j in range(len(norm_label[0])):
                    if all(np.array(norm_pred)[1:, i] == np.array(norm_label)[1:,j]):
                        col_pairs.append((norm_pred[0][i], norm_label[0][j]))
            surplus_cols = set(norm_pred[0]) - set([col_name for col_name, _ in col_pairs])
            # breakpoint()

            # check if the surplus column in norm_pred is mentioned in the nl
            nl_sentences = nl.lower().split('.')
            nl_sentences_toks = [word_tokenize(sent) for sent in nl_sentences]  # list of lists
            neg_toks = ['not', 'no', 'without', 'exclude',  'except', 'ignore', 'skip', 'omit']
            for surplus_col in surplus_cols:
                toks = [t.lower() for t in word_tokenize(surplus_col)]
                for sent_toks in nl_sentences_toks:
                    if set(toks).issubset(set(sent_toks)) and not set(sent_toks).intersection(set(neg_toks)):
                        info.append(f"Surplus column '{surplus_col}' in pred is mentioned in nl.")
                        return False, None
                # remove the surplus column from norm_pred
                norm_pred = np.delete(np.array(norm_pred), np.where(np.array(norm_pred[0]) == surplus_col), axis=1).tolist()
        return True, norm_pred

    def check_rows(self, norm_pred, norm_label, info):
        if len(norm_pred) > len(norm_label):
            info.append(f"Number of pred rows is larger than number of gt rows: {len(norm_pred)} vs {len(norm_label)}. The model may forget LIMIT.")
            return False
        return True

    def eval_exec_match(self, pred_table, label_table, nl, compare_header=False):
        """
        return 1 if the values between prediction and gold are matching
        in the corresponding index. Currently not support multiple col_unit(pairs).
        """
        # breakpoint()
        info = []   # contains helpful normalization and evaluating notes
        # norm_pred = self.normalize_table(pred_table)
        # norm_label = self.normalize_table(label_table)
        if not pred_table: pred_table = [[]]
        if not label_table: label_table = [[]]
        norm_tables = self.normalize_tables({'gt_res': label_table, 'pred_res': pred_table})
        norm_pred, norm_label = norm_tables['norm_pred'], norm_tables['norm_gt']
        # breakpoint()
        logger.debug(f"norm_pred: {norm_pred}, norm_label: {norm_label}")
        if len(norm_pred) == 0 and len(norm_label) == 0:
            return True, norm_pred, norm_label, info
        if len(norm_pred) == 0 or len(norm_label) == 0:
            info.append(f"One of the tables is empty: pred {len(norm_pred)} vs label {len(norm_label)}")
            return False, norm_pred, norm_label, info
        checked_column, modified_norm_pred = self.check_columns(norm_pred, norm_label, nl, info)
        # breakpoint()
        if not checked_column:
            return False, norm_pred, norm_label, info
        if not self.check_rows(modified_norm_pred, norm_label, info):
            return False, norm_pred, norm_label, info
        if compare_header:
            # headers are sometimes not important, so we want to skip this
            score = np.all(np.array(modified_norm_pred) == np.array(norm_label))
        else:
            score = np.all(np.array(modified_norm_pred[1:]) == np.array(norm_label[1:]))
        return score, modified_norm_pred, norm_label, info

    def calculate_scores(self, actual_true, gt_total, pred_total):
        acc = actual_true / (gt_total + pred_total - actual_true) if (gt_total + pred_total - actual_true) != 0 else 1
        rec = actual_true / pred_total if pred_total != 0 else 1
        prec = actual_true / gt_total if gt_total != 0 else 1
        f1 = 2 * prec * rec / (prec + rec) if prec + rec != 0 else 0
        return {
            'acc': acc,
            'rec': rec,
            'prec': prec,
            'f1': f1
        }

    def extract_table_and_conds(self, join: Join):
        return join.table_unit, join.on_condition

    def visit_Sql_Sql(self, node1: Sql, node2: Sql):
        partial_scores = {}
        partial_scores['select'], select_exact_match = self.visit(node1.select, node2.select)
        partial_scores['from'], from_exact_match = self.visit(node1.from_, node2.from_)
        partial_scores['where'], where_exact_match = self.visit(node1.where, node2.where)
        partial_scores['group_by'], group_by_exact_match = self.visit(node1.group_by, node2.group_by)
        partial_scores['having'], having_exact_match = self.visit(node1.having, node2.having)
        partial_scores['order_by'], order_by_exact_match = self.visit(node1.order_by, node2.order_by)
        partial_scores['limit'], limit_exact_match = self.visit(node1.limit, node2.limit)

        exact_match = (select_exact_match and from_exact_match and
                       where_exact_match and group_by_exact_match and
                       having_exact_match and order_by_exact_match and limit_exact_match)

        # partial_scores['intersect'] = self.visit(node1.intersect, node2.intersect)
        # partial_scores['union'] = self.visit(node1.union, node2.union)
        # partial_scores['except'] = self.visit(node1.except_, node2.except_)
        return partial_scores, exact_match

    def visit_Select_Select(self, node1: Select, node2: Select):
        '''
        Return Acc, Rec, Precision, F1 and if two nodes are matched
        Mimic set comparision - ignore wrong ordering
        '''
        if not node1 or not node2:
            return 0, 0, 0, 0, 0
        assert node1.col_units is not None and node2.col_units is not None, "Select nodes must have col_units"

        gt_total = len(node1.col_units)
        pred_total = len(node2.col_units)

        # recall - actually true / total predicted
        actual_true = 0
        for col_unit in node1.col_units:
            if col_unit in node2.col_units:
                actual_true += 1

        score_dict = self.calculate_scores(actual_true, gt_total, pred_total)

        return score_dict, score_dict['acc'] == 1

    def visit_From_From(self, node1: From, node2: From):
        """
        From has multiple tables combined by 'JOIN'
        Match the set of tables + Match the set of conditions -> average out
        """
        if not node1 or not node2:
            return 0, 0, 0, 0, 0
        
        if node1.table_unit is None or node2.table_unit is None:
            return {'acc': 0, 'rec': 0, 'prec': 0, 'f1': 0}, False

        gt_tables, gt_conds = [], []
        pred_tables, pred_conds = [], []
        for join in node1.joins:
            table, join_conds = self.extract_table_and_conds(join)
            gt_tables.append(table)
            gt_conds.extend(join_conds)
        for join in node2.joins:
            table, join_conds = self.extract_table_and_conds(join)
            pred_tables.append(table)
            pred_conds.extend(join_conds)
        
        if len(gt_tables) == len(pred_tables) == 0:
            return {'acc': 1, 'rec': 1, 'prec': 1, 'f1': 1}, True

        # evaluate tables
        # TableUnit can be TableRef and Sql
        pred_table_refs = [node for node in pred_tables if node.type == 'table']
        pred_sql = [node for node in pred_tables if node.type == 'sql']
        gt_table_refs = [node for node in gt_tables if node.type == 'table']
        gt_sql = [node for node in gt_tables if node.type == 'sql']

        # for TableRefs, compare 2 tables
        actual_true = 0
        for table in pred_table_refs:
            if table in gt_table_refs:
                actual_true += 1

        # for Sqls, calculate score for each pair of Sqls -> return the max score
        if len(pred_sql) > 0 and len(gt_sql) > 0:
            for pred_sql in pred_sql:
                max_score = 0
                for gt_sql in gt_sql:
                    acc, rec, prec, f1, _ =  self.visit(pred_sql, gt_sql)
                    if acc > max_score: max_score = acc
                if max_score > 0.5: actual_true += 1

        gt_total, pred_total = len(gt_tables), len(pred_tables)
        table_scores = self.calculate_scores(actual_true, gt_total, pred_total)

        # evaluate conds
        actual_true = 0
        for cond in pred_conds:
            if cond in gt_conds:
                actual_true += 1

        gt_total, pred_total = len(gt_conds), len(pred_conds)
        conds_scores = self.calculate_scores(actual_true, gt_total, pred_total)

        # can be adjusted to desired weights
        acc = (table_scores['acc'] + conds_scores['acc']) / 2
        rec = (table_scores['rec'] + conds_scores['rec']) / 2
        prec = (table_scores['prec'] + conds_scores['prec']) / 2
        f1 = (table_scores['f1'] + conds_scores['f1']) / 2

        return {
            'acc': acc,
            'rec': rec,
            'prec': prec,
            'f1': f1
        }, acc == 1

    def visit_Where_Where(self, node1: Where, node2: Where):
        if not node1 or not node2:
            return 0, 0, 0, 0, 0
        print(f"In visit where: {node1.conds}, {node2.conds}")
        assert node1.conds is not None and node2.conds is not None, "Where nodes must have conds"
        if len(node1.conds) == 0 and len(node2.conds) == 0:
            return {'acc': 1, 'rec': 1, 'prec': 1, 'f1': 1}, True

        gt_total, pred_total = len(node1.conds), len(node2.conds)

        actual_true = 0
        for cond in node1.conds:
            if cond in node2.conds:
                actual_true += 1

        scores = self.calculate_scores(actual_true, gt_total, pred_total)
        return scores, scores['acc'] == 1

    def visit_OrderBy_OrderBy(self, node1: OrderBy, node2: OrderBy):
        if not node1 or not node2:
            return 0, 0, 0, 0, 0
        assert node1.order_cols is not None and node2.order_cols is not None, "OrderBy nodes must have order"
        if len(node1.order_cols) == 0 and len(node2.order_cols) == 0:
            return {'acc': 1, 'rec': 1, 'prec': 1, 'f1': 1}, True

        gt_total, pred_total = len(node1.order_cols), len(node2.order_cols)

        actual_true = 0
        for order_col in node1.order_cols:
            if order_col in node2.order_cols:
                actual_true += 1

        scores = self.calculate_scores(actual_true, gt_total, pred_total)
        return scores, scores['acc'] == 1

    def visit_GroupBy_GroupBy(self, node1: GroupBy, node2: GroupBy):
        if not node1 or not node2:
            return 0, 0, 0, 0, 0
        assert node1.col_units is not None and node2.col_units is not None, "GroupBy nodes must have group_cols"
        if len(node1.col_units) == 0 and len(node2.col_units) == 0:
            return {'acc': 1, 'rec': 1, 'prec': 1, 'f1': 1}, True

        gt_total, pred_total = len(node1.col_units), len(node2.col_units)

        actual_true = 0
        for group_col in node1.col_units:
            if group_col in node2.col_units:
                actual_true += 1

        scores = self.calculate_scores(actual_true, gt_total, pred_total)
        return scores, scores['acc'] == 1

    def visit_Having_Having(self, node1: Having, node2: Having):
        if not node1 or not node2:
            return 0, 0, 0, 0, 0
        assert node1.conds is not None and node2.conds is not None, "Having nodes must have conds"
        if len(node1.conds) == 0 and len(node2.conds) == 0:
            return {'acc': 1, 'rec': 1, 'prec': 1, 'f1': 1}, True

        gt_total, pred_total = len(node1.conds), len(node2.conds)

        actual_true = 0
        for cond in node1.conds:
            if cond in node2.conds:
                actual_true += 1

        scores = self.calculate_scores(actual_true, gt_total, pred_total)
        return scores, scores['acc'] == 1

    def visit_Limit_Limit(self, node1: Limit, node2: Limit):
        if not node1 or not node2:
            return {'acc': 0, 'rec': 0, 'prec': 0, 'f1': 0}, False
        
        if node1.value is None and node2.value is None:
            return {'acc': 1, 'rec': 1, 'prec': 1, 'f1': 1}, True

        if node1.value == node2.value:
            return {'acc': 1, 'rec': 1, 'prec': 1, 'f1': 1}, True
        return {'acc': 0, 'rec': 0, 'prec': 0, 'f1': 0}, False