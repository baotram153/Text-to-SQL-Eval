import argparse
from refactor.parser import Parser
from lexer import Lexer
from evaluator import Evaluator
from utils import *
from utils.schema import get_schema_from_json
from refactor.nodes import *
import json
import re
# import dash_dangerously_set_inner_html
# from json2tree import convert
import json

# reading dataset
import os
import yaml

# logging
import sys
import logging

# dash
import dash
from dash import Dash, dash_table, html, dcc
import pandas as pd
import dash_ag_grid as dag
import plotly.express as px

logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - In %(funcName)s() - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('benchmark.log', encoding='utf-8')
    ]
)

DATA_ROOT_DIR = os.path.dirname(os.path.abspath(__file__))

def prepare_data_dir():
    data_dir = 'evaluate_data'
    os.makedirs(data_dir, exist_ok=True)

def collect_labels_from_dir(gold_dir):
    pass

def collect_labels_from_yaml(gold_file: str):
    with open(gold_file, 'r', encoding='utf-8') as f:
        gold_data = yaml.safe_load(f)['test_cases']
    gold_list = []
    for item in gold_data:
        assert isinstance(item, dict), "Each item in gold data should be a dictionary"
        query = item['sql'][0]['query'].strip().lower()
        db = item['dataset_id'].strip().lower()
        tc_id = item['id']
        nl = item['question']
        complexity = item.get('complexity', 1)
        assert query and db and tc_id, "Query, database name and testcase ID must not be empty"
        gold_list.append({
            'query': query,
            'db': db,
            'tc_id': tc_id,
            'nl': nl,
            'complexity': complexity
        })
    logger.info(f"Collected {len(gold_list)} gold labels from {gold_file}")
    return gold_list

def collect_pred_from_dir(pred_dir):
    # pred_dir/run_id/result/query.sql
    pred_list = []
    for run_id in sorted(os.listdir(pred_dir)):
        run_path = os.path.join(pred_dir, run_id)
        if not os.path.isdir(run_path):
            continue
        sql_file = os.path.join(run_path, 'result/query.sql')
        sql = ""
        if os.path.exists(sql_file):
            with open(sql_file, 'r', encoding='utf-8') as f:
                lines = [line.strip() for line in f if line.strip() and not line.strip().startswith('--')]
                sql = ' '.join(lines)
        pred_list.append(sql)
    return pred_list

def collect_pred_from_yaml(pred_file):
    pass

def collect_pred_table_from_dir(pred_table_dir):
    pred_list = []
    for run_id in sorted(os.listdir(pred_table_dir)):
        run_dir = os.path.join(pred_table_dir, run_id)
        if not os.path.isdir(run_dir):
            continue
        table_file = os.path.join(run_dir, 'result/data.json')
        if os.path.exists(table_file):
            with open(table_file, 'r', encoding='utf-8') as f:
                table_data = json.load(f)
                pred_list.append(table_data)
        else:
            pred_list.append(None)
    return pred_list

def collect_gt_table_from_dir(gt_table_dir):
    gt_list = []
    if not os.path.isdir(gt_table_dir):
        return gt_list
    for run_id in sorted(os.listdir(gt_table_dir)):
        run_dir = os.path.join(gt_table_dir, run_id)
        if not os.path.isdir(run_dir):
            continue
        table_file = os.path.join(run_dir, 'gt_data_result.json')
        if os.path.exists(table_file):
            with open(table_file, 'r', encoding='utf-8') as f:
                table_data = json.load(f)
                gt_list.append(table_data)
        else:
            gt_list.append(None)
    return gt_list

def init_content_matching():
    return {
        'testcase_id': [],
        'pred_sql': [],
        'gt_sql': [],
        'hardness': [],
        'parsed_gt_sql': [],
        'parsed_pred_sql': [],
        'exact_match': [],
        'component_match': [],
    }

def init_exec_matching():
    return {
        'testcase_id': [],
        'pred_res': [],
        'pred_res_html': [],
        'gt_res': [],
        'gt_res_html': [],
        'norm_pred': [],
        'norm_gt': [],
        'norm_pred_html': [],
        'norm_gt_html': [],
        'complexity': [],
        'is_match': [],
        'info': [],
    }

def format_sql_ast_to_html(tree_str):
    indent_level = 0
    html_lines = []

    def add_line(text, indent_change=0):
        nonlocal indent_level
        if indent_change < 0:
            indent_level += indent_change
        html_lines.append(f"<div style='margin-left: {indent_level * 20}px'>{text.strip()}</div>")
        if indent_change > 0:
            indent_level += indent_change

    # Clean and tokenize
    tree_str = tree_str.replace("\\n", "").strip()
    tokens = re.findall(r'\w+\s*=\s*|[(),\[\]]|[^=\[\],()]+', tree_str)

    stack = []
    i = 0
    while i < len(tokens):
        token = tokens[i].strip()

        if token.endswith('='):
            key = token[:-1].strip()
            next_token = tokens[i + 1].strip()
            if next_token in ['(', '[']:
                add_line(f"{key}=", 1)
                stack.append(next_token)
                i += 1
            else:
                add_line(f"{key}={next_token}")
                i += 1
        elif token in ['(', '[']:
            add_line(token, 1)
            stack.append(token)
        elif token in [')', ']']:
            indent_level -= 1
            add_line(token)
            if stack:
                stack.pop()
        elif token == ',':
            pass  # skip
        else:
            add_line(token)
        i += 1

    return "<div style='font-family:monospace'>" + "\n".join(html_lines) + "</div>"


def sql_ast_to_html(sql_text: str) -> str:
    """Convert a SQL AST string into collapsible HTML tree."""
    def parse_block(value: str) -> str:
        # breakpoint()
        html_str = "<ul>"
        i = 0
        while i < len(value):
            match = re.match(r'([A-Za-z_][A-Za-z0-9_]*)\(', value[i:])
            if match:
                name = match.group(1)
                start = i + len(name) + 1
                bracket_level = 1
                j = start
                while j < len(value) and bracket_level > 0:
                    if value[j] == '(':
                        bracket_level += 1
                    elif value[j] == ')':
                        bracket_level -= 1
                    j += 1
                # breakpoint()
                inner_content = value[start:j - 1]
                html_str += f'<li><details open><summary><b>{name}</b></summary>{parse_block(inner_content)}</details></li>'
                i = j
            else:
                m = re.match(r'\s*([a-zA-Z_][a-zA-Z0-9_]*)\s*=\s*("[^"]*"|[^=,()\[\]]+)', value[i:])
                if m:
                    key = m.group(1)
                    val = m.group(2).strip().strip('"')
                    html_str += f'<li>{key}: {val}</li>'
                    i += m.end()
                else:
                    i += 1
        html_str += "</ul>"
        return html_str

    return parse_block(sql_text)

def dict_to_html_tree(data):
    def build_tree(d):
        html = "<ul>\n"
        for key, value in d.items():
            if isinstance(value, dict):
                # html += f"<li><strong>{key}</strong>{build_tree(value)}</li>\n"
                html += f"<details><summary>{key}</summary>{build_tree(value)}</details>\n"
            else:
                html += f"<li>{key}: {value}</li>\n"
        html += "</ul>\n"
        return html

    return build_tree(data)

def array_to_html_table(array):
    '''
    Converts a 2D array to an HTML table with inline CSS.
    The first row is used as the header.
    '''
    if not array or len(array) == 0:
        return ""

    # Inline styles
    table_style = "border-collapse: collapse; font-family: Arial, sans-serif; font-size: 14px;"
    th_style = "background-color: #f2f2f2; border: 1px solid #000; min-width: 100px;"
    td_style = "border: 1px solid #000; min-width: 100px;"

    html = f'<table border="1" cellspacing="0" style="{table_style}">\n'

    # Header
    header = array[0]
    html += "  <tr>" + "".join(f'<th style="{th_style}">{col}</th>' for col in header) + "</tr>\n"

    # Rows
    for row in array[1:]:
        html += "  <tr>" + "".join(f'<td style="{td_style}">{cell}</td>' for cell in row) + "</tr>\n"

    html += "</table>"
    return html

def convert_to_link(tc_name):

    return f"<a href='/testcases/{tc_name}'>{tc_name}</a>"


def show_content_matching_table(content_matching):
    df = pd.DataFrame(content_matching)
    col_names = {
        'testcase_id': 'Testcase ID',
        'pred_sql': 'Predicted SQL',
        'gt_sql': 'Groundtruth SQL',
        'hardness': 'Hardness',
        'parsed_pred_sql': 'Parsed Prediction SQL',
        'parsed_gt_sql': 'Parsed Groundtruth SQL',
        'exact_match': 'Exact Matching',
        'component_match': 'Component Matching',
    }

    default_col_def = {
        "cellRenderer": "markdown",
        "cellStyle": {
            "textAlign": "left",
            "maxWidth": "400px",
            "maxHeight": "120px",
            "minHeight": "100px",
            "lineHeight": "20px",
            "overflow": "auto",
            "textOverflow": "ellipsis",
            "whiteSpace": "normal",
            "fontFamily": "monospace",
            "display": "block",
        },
        "wrapText": False,
        "autoHeight": False,
    }

    column_defs = [
        {"field": k, "headerName": v}
        for k, v in col_names.items()
    ]

    app = Dash(__name__)

    app.layout = html.Div(
        [
            html.H2("Content Matching Table"),
            dag.AgGrid(
                id="content-match-table",
                rowData=df.to_dict("records"),
                columnDefs=column_defs,
                defaultColDef=default_col_def,
                dashGridOptions={
                    "pagination": True,
                    "paginationPageSize": 20,
                    "rowHeight": 150,
                },
                dangerously_allow_code=True,
                style={
                    'height': 800,
                }
            )
        ],
        style={"margin": "2rem"},
    )

    app.run(debug=True)

def array_to_ag_grid_data(array):
    if not array or len(array) == 0: return {}
    keys = array[0]
    result = {key: [row[i].strip() if i == 0 else row[i] for row in array[1:]] for i, key in enumerate(keys)}
    print(f"Result: {result}")
    return result

def show_exec_matching_table(exec_matching):
    df = pd.DataFrame(exec_matching)
    print(f"Exec matching: {exec_matching}")
    app = Dash(__name__)
    col_names = {
        'testcase_id': 'Testcase ID',
        'pred_res_html': 'Predicted Result',
        'gt_res_html': 'Groundtruth Result',
        'norm_pred_html': 'Normalized Predicted Result',
        'norm_gt_html': 'Normalized Groundtruth Result',
        'complexity': 'Complexity',
        'is_match': 'Is Match',
    }

    default_col_def = {
        "cellRenderer": "markdown",
        "cellStyle": {
            "textAlign": "left",
            "maxWidth": "600px",
            "maxHeight": "120px",
            "minHeight": "100px",
            "lineHeight": "40px",
            "overflow": "auto",
            "textOverflow": "ellipsis",
            "whiteSpace": "normal",
            "fontFamily": "monospace",
            "display": "block",
        },
        "wrapText": False,
        "autoHeight": False,
    }

    column_defs = [
        {"field": k, "headerName": v, "maxWidth": 600, "minWidth": 300 if 'res' in k or 'norm' in k else 200,}
        for k, v in col_names.items()
    ]

    total = exec_matching.get('total', 0)
    total_match = exec_matching.get('total_match', 0)

    df['complexity'] = df['complexity'].astype(str)
    unique_complexities = sorted(df['complexity'].unique(), key=lambda x: int(x))
    full_complexity_range = [str(i) for i in range(1, 6)]

    complexity_hist = px.histogram(
        df,
        x="complexity",
        color="is_match",
        category_orders={"complexity": full_complexity_range},
        labels={"is_match": "Is match?"}
    )
    main_table = []

    print(f"Row data: {df.to_dict("records")}")

    all_testcase_table = dag.AgGrid(
                id="content-match-table",
                rowData=df.to_dict("records"),
                columnDefs=column_defs,
                defaultColDef=default_col_def,
                dashGridOptions={
                    "pagination": True,
                    "paginationPageSize": 20,
                    "rowHeight": 150,
                },
                dangerously_allow_code=True,
                style={
                    'height': 800,
                    "width": "100%",
                    "margin": "20px auto"
                }
            )

    main_page_content = [html.H1("Execution Matching Table"),
            html.Div([
                html.B("Total Testcases: "), str(total),
                html.Br(),
                html.B("Total Matches: "), str(total_match),
                html.Br(),
                html.B("Match Rate: "), f"{(total_match/total*100 if total else 0):.2f}%"
            ], style={"marginBottom": "1rem", "fontSize": "1.2rem"}),
            html.H2("Number of Testcases per Complexity", style={"textAlign": "center"}),
            html.Div([
                dcc.Graph(figure=complexity_hist)
            ], style={"marginBottom": "2rem"}),
            html.H2("Full Testcase Table", style={"textAlign": "center"}),
            all_testcase_table,
            dcc.Store(id="selected-row-store"),
            html.Div(id="testcase-detail", style={"marginTop": "2rem", "fontFamily": "monospace", "fontSize": "1.1rem"}),
    ]

    app.layout = html.Div(
        [
            dcc.Location(id='url', refresh=False),
            html.Div(id='page-content')
        ],
        style={"margin": "2rem"},
    )

    # @app.callback(
    #     dash.Output("testcase-detail", "children"),
    #     dash.Input("content-match-table", "selectedRows"),
    # )
    # def display_testcase_detail(selected_rows):
    #     if not selected_rows:
    #         return "Click a testcase_id to see details."
    #     row = selected_rows[0]
    #     return html.Pre(json.dumps(row, indent=2, ensure_ascii=False))
    
    @app.callback(
            dash.Output('page-content', 'children'),
            dash.Input('url', 'pathname'))
    def display_page(pathname):
        if pathname and pathname.startswith('/testcases/'):
            testcase_id = pathname.split('/testcases/')[1]
            row = df[df['testcase_id'] == f"<a href='/testcases/{testcase_id}'>{testcase_id}</a>"]
            print(f"Is match: {row.iloc[0]['is_match']}")
            if not row.empty:
                info = row.iloc[0]['info']
                row_data = pd.DataFrame(array_to_ag_grid_data(row.iloc[0]['pred_res'])).to_dict("records")
                print(row_data)
                return html.Div([
                    html.H2(f"Testcase {testcase_id}"),
                    html.H3("Predicted table"),
                    dag.AgGrid(
                        id="content-match-table",
                        rowData=pd.DataFrame(array_to_ag_grid_data(row.iloc[0]['pred_res'])).to_dict("records"),
                        columnDefs=[
                            {"field": k, "headerName": k}
                            for k in row.iloc[0]['pred_res'][0]
                        ],
                        defaultColDef=default_col_def,
                        dashGridOptions={
                            "pagination": True,
                            "paginationPageSize": 10,
                            "rowSelection": "single",
                        },
                        dangerously_allow_code=True,
                        style={"display": "inline-block"}
                    ),
                    html.H3("Groundtruth table"),
                    dag.AgGrid(
                        id="content-match-table",
                        rowData=pd.DataFrame(array_to_ag_grid_data(row.iloc[0]['gt_res'])).to_dict("records"),
                        columnDefs=[
                            {"field": k, "headerName": k}
                            for k in row.iloc[0]['gt_res'][0]
                        ],
                        defaultColDef=default_col_def,
                        dashGridOptions={
                            "pagination": True,
                            "paginationPageSize": 10,
                            "rowSelection": "single",
                        },
                        dangerously_allow_code=True,
                    ),
                    html.H3("Normalized predicted table"),
                    dag.AgGrid(
                        id="content-match-table",
                        rowData=pd.DataFrame(array_to_ag_grid_data(row.iloc[0]['norm_pred'])).to_dict("records"),
                        columnDefs=[
                            {"field": k, "headerName": k}
                            for k in row.iloc[0]['norm_pred'][0]
                        ],
                        defaultColDef=default_col_def,
                        dashGridOptions={
                            "pagination": True,
                            "paginationPageSize": 10,
                            "rowSelection": "single",
                        },
                        dangerously_allow_code=True,
                    ),
                    html.H3("Normalize groundtruth table"),
                    dag.AgGrid(
                        id="content-match-table",
                        rowData=pd.DataFrame(array_to_ag_grid_data(row.iloc[0]['norm_gt'])).to_dict("records"),
                        columnDefs=[
                            {"field": k, "headerName": k}
                            for k in row.iloc[0]['norm_gt'][0]
                        ],
                        defaultColDef=default_col_def,
                        dashGridOptions={
                            "pagination": True,
                            "paginationPageSize": 10,
                            "rowSelection": "single",
                        },
                        dangerously_allow_code=True,
                    ),
                    html.H3("Result"),
                    html.Div("Match" if row.iloc[0]['is_match'] else "Not match"),
                    html.H3("Info"),
                    html.Div(row.iloc[0]['info']),
                ])
            else:
                return html.Div("Testcase not found.")
        return main_page_content

    app.run(debug=True)

def evaluate(gold_sql_file, table_json, etype, kmaps, pred_sql_dir=None, gold_res_dir=None, pred_res_dir=None):
    evaluator = Evaluator()
    rebuilder = Rebuilder()
    visualizer = Visualizer()

    pred_sql_dir = pred_sql_dir or os.getenv('TEST_AQUA_BENCHMARK_DIRECTORY')
    gold_res_dir = gold_res_dir or os.getenv('TEST_AQUA_BENCHMARK_DIRECTORY')
    pred_res_dir = pred_res_dir or os.getenv('TEST_AQUA_BENCHMARK_DIRECTORY')

    logger.info(f"Using gold SQL file: {gold_sql_file}, pred SQL directory: {pred_sql_dir}, gold result directory: {gold_res_dir}, pred result directory: {pred_res_dir}")


    prepare_data_dir()

    glist = collect_labels_from_yaml(gold_sql_file)
    plist = collect_pred_from_dir(pred_dir=os.getenv('TEST_AQUA_BENCHMARK_DIRECTORY', pred_sql_dir))

    # breakpoint()

    levels = ['easy', 'medium', 'hard', 'extra', 'all']
    partial_types = ['select', 'select(no AGG)', 'where', 'where(no OP)', 'group(no Having)',
                     'group', 'order', 'and/or', 'IUEN', 'keywords']
    entries = []
    scores = {}
    content_matching_dict = init_content_matching()
    exec_matching_dict = init_exec_matching()

    for level in levels:
        scores[level] = {'count': 0, 'partial': {}, 'exact': 0.}
        scores[level]['exec'] = 0
        for type_ in partial_types:
            scores[level]['partial'][type_] = {'acc': 0., 'rec': 0., 'f1': 0.,'acc_count':0,'rec_count':0}

    eval_err_num = 0
    logger.info(f"Evaluating {len(plist)} predictions against {len(glist)} ground truths")
    for idx, (p, g) in enumerate(zip(plist, glist)):
        p_str = p
        tc_id, g_str, db_name, nl, complexity = g['tc_id'], g['query'], g['db'], g['nl'], g['complexity']  # get  schema name for future extension
        schema_name, schema = get_schema_from_json(table_json)
        schema = Schema(schema, schema_name)
        try:
            g_parser = Parser(lexer=Lexer(g_str, schema=schema), schema=schema)
            g_sql = g_parser.parse()
            logger.info(f"Parsed Gold SQL: {g_sql}")
        except Exception as e:
            g_sql = Sql()
            eval_err_num += 1

        # hardness = HardnessEvaluator(g_sql).eval_hardness()
        hardness = 'easy'
        scores[hardness]['count'] += 1
        scores['all']['count'] += 1

        try:
            p_parser = Parser(lexer=Lexer(p_str, schema=schema), schema=schema)
            p_sql = p_parser.parse()
        except:
            # if p_sql is not valid, then we will use an empty sql to evaluate with the correct sql
            p_sql = Sql()

        visualizer.print_to_file('SQL String', g_str, p_str)
        visualizer.print_to_file('SQL Dict', g_sql, p_sql)


        # # rebuild sql for value evaluation
        # kmap = kmaps[db_name]
        # g_valid_col_units = rebuilder.build_valid_col_units(g_sql['from']['table_units'], schema)
        # g_sql = rebuilder.rebuild_sql_val(g_sql)
        # g_sql = rebuilder.rebuild_sql_col(g_valid_col_units, g_sql, kmap)
        # p_valid_col_units = rebuilder.build_valid_col_units(p_sql['from']['table_units'], schema)
        # p_sql = rebuilder.rebuild_sql_val(p_sql)
        # p_sql = rebuilder.rebuild_sql_col(p_valid_col_units, p_sql, kmap)

        pred_tables = collect_pred_table_from_dir(pred_res_dir)
        gt_tables = collect_gt_table_from_dir(gold_res_dir)

        logger.debug(f"Predicted tables: {pred_tables}")
        logger.debug(f"Ground truth tables: {gt_tables}")

        if etype in ["all", "match"]:
            print(f"Etype in match")
            partial_scores, exact_match = evaluator.eval_partial_match(p_sql, g_sql)
            # breakpoint()
            # scores[hardness]['exact'] += exact_score
            # scores['all']['exact'] += exact_score
            # for type_ in partial_types:
            #     scores[hardness]['partial'][type_]['acc'] += partial_scores[type_].get('acc', 0)
            #     scores[hardness]['partial'][type_]['acc_count'] += partial_scores[type_].get('acc_count', 0)
            #     scores[hardness]['partial'][type_]['rec'] += partial_scores[type_].get('rec', 0)
            #     scores[hardness]['partial'][type_]['rec_count'] += partial_scores[type_].get('rec_count', 0)
            #     scores[hardness]['partial'][type_]['f1'] += partial_scores[type_].get('f1', 0)
            #     scores['all']['partial'][type_]['acc'] += partial_scores[type_].get('acc', 0)
            #     scores['all']['partial'][type_]['acc_count'] += partial_scores[type_].get('acc_count', 0)
            #     scores['all']['partial'][type_]['rec'] += partial_scores[type_].get('rec', 0)
            #     scores['all']['partial'][type_]['rec_count'] += partial_scores[type_].get('rec_count', 0)
            #     scores['all']['partial'][type_]['f1'] += partial_scores[type_].get('f1', 0)

            for key, value in [
                ('testcase_id', tc_id),
                ('pred_sql', p_str),
                ('gt_sql', g_str),
                ('hardness', hardness),
                ('parsed_gt_sql', format_sql_ast_to_html(str(g_sql))),
                ('parsed_pred_sql', format_sql_ast_to_html(str(p_sql))),
                # ('parsed_gt_sql', str(g_sql)),
                # ('parsed_pred_sql', str(p_sql))
                ('exact_match', exact_match),
                # ('component_match', json.dumps(partial_scores, indent=2)),
                ('component_match', dict_to_html_tree(partial_scores)),
            ]:
                content_matching_dict[key].append(value)

            # entries.append({
            #     'predictSQL': p_str,
            #     'goldSQL': g_str,
            #     'hardness': hardness,
            #     'exact': 1,
            #     'partial': 1
            # })
            logger.info(f"Content matching table: {content_matching_dict}")

        if etype in ["all", "exec"]:
            exec_score, norm_pred, norm_gt, info = evaluator.eval_exec_match(pred_tables[idx], gt_tables[idx], nl)
            # if exec_score:
            #     scores[hardness]['exec'] += 1.0
            #     scores['all']['exec'] += 1.0

            for k, v in [
                ('testcase_id', convert_to_link(tc_id)),
                ('pred_res', pred_tables[idx]),
                ('gt_res', gt_tables[idx]),
                ('pred_res_html', array_to_html_table(pred_tables[idx])),
                ('gt_res_html', array_to_html_table(gt_tables[idx])),
                ('norm_pred', norm_pred),
                ('norm_gt', norm_gt),
                ('norm_pred_html', array_to_html_table(norm_pred)),
                ('norm_gt_html', array_to_html_table(norm_gt)),
                ('complexity', complexity),
                ('is_match', exec_score),
                ('info', info)
            ]:
                exec_matching_dict[k].append(v)

    for level in levels:
        if scores[level]['count'] == 0:
            continue
        if etype in ["all", "exec"]:
            scores[level]['exec'] /= scores[level]['count']

        # if etype in ["all", "match"]:
        #     scores[level]['exact'] /= scores[level]['count']
        #     for type_ in partial_types:
        #         if scores[level]['partial'][type_]['acc_count'] == 0:
        #             scores[level]['partial'][type_]['acc'] = 0
        #         else:
        #             scores[level]['partial'][type_]['acc'] = scores[level]['partial'][type_]['acc'] / \
        #                                                      scores[level]['partial'][type_]['acc_count'] * 1.0
        #         if scores[level]['partial'][type_]['rec_count'] == 0:
        #             scores[level]['partial'][type_]['rec'] = 0
        #         else:
        #             scores[level]['partial'][type_]['rec'] = scores[level]['partial'][type_]['rec'] / \
        #                                                      scores[level]['partial'][type_]['rec_count'] * 1.0
        #         if scores[level]['partial'][type_]['acc'] == 0 and scores[level]['partial'][type_]['rec'] == 0:
        #             scores[level]['partial'][type_]['f1'] = 0
        #         else:
        #             scores[level]['partial'][type_]['f1'] = \
        #                 2.0 * scores[level]['partial'][type_]['acc'] * scores[level]['partial'][type_]['rec'] / (
        #                 scores[level]['partial'][type_]['rec'] + scores[level]['partial'][type_]['acc'])

    visualizer.write_scores_to_terminal(scores=scores, etype=etype)
    visualizer.write_scores_to_file(scores=scores, etype=etype)
    if etype in ["match"]:
        show_content_matching_table(content_matching_dict)
    elif etype in ["exec"]:
        exec_matching_dict['total'] = len(exec_matching_dict['testcase_id'])
        exec_matching_dict['total_match'] = sum(exec_matching_dict['is_match'])
        show_exec_matching_table(exec_matching_dict)
if __name__ == "__main__":

    parser = argparse.ArgumentParser()
    parser.add_argument('--gold_sql', dest='gold_sql', type=str)
    parser.add_argument('--pred_sql', dest='pred_sql', type=str)
    parser.add_argument('--gold_res', dest='gold_res', type=str)
    parser.add_argument('--pred_res', dest='pred_res', type=str)

    parser.add_argument('--table', dest='table', type=str)
    parser.add_argument('--etype', dest='etype', type=str)
    args = parser.parse_args()

    gold_sql_file = args.gold_sql
    pred_sql_dir = args.pred_sql
    gold_res_dir = args.gold_res
    pred_res_dir = args.pred_res

    table = args.table
    etype = args.etype

    assert etype in ["all", "exec", "match"], "Unknown evaluation method"

    kmaps = Rebuilder().build_foreign_key_map_from_json(table)

    evaluate(gold_sql_file, table, etype, kmaps, pred_sql_dir, gold_res_dir, pred_res_dir)