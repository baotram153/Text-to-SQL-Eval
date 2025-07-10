import json
import sqlite3
from typing import Dict, List

class Schema:
    """
    Simple schema which maps each column from each table to a unique identifier
    """
    def __init__(self, schema, name):
        self._schema: Dict[str, List[str]] = schema
        self._idMap = self._map(self._schema)
        self._name = name

    @property
    def schema_dict(self):
        return self._schema

    @property
    def idMap(self):
        return self._idMap

    def _map(self, schema):
        '''
        Map schema to a dict with key as table.column and value as unique identifier
        e.g.
        {
            '*': '__all__',
            'city.id': '__city.id__',
            'city.name': '__city.name__', ...
        }
        
        '''
        idMap = {'*': "__all__"}
        id = 1
        for key, vals in schema.items():
            for val in vals:
                idMap[key.lower() + "." + val.lower()] = "__" + key.lower() + "." + val.lower() + "__"
                id += 1

        for key in schema:
            idMap[key.lower()] = "__" + key.lower() + "__"
            id += 1

        return idMap


def get_schema(db):
    """
    Get database's schema, which is a dict with table name as key
    and list of column names as value
    {table_name: [col1, col2, ...], ...}
    :param db: database path
    :return: schema dict
    """

    schema = {}
    conn = sqlite3.connect(db)
    cursor = conn.cursor()

    # fetch table names
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = [str(table[0].lower()) for table in cursor.fetchall()]

    # fetch table info
    for table in tables:
        cursor.execute("PRAGMA table_info({})".format(table))
        schema[table] = [str(col[1].lower()) for col in cursor.fetchall()]

    return schema


def get_schema_from_json(fpath):
    """Return a dict with table name as key and list of column names as value
    """
    # with open(fpath) as f:
    #     data = json.load(f)

    # schema = {}
    # for entry in data:
    #     table = str(entry['table'].lower())
    #     cols = [str(col['column_name'].lower()) for col in entry['col_data']]
    #     schema[table] = cols
    with open(fpath, 'r', encoding='utf-8') as f:
        tables = json.load(f)[0]
    schema_name = tables['db_id']
    schema = {}
    for idx, table in enumerate(tables['table_names']):
        schema[table.lower()] = []
        for col in tables['column_names']:
            if col[0] == idx:
                schema[table.lower()].append(col[1].lower())

    print(f"Schema loaded from {fpath}: {schema}")

    return schema_name, schema