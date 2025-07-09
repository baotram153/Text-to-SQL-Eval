from nltk.tokenize import word_tokenize
from utils.schema import Schema

class Lexer:
    def __init__(self, string):
        self._string = string
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

        # Extract quoted values and replace with placeholders
        vals = {}
        s_work = s
        for i in range(len(quote_idxs) - 1, 0, -2):
            qidx1 = quote_idxs[i-1]
            qidx2 = quote_idxs[i]
            val = s[qidx1:qidx2+1]
            key = f"__val_{qidx1}_{qidx2}__"
            s_work = s_work[:qidx1] + key + s_work[qidx2+1:]
            vals[key] = val

        # Tokenize (lowercase except for value placeholders)
        toks = [word.lower() for word in word_tokenize(s_work)]
        for i, tok in enumerate(toks):
            if tok in vals:
                toks[i] = vals[tok]  # restore quoted value

        # Merge operators (!=, >=, <=)
        i = 1
        while i < len(toks):
            if toks[i] == '=' and toks[i-1] in ('!', '>', '<'):
                toks[i-1] = toks[i-1] + '='
                del toks[i]
            else:
                i += 1
        return toks
    
    def scan_alias(self):
        '''
        Create a dict with alias as key and table/column name as value
        e.g. {'c': 'city', 'co': 'country', ...}
        TODO: Only table alias is used downstream, should we remove column alias?
        '''
        as_idxs = [idx for idx, tok in enumerate(self.toks) if tok == 'as']
        alias = {}
        for idx in as_idxs:
            alias[self.toks[idx+1]] = self.toks[idx-1]
        return alias
    
    def get_merged_alias_table(self, schema: Schema) -> dict:
        """ Merge detected alias with real table names so every alias found downstream can be resolved via 
        `merged_alias_table[alias]`.
        
        :returns: dict with alias as key and table/column name as value
        """
        for key in schema.schema_dict:
            assert key not in self._alias_tables, "Alias {} has the same name in table".format(key)
            self._alias_tables[key] = key
        return self._alias_tables