from .linear_search import linear_search
from .sort_key import sort_key

# Desempate:
# Chave (-escore, source_order), conforme docs/CONTRATOS.md. Em empate de
# score vence o menor source_order, qualquer que seja a ordem de entrada.
# Assim o resultado nao muda quando os candidatos chegam fora da ordem do
# corpus, como na C2.


def insertion_sort(items, contador=None):
    """Ordena pares (chunk, score) por score decrescente.

    Empates de score saem em ordem crescente de source_order
    (ver sort_key).

    Devolve lista nova e nao altera a original.
    `contador` e opcional: se fornecido, incrementa comparacoes e trocas
    (deslocamentos).

    Tempo: melhor Theta(P); medio e pior Theta(P^2), com P = len(items).
    Espaco extra: O(P), pela copia da entrada.
    """
    result = list(items)

    for i in range(1, len(result)):
        current = result[i]
        j = i - 1
        while j >= 0:
            if contador is not None:
                contador.comparacoes += 1
            if not sort_key(current) < sort_key(result[j]):
                break
            result[j + 1] = result[j]
            if contador is not None:
                contador.trocas += 1
            j -= 1
        result[j + 1] = current

    return result


def linear_search_sorted(query, chunks, estatisticas, contador=None):
    """Busca linear seguida de Insertion Sort.

    Tempo: Theta(C(m + n) + P^2) no pior e no caso medio.
    """
    return insertion_sort(linear_search(query, chunks, estatisticas), contador=contador)
