from paa_context.sort_key import sort_key


class DummyChunk:
    def __init__(self, source_order):
        self.source_order = source_order


def test_maior_score_vem_primeiro():
    chunk_a = DummyChunk(source_order=2)
    chunk_b = DummyChunk(source_order=1)

    item_a = (chunk_a, 10.0)
    item_b = (chunk_b, 20.0)

    assert sort_key(item_b) < sort_key(item_a)


def test_empate_usa_menor_source_order():
    chunk_a = DummyChunk(source_order=1)
    chunk_b = DummyChunk(source_order=2)

    item_a = (chunk_a, 10.0)
    item_b = (chunk_b, 10.0)

    assert sort_key(item_a) < sort_key(item_b)


def test_ordem_transitiva():
    chunk_a = DummyChunk(source_order=1)
    chunk_b = DummyChunk(source_order=2)
    chunk_c = DummyChunk(source_order=3)

    item_a = (chunk_a, 30.0)
    item_b = (chunk_b, 20.0)
    item_c = (chunk_c, 10.0)

    assert sort_key(item_a) < sort_key(item_b)
    assert sort_key(item_b) < sort_key(item_c)
    assert sort_key(item_a) < sort_key(item_c)
