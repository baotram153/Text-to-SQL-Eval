from nltk.tokenize import word_tokenize
from utils.schema import Schema
from utils.constants import *
from copy import deepcopy

class Lexer:
    def __init__(self, string, schema: Schema = None):
        self._string = string
        self._schema = schema
        self._type_dict = []
        self._toks = self.tokenize()
        self._alias_tables = self.scan_alias()

    @property
    def toks(self):
        return self._toks

    def tokenize(self):
        """
        Tokenize the input SQL string, preserving quoted strings as single tokens and handling operators like !=, >=, <=.
        Returns a list of tokens (all lowercased, except quoted strings).
        """
        s = str(self._string)
        s = s.replace("'", '"')  # unify quotes
        quote_idxs = [idx for idx, char in enumerate(s) if char == '"']
        assert len(quote_idxs) % 2 == 0, "Unexpected quote"

        vals = {}
        s_work = s

        # handle quotes (heuristic):
        # - elimiate quotes for single word values (handle column/table names with quotes)
        # - otherwise, handle all words in quotes as single token
        for i in range(len(quote_idxs) - 1, 0, -2):
            qidx1 = quote_idxs[i-1]
            qidx2 = quote_idxs[i]
            val = s[qidx1:qidx2+1]
            key = f"__val_{qidx1}_{qidx2}__"
            s_work = s_work[:qidx1] + key + s_work[qidx2+1:]
            vals[key] = val
            print(f"Extracted value: {val} as key: {key}")

        # tokenize (lowercase except for value placeholders)
        print(f"Vals: {vals}")
        print(f"Keywords: {KEYWORDS}")
        toks = [word.lower() for word in word_tokenize(s_work)]
        for i, tok in enumerate(toks):
            if tok in vals:
                toks[i] = vals[tok]  # restore quoted value
                print(f"Tokenized: {tok} -> {toks[i]}")

        # merge operators (!=, >=, <=)
        i = 1
        while i < len(toks):
            if toks[i] == '=' and toks[i-1] in ('!', '>', '<'):
                toks[i-1] = toks[i-1] + '='
                del toks[i]
            # if the token starts with schema name, remove it
            elif toks[i].startswith(f"{self._schema._name.lower()}."):
                toks[i] = toks[i].split('.', 1)[1]
                i += 1
            else:
                i += 1

        for tok in toks:
            if tok in KEYWORDS:
                self._type_dict.append('kw')
            else:
                self._type_dict.append('id')
        print(f"Tokens after tokenized: {toks}")

        return toks

    def scan_alias(self):
        '''
        Create a dict with alias as key and table/column name as value
        e.g. {'c': 'city', 'co': 'country', ...}
        TODO: Only table alias is used downstream, should we remove column alias?
        '''
        alias = {}
        print(f"Tokens: {self.toks}")
        print(f"Type dict: {self._type_dict}")

        for idx in range(len(self.toks) - 2, -1, -1):
            if self.toks[idx] == 'as':
                print(f"Found alias: {self.toks[idx+1]} -> {self.toks[idx-1]}")
                # remove quotes from alias/table names
                self.toks[idx-1] = self._check_quote_in_name(self.toks[idx-1])
                self.toks[idx+1] = self._check_quote_in_name(self.toks[idx+1])
                # add alias to dict
                alias[self.toks[idx+1]] = self.toks[idx-1]
            if (self._type_dict[idx] == self._type_dict[idx + 1] == 'id'
                and self.toks[idx]   not in ('(', ')', ',')
                and self.toks[idx+1] not in ('(', ')', ',')):
                self.toks[idx] = self._check_quote_in_name(self.toks[idx])
                self.toks[idx + 1] = self._check_quote_in_name(self.toks[idx + 1])
                # add alias to dict
                alias[self.toks[idx + 1]] = self.toks[idx]

                print(f"Removing alias: {self.toks[idx+1]} -> {self.toks[idx]}")
                self.toks.pop(idx + 1)
                self._type_dict.pop(idx + 1)
        return alias

    def get_merged_alias_table(self, schema: Schema) -> dict:
        """ Merge detected alias with real table names so every alias found downstream can be resolved via
        `merged_alias_table[alias]`.

        :returns: dict with alias as key and table/column name as value
        """
        for key in schema.schema_dict:
            assert key not in self._alias_tables, "Alias {} has the same name in table".format(key)
            self._alias_tables[key] = key
        print(f"Alias tables: {self._alias_tables}")

        # remove quotes from alias names
        for tok in self.toks:
            if tok in self._alias_tables.keys():
                self._alias_tables[tok] = self._check_quote_in_name(self._alias_tables[tok])
        return self._alias_tables

    def _check_quote_in_name(self, name: str) -> str:
        """ Check if the name has quotes and remove them if so. """
        if (name.startswith('"') and name.endswith('"')) or (name.startswith("'") and name.endswith("'")):
            return name[1:-1]
        return name