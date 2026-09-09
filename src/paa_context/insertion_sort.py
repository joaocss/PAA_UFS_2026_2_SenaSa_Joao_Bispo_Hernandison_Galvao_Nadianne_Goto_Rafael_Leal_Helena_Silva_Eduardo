from .linear_search import linear_search


def insertion_sort(items):
    """Ordena pares (chunk, score) por score decrescente.

    Insertion Sort estavel: empates preservam a ordem de entrada.
    Devolve lista nova e nao altera a original.

    Tempo: melhor Theta(C); medio e pior Theta(C^2).
    Espaco extra: O(C), pela copia da entrada.
    """
    result = list(items)

    for i in range(1, len(result)):
        current = result[i]
        j = i - 1
        while j >= 0 and result[j][1] < current[1]:
            result[j + 1] = result[j]
            j -= 1
        result[j + 1] = current

    return result


def linear_search_sorted(query, chunks):
    """Busca linear seguida de Insertion Sort.

    Tempo: Theta(C(m + n) + C^2) no pior e no caso medio.
    """
    return insertion_sort(linear_search(query, chunks))
