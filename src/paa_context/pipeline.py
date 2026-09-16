from .insertion_sort import insertion_sort
from .linear_search import linear_search
from .merge_sort import merge_sort


def top_k(resultados, k):
    """Corta os k primeiros resultados com score > 0.

    Assume que `resultados` ja esta ordenado por score decrescente
    (empates por source_order; ver sort_key).

    - k <= 0: lista vazia
    - filtra score > 0 antes do corte (a busca linear ja tira os zeros;
      o filtro fica como garantia)
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


def retrieve(query, chunks, estatisticas, k, algoritmo="insertion", contador=None):
    """Pipeline do prototipo: consulta -> pontuacao -> ordenacao -> top-k.

    Fluxo:
      linear_search (relevance_score em cada chunk, so score > 0)
      -> Insertion Sort ou Merge Sort
      -> top_k (corta em k)

    `estatisticas` vem de build_statistics, calculado uma vez antes.
    `algoritmo` em {"insertion", "merge"}.
    `contador` e opcional e e repassado a ordenacao.
    """
    pontuados = linear_search(query, chunks, estatisticas)

    if algoritmo == "insertion":
        ordenados = insertion_sort(pontuados, contador=contador)
    elif algoritmo == "merge":
        ordenados = merge_sort(pontuados, contador=contador)
    else:
        raise ValueError(f"algoritmo desconhecido: {algoritmo!r}")

    return top_k(ordenados, k)
