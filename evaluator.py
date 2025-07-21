from utils.constants import *
import sqlite3
import datetime
from typing import List, Any, Tuple
import json

class Evaluator:
    def __init__(self):
        self.partial_scores = None

    def eval_exact_match(self, pred, label):
        self.partial_scores = self.eval_partial_match(pred, label)

        for _, score in self.partial_scores.items():
            # exact match only = 1 when all components have f1 = 1
            if score['f1'] != 1:
                return 0

        if len(label['from']['table_units']) > 0:
            label_tables = sorted(label['from']['table_units'])
            pred_tables = sorted(pred['from']['table_units'])
            return label_tables == pred_tables
        return 1

    def eval_partial_match(self, pred, label):
        res = {}
        # for each component in select, where, group,... calculate total matches -> calculate accuracy, recall, f1 from counts (number of matches)

        label_total, pred_total, cnt, cnt_wo_agg = self.eval_sel(pred, label)
        acc, rec, f1 = self.get_scores(cnt, pred_total, label_total)
        res['select'] = {'acc': acc, 'rec': rec, 'f1': f1,'label_total':label_total,'pred_total':pred_total}
        acc, rec, f1 = self.get_scores(cnt_wo_agg, pred_total, label_total)
        res['select(no AGG)'] = {'acc': acc, 'rec': rec, 'f1': f1,'label_total':label_total,'pred_total':pred_total}

        label_total, pred_total, cnt, cnt_wo_agg = self.eval_where(pred, label)
        acc, rec, f1 = self.get_scores(cnt, pred_total, label_total)
        res['where'] = {'acc': acc, 'rec': rec, 'f1': f1,'label_total':label_total,'pred_total':pred_total}
        acc, rec, f1 = self.get_scores(cnt_wo_agg, pred_total, label_total)
        res['where(no OP)'] = {'acc': acc, 'rec': rec, 'f1': f1,'label_total':label_total,'pred_total':pred_total}

        print(f"Evaluating group by: pred: {pred['groupBy']}, label: {label['groupBy']}")
        label_total, pred_total, cnt = self.eval_group(pred, label)
        print(f"Group by evaluation: label_total: {label_total}, pred_total: {pred_total}, count: {cnt}")
        acc, rec, f1 = self.get_scores(cnt, pred_total, label_total)
        res['group(no Having)'] = {'acc': acc, 'rec': rec, 'f1': f1,'label_total':label_total,'pred_total':pred_total}

        label_total, pred_total, cnt = self.eval_having(pred, label)
        acc, rec, f1 = self.get_scores(cnt, pred_total, label_total)
        res['group'] = {'acc': acc, 'rec': rec, 'f1': f1,'label_total':label_total,'pred_total':pred_total}

        label_total, pred_total, cnt = self.eval_order(pred, label)
        acc, rec, f1 = self.get_scores(cnt, pred_total, label_total)
        res['order'] = {'acc': acc, 'rec': rec, 'f1': f1,'label_total':label_total,'pred_total':pred_total}

        label_total, pred_total, cnt = self.eval_and_or(pred, label)
        acc, rec, f1 = self.get_scores(cnt, pred_total, label_total)
        res['and/or'] = {'acc': acc, 'rec': rec, 'f1': f1,'label_total':label_total,'pred_total':pred_total}

        label_total, pred_total, cnt = self.eval_IUEN(pred, label)
        acc, rec, f1 = self.get_scores(cnt, pred_total, label_total)
        res['IUEN'] = {'acc': acc, 'rec': rec, 'f1': f1,'label_total':label_total,'pred_total':pred_total}

        label_total, pred_total, cnt = self.eval_keywords(pred, label)
        acc, rec, f1 = self.get_scores(cnt, pred_total, label_total)
        res['keywords'] = {'acc': acc, 'rec': rec, 'f1': f1,'label_total':label_total,'pred_total':pred_total}

        return res

    def eval_exec_match(db, p_str, g_str, pred, gold):
        """
        return 1 if the values between prediction and gold are matching
        in the corresponding index. Currently not support multiple col_unit(pairs).
        """
        conn = sqlite3.connect(db)
        cursor = conn.cursor()
        try:
            cursor.execute(p_str)
            p_res = cursor.fetchall()
        except:
            return False

        cursor.execute(g_str)
        q_res = cursor.fetchall()

        def res_map(res, val_units):
            rmap = {}
            for idx, val_unit in enumerate(val_units):
                key = tuple(val_unit[1]) if not val_unit[2] else (val_unit[0], tuple(val_unit[1]), tuple(val_unit[2]))
                rmap[key] = [r[idx] for r in res]
            return rmap

        p_val_units = [unit[1] for unit in pred['select'][1]]
        q_val_units = [unit[1] for unit in gold['select'][1]]
        return res_map(p_res, p_val_units) == res_map(q_res, q_val_units)
    
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

        def norm(val: Any) -> Any:                       # cell normaliser
            if val is None or (isinstance(val, str) and val.strip().upper() == "NULL"):
                return None
            if isinstance(val, (int, float)):            # numeric -> rounded
                return round(float(val), 6) if isinstance(val, float) else val
            if isinstance(val, str):
                # numeric disguised as str?
                try:
                    f = float(val)
                    return round(f, 6) if abs(f - int(f)) >= epsilon else int(round(f))
                except ValueError:
                    pass
                # date formats → ISO
                for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%m/%d/%Y"):
                    try:
                        return datetime.datetime.strptime(val.strip(), fmt).date().isoformat()
                    except ValueError:
                        continue
                return val.strip()                       # generic string
            return val                                   # any other type

        norm_rows: List[Tuple[Any, ...]] = [
            [norm(row[i]) for i in order] for row in rows
        ]

        if not ordered:                                  # stable comparison order
            norm_rows.sort(key=lambda r: tuple("" if x is None else str(x) for x in r))

        return [new_header] + norm_rows

    def eval_exec_match(self, pred_table_file, label_table_file):
        pred_table = json.load(open(pred_table_file, 'r'))
        label_table = json.load(open(label_table_file, 'r'))
        normalized_pred = self.normalize_table(pred_table)
        print(f"Pred table: {normalized_pred}")
        print(f"Label table: {label_table}")
        return normalized_pred == label_table

    def get_scores(self, count, pred_total, label_total):
        """
            Accuracy, recall, F1 only = 1 when all components match (number of matches == total number of (predicted and gold) labels)
        """
        if pred_total != label_total:
            return 0,0,0
        elif count == pred_total:
            return 1,1,1
        return 0,0,0

    def eval_sel(self, pred, label):
        """
            Count number of labels in pred['select'] that are also in label['select']
            Returns total number of labels, total number of predictions, number of matches, and number of matches without aggregation
        """
        pred_sel = pred['select'][1]
        label_sel = label['select'][1]
        label_wo_agg = [unit[1] for unit in label_sel]
        pred_total = len(pred_sel)
        label_total = len(label_sel)
        cnt = 0
        cnt_wo_agg = 0

        for unit in pred_sel:
            if unit in label_sel:
                cnt += 1
                label_sel.remove(unit)
            if unit[1] in label_wo_agg:
                cnt_wo_agg += 1
                label_wo_agg.remove(unit[1])

        return label_total, pred_total, cnt, cnt_wo_agg


    def eval_where(self, pred, label):
        """
            Label conditions are in the form: (not_op, op_id, val_unit, val1, val2)
            Label conditions without aggregation are: val_unit
        """
        pred_conds = [unit for unit in pred['where'][::2]]
        label_conds = [unit for unit in label['where'][::2]]
        label_wo_agg = [unit[2] for unit in label_conds]    # unit.shape: (not_op, op_id, val_unit, val1, val2)
        pred_total = len(pred_conds)
        label_total = len(label_conds)
        cnt = 0
        cnt_wo_agg = 0

        for unit in pred_conds:
            if unit in label_conds:
                cnt += 1
                label_conds.remove(unit)
            if unit[2] in label_wo_agg:
                cnt_wo_agg += 1
                label_wo_agg.remove(unit[2])

        return label_total, pred_total, cnt, cnt_wo_agg


    def eval_group(self, pred, label):
        pred_cols = [unit[1] for unit in pred['groupBy']]
        label_cols = [unit[1] for unit in label['groupBy']]
        pred_total = len(pred_cols)
        label_total = len(label_cols)
        cnt = 0
        pred_cols = [pred.split(".")[1] if "." in pred else pred for pred in pred_cols]
        label_cols = [label.split(".")[1] if "." in label else label for label in label_cols]
        for col in pred_cols:
            if col in label_cols:
                cnt += 1
                label_cols.remove(col)
        return label_total, pred_total, cnt


    def eval_having(self, pred, label):
        """
            The evaluation of having clause is similar to group by, with the addition of checking the having condition.
            Is this fair?
        """
        pred_total = label_total = cnt = 0
        if len(pred['groupBy']) > 0:
            pred_total = 1
        if len(label['groupBy']) > 0:
            label_total = 1

        pred_cols = [unit[1] for unit in pred['groupBy']]
        label_cols = [unit[1] for unit in label['groupBy']]
        if pred_total == label_total == 1 \
                and pred_cols == label_cols \
                and pred['having'] == label['having']:
            cnt = 1

        return label_total, pred_total, cnt


    def eval_order(self, pred, label):
        print(f"Evaluating order by: pred: {pred['orderBy']}, label: {label['orderBy']}")
        pred_total = label_total = cnt = 0
        if len(pred['orderBy']) > 0:
            pred_total = 1
        if len(label['orderBy']) > 0:
            label_total = 1
        print(len(label['orderBy'][1]), len(pred['orderBy'][1]))
        print(pred['orderBy'][1])
        print(label['orderBy'][1])
        if len(label['orderBy'][1]) > 0 and pred['orderBy'][1] == label['orderBy'][1] and \
                ((pred['limit'] is None and label['limit'] is None) or (pred['limit'] is not None and label['limit'] is not None)):
            cnt = 1
        print(f"Order by evaluation: label_total: {label_total}, pred_total: {pred_total}, count: {cnt}")
        return label_total, pred_total, cnt


    def eval_and_or(self, pred, label):
        pred_ao = pred['where'][1::2]
        label_ao = label['where'][1::2]
        pred_ao = set(pred_ao)
        label_ao = set(label_ao)

        if pred_ao == label_ao:
            return 1,1,1
        return len(pred_ao),len(label_ao),0

    def eval_IUEN(self, pred, label):
        lt1, pt1, cnt1 = self.eval_nested(pred['intersect'], label['intersect'])
        lt2, pt2, cnt2 = self.eval_nested(pred['except'], label['except'])
        lt3, pt3, cnt3 = self.eval_nested(pred['union'], label['union'])
        label_total = lt1 + lt2 + lt3
        pred_total = pt1 + pt2 + pt3
        cnt = cnt1 + cnt2 + cnt3
        return label_total, pred_total, cnt

    def get_keywords(self, sql):
        res = set()
        if len(sql['where']) > 0:
            res.add('where')
        if len(sql['groupBy']) > 0:
            res.add('group')
        if len(sql['having']) > 0:
            res.add('having')
        if len(sql['orderBy']) > 0:
            res.update(sql['orderBy'][0])
            res.add('order')
        if sql['limit'] is not None:
            res.add('limit')
        if sql['except'] is not None:
            res.add('except')
        if sql['union'] is not None:
            res.add('union')
        if sql['intersect'] is not None:
            res.add('intersect')

        ao = sql['from']['conds'][1::2] + sql['where'][1::2] + sql['having'][1::2]
        if len([token for token in ao if token == 'or']) > 0:
            res.add('or')

        cond_units = sql['from']['conds'][::2] + sql['where'][::2] + sql['having'][::2]

        if len([cond_unit for cond_unit in cond_units if cond_unit[0]]) > 0:
            res.add('not')

        if len([cond_unit for cond_unit in cond_units if cond_unit[1] == WHERE_OPS.index('in')]) > 0:
            res.add('in')

        if len([cond_unit for cond_unit in cond_units if cond_unit[1] == WHERE_OPS.index('like')]) > 0:
            res.add('like')

        return res

    def eval_keywords(self, pred, label):
        pred_keywords = self.get_keywords(pred)
        label_keywords = self.get_keywords(label)
        pred_total = len(pred_keywords)
        label_total = len(label_keywords)
        cnt = 0

        for k in pred_keywords:
            if k in label_keywords:
                cnt += 1
        return label_total, pred_total, cnt

    def eval_nested(self, pred, label):
        label_total = 0
        pred_total = 0
        cnt = 0
        if pred is not None:
            pred_total += 1
        if label is not None:
            label_total += 1
        if pred is not None and label is not None:
            cnt += Evaluator().eval_exact_match(pred, label)
        return label_total, pred_total, cnt


