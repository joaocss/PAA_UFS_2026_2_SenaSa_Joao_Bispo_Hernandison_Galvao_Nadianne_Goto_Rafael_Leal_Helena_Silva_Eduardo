from .modelos import Chunk
from .relevance import relevance_score

TEXTOS_PYTHON = [
    "Uma lista em Python armazena elementos em uma sequencia ordenada.",
    "Uma tupla em Python e imutavel e tambem armazena uma sequencia.",
    "Um dicionario associa chaves a valores.",
    "Funcoes em Python sao definidas com a palavra def.",
    "Operadores booleanos representam verdadeiro ou falso.",
]

CHUNKS_PYTHON = [
    Chunk(
        chunk_id=f"exemplo-c{i:04d}",
        source_order=i,
        texto=texto,
        tipo="markdown",
        arquivo="exemplo.ipynb",
        capitulo="Exemplo",
        secao="",
        celula_idx=i,
        token_inicio=0,
        token_fim=0,
        n_tokens=0,
    )
    for i, texto in enumerate(TEXTOS_PYTHON)
]


def linear_search(query, chunks, estatisticas):
    """Varre todos os chunks e pontua cada um com relevance_score.

    Devolve a lista de pares (chunk, score) com score > 0, na ordem do
    corpus. Chunks com score zero ficam fora (contrato 02), entao a
    ordenacao recebe so os P candidatos, como na C2.
    Nao ordena, nao corta top-k e nao usa indice.

    Tempo:  Theta(C * (m + n)), em qualquer caso.
    Espaco extra:  O(m + n) para as contagens do par atual,
    mais O(P) para a lista de saida.
    """
    results = []

    for chunk in chunks:
        score = relevance_score(query, chunk, estatisticas)
        if score > 0:
            results.append((chunk, score))

    return results
