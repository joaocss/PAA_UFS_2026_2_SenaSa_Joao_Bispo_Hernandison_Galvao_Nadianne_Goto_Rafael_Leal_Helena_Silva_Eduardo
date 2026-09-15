import bisect
import random

from paa_context.busca_binaria import busca_binaria
from paa_context.contador import Contador

VOCAB = ["classe", "dicionario", "funcao", "lista", "loop", "recursao", "string", "tupla"]


def test_primeiro_termo():
    assert busca_binaria(VOCAB, "classe") == 0


def test_ultimo_termo():
    assert busca_binaria(VOCAB, "tupla") == len(VOCAB) - 1


def test_termo_entre_duas_chaves_ausente():
    assert busca_binaria(VOCAB, "metodo") == -1


def test_termo_fora_dos_limites():
    assert busca_binaria(VOCAB, "aaa") == -1
    assert busca_binaria(VOCAB, "zzz") == -1


def test_vocabulario_vazio():
    assert busca_binaria([], "qualquer") == -1


def test_um_elemento():
    assert busca_binaria(["so"], "so") == 0
    assert busca_binaria(["so"], "nao") == -1


def test_oito_termos_no_maximo_quatro_rodadas():
    # Duas comparacoes por rodada (igualdade e menor), no maximo log2(8) + 1 rodadas.
    for termo in VOCAB:
        contador = Contador()
        busca_binaria(VOCAB, termo, contador)
        assert contador.comparacoes <= 8


def test_contador_nao_e_obrigatorio():
    assert busca_binaria(VOCAB, "lista") == 3


def test_concorda_com_bisect_em_vocabularios_aleatorios():
    rng = random.Random(2026)
    for _ in range(200):
        vocab = sorted({f"t{rng.randrange(1000)}" for _ in range(rng.randrange(0, 60))})
        for _ in range(10):
            termo = f"t{rng.randrange(1000)}"
            pos = bisect.bisect_left(vocab, termo)
            esperado = pos if pos < len(vocab) and vocab[pos] == termo else -1
            assert busca_binaria(vocab, termo) == esperado
