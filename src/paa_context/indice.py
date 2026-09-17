"""Indice invertido da configuracao C2.

Na construcao, cada termo do corpus ganha a lista das posicoes dos chunks em
que aparece (postings). Na consulta, a busca binaria acha cada termo no
vocabulario ordenado, as listas desses termos sao unidas e so os chunks da
uniao sao pontuados, com a mesma relevance_score de C1 e C3.
"""

from dataclasses import dataclass

from .busca_binaria import busca_binaria
from .merge_sort import merge_sort
from .pipeline import top_k
from .preprocessing import normalize
from .relevance import relevance_score


@dataclass
class IndiceInvertido:
    """Indice pronto para consulta.

    chunks: os chunks, na ordem em que foram indexados.
    vocabulario: termos distintos em ordem crescente, para a busca binaria.
    postings: postings[i] tem, em ordem crescente, as posicoes em `chunks`
        dos chunks que contem vocabulario[i].
    """

    chunks: list
    vocabulario: list
    postings: list


def construir_indice(chunks):
    """Monta o indice invertido sobre os chunks, na ordem em que vieram.

    Os termos passam pelo mesmo normalize da pontuacao. O dicionario abaixo
    so existe durante a construcao; a consulta acha os termos por busca
    binaria. O vocabulario e ordenado uma vez com sorted do Python, na
    construcao, fora da consulta que as configuracoes comparam.

    Tempo: Theta(T + V log V), com T tokens no corpus e V termos distintos.
    Espaco: Theta(V + soma dos tamanhos dos postings).
    """
    por_termo = {}
    for posicao, chunk in enumerate(chunks):
        for termo in set(normalize(chunk.texto)):
            por_termo.setdefault(termo, []).append(posicao)

    vocabulario = sorted(por_termo)
    postings = [por_termo[termo] for termo in vocabulario]
    return IndiceInvertido(chunks=list(chunks), vocabulario=vocabulario, postings=postings)


def unir_postings(a, b):
    """Uniao de duas listas crescentes de posicoes, sem repeticao, em ordem crescente.

    Dois ponteiros, como o merge do Merge Sort.

    Tempo: Theta(len(a) + len(b)).
    """
    uniao = []
    i = 0
    j = 0

    while i < len(a) and j < len(b):
        if a[i] == b[j]:
            uniao.append(a[i])
            i += 1
            j += 1
        elif a[i] < b[j]:
            uniao.append(a[i])
            i += 1
        else:
            uniao.append(b[j])
            j += 1

    uniao.extend(a[i:])
    uniao.extend(b[j:])
    return uniao


def buscar_indexado(consulta, indice, estatisticas, contador=None):
    """Candidatos da C2: pares (chunk, score) com score > 0, na ordem do corpus.

    Para cada termo distinto da consulta, busca_binaria no vocabulario; se o
    termo existe, seus postings entram na uniao. So os chunks da uniao sao
    pontuados. Devolve os mesmos pares que linear_search.
    `contador` e opcional: se fornecido, soma as comparacoes da busca binaria.

    Tempo: O(m log V + m S + P(m + n)), com m termos na consulta, S a soma
    dos postings desses termos e P candidatos.
    """
    termos = list(dict.fromkeys(normalize(consulta)))

    posicoes = []
    for termo in termos:
        i = busca_binaria(indice.vocabulario, termo, contador)
        if i >= 0:
            posicoes = unir_postings(posicoes, indice.postings[i])

    resultados = []
    for posicao in posicoes:
        chunk = indice.chunks[posicao]
        score = relevance_score(consulta, chunk, estatisticas)
        if score > 0:
            resultados.append((chunk, score))

    return resultados


def recuperar_indexado(consulta, indice, estatisticas, k, contador=None):
    """C2 completa: buscar_indexado -> Merge Sort dos candidatos -> top_k.

    `contador`, se fornecido, soma as comparacoes da busca binaria e do
    Merge Sort.
    """
    candidatos = buscar_indexado(consulta, indice, estatisticas, contador=contador)
    return top_k(merge_sort(candidatos, contador=contador), k)
