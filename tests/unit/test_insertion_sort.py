from paa_context.contador import Contador
from paa_context.insertion_sort import insertion_sort, linear_search_sorted
from paa_context.linear_search import CHUNKS_PYTHON, linear_search
from paa_context.relevance import build_statistics

ESTATISTICAS = build_statistics(CHUNKS_PYTHON)

# source_order: a = 0, b = 1, c = 2, d = 3, e = 4
a, b, c, d, e = CHUNKS_PYTHON


def test_lista_vazia():
    assert insertion_sort([]) == []


def test_um_elemento():
    items = [(a, 0.5)]

    assert insertion_sort(items) == items


def test_ja_ordenada():
    items = [(a, 1.0), (b, 0.5), (c, 0.0)]

    assert insertion_sort(items) == items


def test_ordem_inversa():
    items = [(c, 0.0), (b, 0.5), (a, 1.0)]

    assert insertion_sort(items) == [(a, 1.0), (b, 0.5), (c, 0.0)]


def test_empate_na_ordem_do_corpus():
    items = [(b, 0.5), (d, 0.5)]

    assert insertion_sort(items) == items


def test_empate_fora_da_ordem_do_corpus():
    items = [(d, 0.5), (b, 0.5)]

    assert insertion_sort(items) == [(b, 0.5), (d, 0.5)]


def test_empate_tres_elementos():
    items = [(a, 0.5), (b, 0.5), (c, 0.5)]

    assert insertion_sort(items) == items


def test_empate_tres_elementos_embaralhados():
    items = [(c, 0.5), (a, 0.5), (b, 0.5)]

    assert insertion_sort(items) == [(a, 0.5), (b, 0.5), (c, 0.5)]


def test_nao_altera_entrada():
    items = [(c, 0.0), (a, 1.0)]
    original = list(items)

    insertion_sort(items)

    assert items == original


def test_reutiliza_busca_linear():
    query = "lista python"
    pontuados = linear_search(query, CHUNKS_PYTHON, ESTATISTICAS)
    ordenados = insertion_sort(pontuados)

    assert sorted(score for _, score in ordenados) == sorted(
        score for _, score in pontuados
    )
    assert {chunk for chunk, _ in ordenados} == {chunk for chunk, _ in pontuados}


def test_consulta_lista_python():
    resultados = linear_search_sorted("lista python", CHUNKS_PYTHON, ESTATISTICAS)
    chunks = [chunk for chunk, _ in resultados]
    scores = [score for _, score in resultados]

    assert chunks == [a, b, d]
    assert scores[0] > scores[1]
    assert scores[1] == scores[2]


def test_contador_ordem_inversa():
    items = [(c, 0.0), (b, 0.5), (a, 1.0)]
    contador = Contador()

    insertion_sort(items, contador=contador)

    assert contador.comparacoes == 3
    assert contador.trocas == 3


def test_contador_lista_vazia():
    contador = Contador()

    insertion_sort([], contador=contador)

    assert contador.comparacoes == 0
    assert contador.trocas == 0
