from .insertion_sort import insertion_sort
from .linear_search import linear_search
from .merge_sort import merge_sort


def top_k(resultados, k):
    """Corta os k primeiros resultados com score > 0.

    Assume que `resultados` ja esta ordenado por score decrescente
    (empates na ordem do corpus; ver docstrings dos sorts).

    - k <= 0: lista vazia
    - filtra score > 0 antes do corte
    - k maior que o numero de candidatos: devolve todos os validos
    """
    if k <= 0:
        return []

    candidatos = [
        (chunk, score)
        for chunk, score in resultados
        if score > 0
    ]
    return candidatos[:k]


def retrieve(query, chunks, k, algoritmo="insertion", contador=None):
    """Pipeline do prototipo: consulta -> pontuacao -> ordenacao -> top-k.

    Fluxo:
      linear_search (relevance_score em cada chunk)
      -> Insertion Sort ou Merge Sort
      -> top_k (filtra score > 0 e corta em k)

    `algoritmo` em {"insertion", "merge"}.
    `contador` e opcional e e repassado a ordenacao.
    """
    pontuados = linear_search(query, chunks)

    if algoritmo == "insertion":
        ordenados = insertion_sort(pontuados, contador=contador)
    elif algoritmo == "merge":
        ordenados = merge_sort(pontuados, contador=contador)
    else:
        raise ValueError(f"algoritmo desconhecido: {algoritmo!r}")

    return top_k(ordenados, k)
