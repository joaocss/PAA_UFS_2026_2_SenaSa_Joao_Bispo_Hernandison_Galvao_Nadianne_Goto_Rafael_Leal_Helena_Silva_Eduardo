from .linear_search import linear_search

# Desempate (prototipo):
# Enquanto nao houver source_order na estrutura oficial de Chunk,
# empates de score preservam a ordem do corpus (ordem de entrada apos
# a busca linear). Quando Chunk existir, a chave passa a ser
# (-escore, source_order), conforme docs/CONTRATOS.md.


def _merge(left, right, contador=None):
    """Combina duas metades ja ordenadas por score decrescente.

    Em empate, escolhe o da esquerda primeiro (estabilidade =
    ordem do corpus). Sera substituido por source_order com Chunk.
    """
    merged = []
    i = 0
    j = 0

    while i < len(left) and j < len(right):
        if contador is not None:
            contador.comparacoes += 1
        if left[i][1] >= right[j][1]:
            merged.append(left[i])
            i += 1
        else:
            merged.append(right[j])
            j += 1
        if contador is not None:
            contador.trocas += 1

    while i < len(left):
        merged.append(left[i])
        i += 1
        if contador is not None:
            contador.trocas += 1

    while j < len(right):
        merged.append(right[j])
        j += 1
        if contador is not None:
            contador.trocas += 1

    return merged


def merge_sort(items, contador=None):
    """Ordena pares (chunk, score) por score decrescente.

    Merge Sort recursivo, estavel: empates preservam a ordem de entrada
    (ordem do corpus apos a busca linear). Esse criterio sera
    substituido por source_order quando a estrutura Chunk existir.

    Devolve lista nova e nao altera a original.
    Sem atalho para lista ja ordenada nem troca para Insertion Sort.
    `contador` e opcional: se fornecido, incrementa comparacoes e trocas
    (copias para a lista de saida do merge).

    Tempo: Theta(C log C) em qualquer caso.
    Espaco extra: O(C).
    """
    if len(items) <= 1:
        return list(items)

    mid = len(items) // 2
    left = merge_sort(items[:mid], contador=contador)
    right = merge_sort(items[mid:], contador=contador)
    return _merge(left, right, contador=contador)


def linear_search_merge_sorted(query, chunks, contador=None):
    """Busca linear seguida de Merge Sort.

    Tempo: Theta(C(m + n) + C log C) em qualquer caso.
    """
    return merge_sort(linear_search(query, chunks), contador=contador)
