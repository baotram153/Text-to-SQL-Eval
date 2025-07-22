import argparse
from parser import Parser
from lexer import Lexer
from evaluator import Evaluator
from utils import *
from utils.schema import get_schema_from_json
import os
import yaml

DATA_ROOT_DIR = os.path.dirname(os.path.abspath(__file__))

def prepare_data_dir():
    data_dir = 'evaluate_data'
    os.makedirs(data_dir, exist_ok=True)

def collect_labels_from_dir(gold_dir):
    pass

def collect_labels_from_yaml(gold_file: str):
    with open(gold_file, 'r', encoding='utf-8') as f:
        gold_data = yaml.safe_load(f)
    gold_list = []
    for item in gold_data:
        if isinstance(item, dict) and 'query' in item and 'dataset_uname' in item:
            query = item['sql'].strip().lower()
            db = item['dataset_uname'].strip().lower()
            if query and db:
                gold_list.append((query, db))
    return gold_list

def collect_pred_from_dir(pred_dir):
    # pred_dir/run_id/result/query.sql
    pred_list = []
    for root, dirnames, _ in os.walk(pred_dir):
        for run_id in sorted(dirnames):
            sql_file = os.path.join(root, run_id, 'result/query.sql')
            if os.path.exists(sql_file):
                with open(sql_file, 'r', encoding='utf-8') as f:
                    # skip sql comments and empty lines
                    lines = []
                    for line in f:
                        line = line.strip()
                        if not line or line.startswith('--'):
                            continue
                        lines.append(line)
                    pred_sql = ' '.join(lines)
                    if pred_sql:
                        pred_list.append(pred_sql)
                    else:
                        pred_list.append(None)
            else:
                pred_list.append(None)
    return pred_list

def collect_pred_from_yaml(pred_file):
    pass

def evaluate(gold, predict_dir, pred_table_file, label_table_file, table_json, db_dir, etype, kmaps):
    evaluator = Evaluator()
    rebuilder = Rebuilder()

    # prepare_data_dir()
    # glist = collect_labels_from_yaml(gold)
    # plist = collect_pred_from_dir(pred_dir=os.getenv('TEST_AQUA_BENCHMARK_DIRECTORY', predict_dir))
    
    with open(gold, 'r', encoding='utf-8') as f:
        # glist = f.readlines()
        glist = ' '.join(f.readlines())
    
    with open(predict_dir, 'r', encoding='utf-8') as f:
        plist = ' '.join(f.readlines())
    
    glist = [glist]
    plist = [plist]
    print(glist)
    print(plist)

    levels = ['easy', 'medium', 'hard', 'extra', 'all']
    partial_types = ['select', 'select(no AGG)', 'where', 'where(no OP)', 'group(no Having)',
                     'group', 'order', 'and/or', 'IUEN', 'keywords']
    entries = []
    scores = {}

    for level in levels:
        scores[level] = {'count': 0, 'partial': {}, 'exact': 0.}
        scores[level]['exec'] = 0
        for type_ in partial_types:
            scores[level]['partial'][type_] = {'acc': 0., 'rec': 0., 'f1': 0.,'acc_count':0,'rec_count':0}

    eval_err_num = 0
    for p, g in zip(plist, glist):
        p_str = p
        g_str = g
        # db_name = db
        # db = os.path.join(db_dir, db, db + ".sqlite")
        schema_name, schema = get_schema_from_json(table_json)
        schema = Schema(schema, schema_name)  # Example schema, replace with actual schema loading
        print(f"g_str: {g_str}, p_str: {p_str}")
        g_parser = Parser(lexer=Lexer(g_str, schema=schema), schema=schema)
        g_sql = g_parser.parse()
        
        hardness = HardnessEvaluator(g_sql).eval_hardness()
        scores[hardness]['count'] += 1
        scores['all']['count'] += 1

        # try:
        #     p_parser = Parser(lexer=Lexer(p_str, schema=schema), schema=schema)
        #     p_sql = p_parser.parse()
        # except:
        #     # If p_sql is not valid, then we will use an empty sql to evaluate with the correct sql
        #     p_sql = {
        #     "except": None,
        #     "from": {
        #         "conds": [],
        #         "table_units": []
        #     },
        #     "groupBy": [],
        #     "having": [],
        #     "intersect": None,
        #     "limit": None,
        #     "orderBy": [],
        #     "select": [
        #         False,
        #         []
        #     ],
        #     "union": None,
        #     "where": []
        #     }
        #     eval_err_num += 1
        #     print("eval_err_num:{}".format(eval_err_num))

        p_parser = Parser(lexer=Lexer(p_str, schema=schema), schema=schema)
        p_sql = p_parser.parse()

        print(f"g_sql: {g_sql}, p_sql: {p_sql}")

        # rebuild sql for value evaluation
        # kmap = kmaps[db_name]
        kmap = kmaps['car_retails']
        g_valid_col_units = rebuilder.build_valid_col_units(g_sql['from']['table_units'], schema)
        g_sql = rebuilder.rebuild_sql_val(g_sql)
        g_sql = rebuilder.rebuild_sql_col(g_valid_col_units, g_sql, kmap)
        p_valid_col_units = rebuilder.build_valid_col_units(p_sql['from']['table_units'], schema)
        p_sql = rebuilder.rebuild_sql_val(p_sql)
        p_sql = rebuilder.rebuild_sql_col(p_valid_col_units, p_sql, kmap)

        if etype in ["all", "exec"]:
            # exec_score = evaluator.eval_exec_match(db, p_str, g_str, p_sql, g_sql)
            exec_score = evaluator.eval_exec_match(pred_table_file, label_table_file)
            print(exec_score)
            if exec_score:
                scores[hardness]['exec'] += 1.0
                scores['all']['exec'] += 1.0

        if etype in ["all", "match"]:
            exact_score = evaluator.eval_exact_match(p_sql, g_sql)
            partial_scores = evaluator.partial_scores
            if exact_score == 0:
                print("{} pred: {}".format(hardness,p_str))
                print("{} gold: {}".format(hardness,g_str))
                print("")
            scores[hardness]['exact'] += exact_score
            scores['all']['exact'] += exact_score
            for type_ in partial_types:
                if partial_scores[type_]['pred_total'] > 0:
                    scores[hardness]['partial'][type_]['acc'] += partial_scores[type_]['acc']
                    scores[hardness]['partial'][type_]['acc_count'] += 1
                if partial_scores[type_]['label_total'] > 0:
                    scores[hardness]['partial'][type_]['rec'] += partial_scores[type_]['rec']
                    scores[hardness]['partial'][type_]['rec_count'] += 1
                scores[hardness]['partial'][type_]['f1'] += partial_scores[type_]['f1']
                if partial_scores[type_]['pred_total'] > 0:
                    scores['all']['partial'][type_]['acc'] += partial_scores[type_]['acc']
                    scores['all']['partial'][type_]['acc_count'] += 1
                if partial_scores[type_]['label_total'] > 0:
                    scores['all']['partial'][type_]['rec'] += partial_scores[type_]['rec']
                    scores['all']['partial'][type_]['rec_count'] += 1
                scores['all']['partial'][type_]['f1'] += partial_scores[type_]['f1']

            entries.append({
                'predictSQL': p_str,
                'goldSQL': g_str,
                'hardness': hardness,
                'exact': exact_score,
                'partial': partial_scores
            })

    for level in levels:
        if scores[level]['count'] == 0:
            continue
        if etype in ["all", "exec"]:
            scores[level]['exec'] /= scores[level]['count']

        if etype in ["all", "match"]:
            scores[level]['exact'] /= scores[level]['count']
            for type_ in partial_types:
                if scores[level]['partial'][type_]['acc_count'] == 0:
                    scores[level]['partial'][type_]['acc'] = 0
                else:
                    scores[level]['partial'][type_]['acc'] = scores[level]['partial'][type_]['acc'] / \
                                                             scores[level]['partial'][type_]['acc_count'] * 1.0
                if scores[level]['partial'][type_]['rec_count'] == 0:
                    scores[level]['partial'][type_]['rec'] = 0
                else:
                    scores[level]['partial'][type_]['rec'] = scores[level]['partial'][type_]['rec'] / \
                                                             scores[level]['partial'][type_]['rec_count'] * 1.0
                if scores[level]['partial'][type_]['acc'] == 0 and scores[level]['partial'][type_]['rec'] == 0:
                    scores[level]['partial'][type_]['f1'] = 0
                else:
                    scores[level]['partial'][type_]['f1'] = \
                        2.0 * scores[level]['partial'][type_]['acc'] * scores[level]['partial'][type_]['rec'] / (
                        scores[level]['partial'][type_]['rec'] + scores[level]['partial'][type_]['acc'])

    Visualizer(etype, scores).print_scores()
    
if __name__ == "__main__":

    parser = argparse.ArgumentParser()
    parser.add_argument('--gold', dest='gold', type=str)
    parser.add_argument('--pred', dest='pred', type=str)
    parser.add_argument('--db', dest='db', type=str)
    parser.add_argument('--table', dest='table', type=str)
    parser.add_argument('--etype', dest='etype', type=str)
    parser.add_argument('--pred_table', dest='pred_table', type=str, default='mocked_data/pred_res.json')
    parser.add_argument('--label_table', dest='label_table', type=str, default='mocked_data/label_res.json')
    args = parser.parse_args()

    # gold = args.gold
    # pred = args.pred
    gold_dir = args.gold
    pred_dir = args.pred
    pred_table_file = args.pred_table
    label_table_file = args.label_table
    db_dir = args.db
    table = args.table
    etype = args.etype

    assert etype in ["all", "exec", "match"], "Unknown evaluation method"

    kmaps = Rebuilder().build_foreign_key_map_from_json(table)

    evaluate(gold_dir, pred_dir, pred_table_file, label_table_file, table, db_dir, etype, kmaps)