from .relevance import relevance_score

CHUNKS_PYTHON = [
    "Uma lista em Python armazena elementos em uma sequencia ordenada.",
    "Uma tupla em Python e imutavel e tambem armazena uma sequencia.",
    "Um dicionario associa chaves a valores.",
    "Funcoes em Python sao definidas com a palavra def.",
    "Operadores booleanos representam verdadeiro ou falso.",
]


def linear_search(query, chunks):
    """Varre todos os chunks e pontua cada um com relevance_score.

    Devolve a lista de pares (chunk, score) na ordem do corpus.
    Nao ordena, nao corta top-k e nao usa indice.

    Tempo:  Theta(C * (m + n)), em qualquer caso.
    Espaco extra:  O(m + n) para os conjuntos do par atual,
    mais O(C) para a lista de saida.
    """
    results = []

    for chunk in chunks:
        score = relevance_score(query, chunk)
        results.append((chunk, score))

    return results
