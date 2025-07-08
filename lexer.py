from nltk.tokenize import word_tokenize
from utils.schema import Schema

class Lexer:
    def __init__(self, string):
        self._string = string
        self._toks = self.tokenize(string)
        self._alias_tables = self.scan_alias()   
        
    @property
    def toks(self):
        return self._toks
    
    def tokenize(string):
        string = str(string)
        string = string.replace("\'", "\"")     # ensure all strings are wrapped in double quotes instead of single quotes
        quote_idxs = [idx for idx, char in enumerate(string) if char == '"']
        assert len(quote_idxs) % 2 == 0, "Unexpected quote"

        # keep string value as token
        vals = {}
        for i in range(len(quote_idxs)-1, -1, -2):
            qidx1 = quote_idxs[i-1]
            qidx2 = quote_idxs[i]
            val = string[qidx1: qidx2+1]
            key = "__val_{}_{}__".format(qidx1, qidx2)
            string = string[:qidx1] + key + string[qidx2+1:]
            vals[key] = val

        toks = [word.lower() for word in word_tokenize(string)]
        # replace with string value token
        for i in range(len(toks)):
            if toks[i] in vals:
                toks[i] = vals[toks[i]]

        # find if there exists !=, >=, <=
        eq_idxs = [idx for idx, tok in enumerate(toks) if tok == "="]
        eq_idxs.reverse()
        prefix = ('!', '>', '<')
        for eq_idx in eq_idxs:
            pre_tok = toks[eq_idx-1]
            if pre_tok in prefix:
                toks = toks[:eq_idx-1] + [pre_tok + "="] + toks[eq_idx+1: ]

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
            assert key not in self.alias_tables, "Alias {} has the same name in table".format(key)
            self.alias_tables[key] = key
        return self.alias_tables