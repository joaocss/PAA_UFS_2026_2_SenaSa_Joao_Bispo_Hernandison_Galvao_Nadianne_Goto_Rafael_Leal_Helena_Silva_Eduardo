from paa_context.preprocessing import normalize


def test_lowercase():
    assert normalize("Python") == ["python"]


def test_remove_acentos():
    assert normalize("função") == ["funcao"]


def test_remove_pontuacao():
    assert normalize("lista, Python!") == ["lista", "python"]


def test_tokenizacao():
    assert normalize("uma lista em python") == ["uma", "lista", "em", "python"]


def test_string_vazia():
    assert normalize("") == []