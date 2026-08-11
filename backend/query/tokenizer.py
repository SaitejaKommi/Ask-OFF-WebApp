from typing import List

class QueryTokenizer:
    @staticmethod
    def tokenize(query: str) -> List[str]:
        if not query:
            return []
        return query.strip().split()

    @classmethod
    def generate_ngrams(cls, tokens: List[str], max_n: int = 4) -> List[str]:
        ngrams = []
        n_tokens = len(tokens)
        for n in range(1, min(max_n, n_tokens) + 1):
            for i in range(n_tokens - n + 1):
                ngram = " ".join(tokens[i:i + n])
                ngrams.append(ngram)
        # Sort ngrams by length descending so that longer matches (e.g. "butternut mountain farm") 
        # are processed or ranked before shorter matches (e.g. "butternut") during parsing.
        ngrams.sort(key=len, reverse=True)
        return ngrams
