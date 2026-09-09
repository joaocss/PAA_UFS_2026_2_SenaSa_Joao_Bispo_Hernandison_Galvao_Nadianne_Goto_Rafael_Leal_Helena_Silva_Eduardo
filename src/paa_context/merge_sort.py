from .linear_search import linear_search


def _merge(left, right):
    """Combina duas metades ja ordenadas por score decrescente.

    Em empate, escolhe o da esquerda primeiro (estabilidade).
    """
    merged = []
    i = 0
    j = 0

    while i < len(left) and j < len(right):
        if left[i][1] >= right[j][1]:
            merged.append(left[i])
            i += 1
        else:
            merged.append(right[j])
            j += 1

    merged.extend(left[i:])
    merged.extend(right[j:])
    return merged


def merge_sort(items):
    """Ordena pares (chunk, score) por score decrescente.

    Merge Sort recursivo, estavel: empates preservam a ordem de entrada.
    Devolve lista nova e nao altera a original.
    Sem atalho para lista ja ordenada nem troca para Insertion Sort.

    Tempo: Theta(C log C) em qualquer caso.
    Espaco extra: O(C).
    """
    if len(items) <= 1:
        return list(items)

    mid = len(items) // 2
    left = merge_sort(items[:mid])
    right = merge_sort(items[mid:])
    return _merge(left, right)


def linear_search_merge_sorted(query, chunks):
    """Busca linear seguida de Merge Sort.

    Tempo: Theta(C(m + n) + C log C) em qualquer caso.
    """
    return merge_sort(linear_search(query, chunks))
