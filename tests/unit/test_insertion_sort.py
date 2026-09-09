from paa_context.insertion_sort import insertion_sort, linear_search_sorted
from paa_context.linear_search import CHUNKS_PYTHON, linear_search


def test_lista_vazia():
    assert insertion_sort([]) == []


def test_um_elemento():
    items = [("unico", 0.5)]

    assert insertion_sort(items) == items


def test_ja_ordenada():
    items = [("a", 1.0), ("b", 0.5), ("c", 0.0)]

    assert insertion_sort(items) == items


def test_ordem_inversa():
    items = [("c", 0.0), ("b", 0.5), ("a", 1.0)]

    assert insertion_sort(items) == [("a", 1.0), ("b", 0.5), ("c", 0.0)]


def test_empate_preserva_ordem():
    items = [("tupla", 0.5), ("funcoes", 0.5)]

    assert insertion_sort(items) == items


def test_nao_altera_entrada():
    items = [("c", 0.0), ("a", 1.0)]
    original = list(items)

    insertion_sort(items)

    assert items == original


def test_reutiliza_busca_linear():
    query = "lista python"
    pontuados = linear_search(query, CHUNKS_PYTHON)
    ordenados = insertion_sort(pontuados)

    assert sorted(score for _, score in ordenados) == sorted(
        score for _, score in pontuados
    )
    assert {chunk for chunk, _ in ordenados} == set(CHUNKS_PYTHON)


def test_consulta_lista_python():
    resultados = linear_search_sorted("lista python", CHUNKS_PYTHON)
    chunks = [chunk for chunk, _ in resultados]
    scores = [score for _, score in resultados]

    assert scores == [1.0, 0.5, 0.5, 0.0, 0.0]
    assert chunks[0] == CHUNKS_PYTHON[0]
    assert chunks[1] == CHUNKS_PYTHON[1]
    assert chunks[2] == CHUNKS_PYTHON[3]
