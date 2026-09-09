from .linear_search import linear_search

# Desempate (prototipo):
# Enquanto nao houver source_order na estrutura oficial de Chunk,
# empates de score preservam a ordem do corpus (ordem de entrada apos
# a busca linear). Quando Chunk existir, a chave passa a ser
# (-escore, source_order), conforme docs/CONTRATOS.md.


def insertion_sort(items, contador=None):
    """Ordena pares (chunk, score) por score decrescente.

    Insertion Sort estavel: empates preservam a ordem de entrada
    (ordem do corpus apos a busca linear). Esse criterio sera
    substituido por source_order quando a estrutura Chunk existir.

    Devolve lista nova e nao altera a original.
    `contador` e opcional: se fornecido, incrementa comparacoes e trocas
    (deslocamentos).

    Tempo: melhor Theta(C); medio e pior Theta(C^2).
    Espaco extra: O(C), pela copia da entrada.
    """
    result = list(items)

    for i in range(1, len(result)):
        current = result[i]
        j = i - 1
        while j >= 0:
            if contador is not None:
                contador.comparacoes += 1
            if not result[j][1] < current[1]:
                break
            result[j + 1] = result[j]
            if contador is not None:
                contador.trocas += 1
            j -= 1
        result[j + 1] = current

    return result


def linear_search_sorted(query, chunks, contador=None):
    """Busca linear seguida de Insertion Sort.

    Tempo: Theta(C(m + n) + C^2) no pior e no caso medio.
    """
    return insertion_sort(linear_search(query, chunks), contador=contador)
