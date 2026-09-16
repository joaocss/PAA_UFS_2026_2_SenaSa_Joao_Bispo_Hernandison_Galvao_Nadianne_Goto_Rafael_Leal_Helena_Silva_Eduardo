from .linear_search import linear_search
from .sort_key import sort_key

# Desempate:
# Chave (-escore, source_order), conforme docs/CONTRATOS.md. Em empate de
# score vence o menor source_order, qualquer que seja a ordem de entrada.
# Assim o resultado nao muda quando os candidatos chegam fora da ordem do
# corpus, como na C2.


def _merge(left, right, contador=None):
    """Combina duas metades ja ordenadas por score decrescente.

    Em empate de score, vence o menor source_order (ver sort_key).
    """
    merged = []
    i = 0
    j = 0

    while i < len(left) and j < len(right):
        if contador is not None:
            contador.comparacoes += 1
        if sort_key(left[i]) <= sort_key(right[j]):
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

    Merge Sort recursivo. Empates de score saem em ordem crescente de
    source_order (ver sort_key).

    Devolve lista nova e nao altera a original.
    Sem atalho para lista ja ordenada nem troca para Insertion Sort.
    `contador` e opcional: se fornecido, incrementa comparacoes e trocas
    (copias para a lista de saida do merge).

    Tempo: Theta(P log P) em qualquer caso, com P = len(items).
    Espaco extra: O(P).
    """
    if len(items) <= 1:
        return list(items)

    mid = len(items) // 2
    left = merge_sort(items[:mid], contador=contador)
    right = merge_sort(items[mid:], contador=contador)
    return _merge(left, right, contador=contador)


def linear_search_merge_sorted(query, chunks, estatisticas, contador=None):
    """Busca linear seguida de Merge Sort.

    Tempo: Theta(C(m + n) + P log P) em qualquer caso.
    """
    return merge_sort(linear_search(query, chunks, estatisticas), contador=contador)
