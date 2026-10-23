"""Testes da selecao de contexto (AV2).

Cobrem as categorias da secao 11 do enunciado (normal, vazio, fronteira,
empate, entrada grande, dado duplicado e adversarial), os casos obrigatorios
do contrato 07 da Parte A, a validacao de entrada e as regras de desempate
dos contratos 05 e 06 de docs/CONTRATOS_AV2.md. O contrato 14 liga cada
teste ao requisito que ele avalia.
"""

import dataclasses
import itertools
import math
import random
from types import SimpleNamespace

import pytest

from paa_context.selecao import (
    ESCALA_VALOR,
    ESTRATEGIAS,
    Item,
    forca_bruta,
    guloso_densidade,
    guloso_modificado,
    guloso_valor,
    itens_de_resultados,
    mochila_dp,
    prefixo_ranking,
)


PADRAO = object()  # marca "nao informado", para que None possa ser testado como entrada


def item(nome, custo, valor, posicao, source_order=PADRAO, escore=PADRAO):
    # sem indicacao, o lugar no livro acompanha o lugar no ranking e o
    # escore e o valor desfeito da escala
    return Item(
        chunk_id=nome, custo=custo, valor=valor, posicao=posicao,
        source_order=posicao if source_order is PADRAO else source_order,
        escore=valor / ESCALA_VALOR if escore is PADRAO else escore,
    )


def chunk(chunk_id, n_tokens, source_order):
    return SimpleNamespace(chunk_id=chunk_id, n_tokens=n_tokens, source_order=source_order)


# Exemplo da aula 07 (livro, casaco e camera), com chunks no lugar dos objetos.
AULA07 = [item("livro", 2, 3, 0), item("casaco", 3, 4, 1), item("camera", 4, 5, 2)]

# Contraexemplo 1 do contrato 11: {A, D} e {B, C} valem 8 e custam 10 com W = 10.
EMPATE = [item("A", 6, 5, 0), item("B", 5, 4, 1), item("C", 5, 4, 2), item("D", 4, 3, 3)]


def otima_parte_a(itens, W):
    """Juiz dos desempates da Parte A (contrato 05): entre as solucoes viaveis,
    a de maior valor; no empate, a de menor custo; persistindo o empate, a de
    sequencia crescente de source_order lexicograficamente menor."""
    viaveis = [
        sub
        for r in range(len(itens) + 1)
        for sub in itertools.combinations(itens, r)
        if sum(i.custo for i in sub) <= W
    ]
    escolhida = min(viaveis, key=lambda sub: (
        -sum(i.valor for i in sub),
        sum(i.custo for i in sub),
        sorted(i.source_order for i in sub),
    ))
    return sorted(escolhida, key=lambda i: i.posicao)


# 1. Caso normal -------------------------------------------------------------

def test_normal_exemplo_da_aula07():
    selecao = mochila_dp(AULA07, 5)
    assert selecao.ids == ["livro", "casaco"]
    assert selecao.valor_total == 7
    assert selecao.custo_total == 5


def test_normal_exemplo_rag_da_aula07():
    # aula 07, slide 26: orcamento de 1.000 palavras; entram A, B e D (950 palavras, 23 pontos)
    itens = [item("A_definicao", 350, 9, 0), item("B_exemplo", 400, 8, 1),
             item("C_historico", 500, 5, 2), item("D_excecao", 200, 6, 3)]
    selecao = mochila_dp(itens, 1000)
    assert selecao.ids == ["A_definicao", "B_exemplo", "D_excecao"]
    assert selecao.valor_total == 23
    assert selecao.custo_total == 950


def test_falha_gulosa_da_aula08():
    # aula 08, slide 9, e exemplo do contrato 07: guloso 160, otimo 220
    itens = [item("p10", 10, 60, 0), item("p20", 20, 100, 1), item("p30", 30, 120, 2)]
    assert guloso_densidade(itens, 50).valor_total == 160
    assert guloso_densidade(itens, 50).custo_total == 30
    assert guloso_valor(itens, 50).valor_total == 220  # neste caso, o guloso por valor acerta
    assert mochila_dp(itens, 50).ids == ["p20", "p30"]
    assert mochila_dp(itens, 50).valor_total == 220
    assert mochila_dp(itens, 50).custo_total == 50
    # o guloso modificado nao corrige este caso, mas cumpre a garantia: 160 >= 220 / 2
    assert guloso_modificado(itens, 50).valor_total == 160


# 2. Vazio --------------------------------------------------------------------

def test_vazio_sem_candidatos():
    # consulta sem correspondencia: a AV1 devolve lista vazia
    for estrategia in ESTRATEGIAS.values():
        selecao = estrategia([], 100)
        assert selecao.escolhidos == []
        assert selecao.custo_total == 0
        assert selecao.relevancia_total == 0


def test_vazio_orcamento_zero():
    for estrategia in ESTRATEGIAS.values():
        assert estrategia(AULA07, 0).escolhidos == []


# 3. Fronteira ----------------------------------------------------------------

def test_fronteira_item_que_cabe_exatamente():
    itens = [item("a", 10, 5, 0)]
    assert mochila_dp(itens, 10).ids == ["a"]
    assert mochila_dp(itens, 9).ids == []  # uma palavra a menos e nao cabe


def test_fronteira_guloso_enche_o_orcamento_exatamente():
    # soma dos custos igual a W: os tres cabem, em qualquer estrategia
    itens = [item("a", 4, 5, 0), item("b", 3, 4, 1), item("c", 3, 1, 2)]
    for estrategia in ESTRATEGIAS.values():
        assert estrategia(itens, 10).custo_total == 10


def test_fronteira_todos_cabem_todos_entram():
    # orcamento folgado: as cinco estrategias levam tudo, na ordem do ranking
    for estrategia in ESTRATEGIAS.values():
        assert estrategia(AULA07, 100).ids == ["livro", "casaco", "camera"]


def test_fronteira_nenhum_item_cabe():
    # todos os itens excedem o limite: a solucao e vazia, sem erro
    itens = [item("a", 300, 9, 0), item("b", 256, 8, 1)]
    for estrategia in ESTRATEGIAS.values():
        assert estrategia(itens, 128).escolhidos == []


def test_fronteira_item_maior_que_o_orcamento_nao_bloqueia_os_demais():
    # contrato 07: o item com custo > W fica de fora, e os outros continuam elegiveis
    itens = [item("enorme", 50, 100, 0), item("b", 4, 3, 1), item("c", 5, 4, 2)]
    for nome in ("guloso_valor", "guloso_densidade", "guloso_modificado", "mochila_dp"):
        assert ESTRATEGIAS[nome](itens, 10).ids == ["b", "c"]


# 4. Validacao de entrada (contrato 11, regra 2) ------------------------------

@pytest.mark.parametrize("W", [-1, 10.0, True, "10", None])
def test_validacao_orcamento_invalido_e_erro(W):
    for estrategia in ESTRATEGIAS.values():
        with pytest.raises(ValueError):
            estrategia(AULA07, W)


@pytest.mark.parametrize("onde", [0, 1, 2])
@pytest.mark.parametrize("custo, valor", [(0, 5), (-3, 5), (1.5, 5), (True, 5),
                                          (2, 0), (2, -1), (2, 2.7), (2, True)])
def test_validacao_item_invalido_e_erro(custo, valor, onde):
    # o item invalido aparece no comeco, no meio e no fim, pois a validacao percorre todos
    itens = [item("bom1", 2, 3, 0), item("bom2", 3, 4, 1)]
    itens.insert(onde, item("ruim", custo, valor, 9, escore=1.0))
    for estrategia in ESTRATEGIAS.values():
        with pytest.raises(ValueError):
            estrategia(itens, 10)


@pytest.mark.parametrize("escore", [0, 0.0, -1.0, math.nan, math.inf, True, "1.0", None])
def test_validacao_escore_invalido_e_erro(escore):
    itens = [item("a", 2, 3, 0), item("b", 2, 3, 1, escore=escore)]
    for estrategia in ESTRATEGIAS.values():
        with pytest.raises(ValueError):
            estrategia(itens, 10)


@pytest.mark.parametrize("posicao", [-1, 1.0, True, "1", None])
def test_validacao_posicao_invalida_e_erro(posicao):
    itens = [item("a", 2, 3, 0), item("b", 2, 3, posicao, source_order=1)]
    for estrategia in ESTRATEGIAS.values():
        with pytest.raises(ValueError):
            estrategia(itens, 10)


@pytest.mark.parametrize("source_order", [-1, 1.0, True, "1", None])
def test_validacao_source_order_invalido_e_erro(source_order):
    itens = [item("a", 2, 3, 0), item("b", 2, 3, 1, source_order=source_order)]
    for estrategia in ESTRATEGIAS.values():
        with pytest.raises(ValueError):
            estrategia(itens, 10)


def test_validacao_posicao_repetida_e_erro():
    # com posicoes iguais, o desempate dependeria da ordem da lista
    itens = [item("a", 5, 7, 0, 0), item("b", 5, 7, 0, 1), item("c", 5, 7, 1, 2)]
    for estrategia in ESTRATEGIAS.values():
        with pytest.raises(ValueError):
            estrategia(itens, 10)


def test_validacao_source_order_repetido_e_erro():
    itens = [item("a", 5, 7, 0, 4), item("b", 5, 7, 1, 4), item("c", 5, 7, 2, 5)]
    for estrategia in ESTRATEGIAS.values():
        with pytest.raises(ValueError):
            estrategia(itens, 10)


def test_validacao_chunk_id_repetido_e_erro():
    itens = [item("a", 2, 3, 0), item("a", 2, 3, 1)]
    for estrategia in ESTRATEGIAS.values():
        with pytest.raises(ValueError):
            estrategia(itens, 10)


# 5. Empate -------------------------------------------------------------------

def test_empate_dp_itens_identicos_ficam_os_de_menor_source_order():
    # cabem dois de tres iguais: ficam os primeiros do livro
    itens = [item("x", 5, 7, 0), item("y", 5, 7, 1), item("z", 5, 7, 2)]
    assert mochila_dp(itens, 10).ids == ["x", "y"]


def test_empate_dp_mesmo_valor_e_custo_decide_o_source_order():
    # contraexemplo 1: {A, D} e {B, C} valem 8 e custam 10; (0, 3) < (1, 2)
    dp = mochila_dp(EMPATE, 10)
    assert dp.ids == ["A", "D"]
    assert dp.valor_total == forca_bruta(EMPATE, 10).valor_total == 8
    # com B e C no comeco do livro, (0, 1) vem antes de (2, 3) e fica {B, C}
    no_livro = [item("A", 6, 5, 0, 2), item("B", 5, 4, 1, 0),
                item("C", 5, 4, 2, 1), item("D", 4, 3, 3, 3)]
    assert mochila_dp(no_livro, 10).ids == ["B", "C"]


def test_empate_dp_mesmo_valor_fica_o_menor_custo():
    # contraexemplo 2: {1, 3, 4, 5} e {1, 4, 6} valem 28; fica o de menor custo
    custos_valores = [(10, 4), (10, 11), (7, 2), (3, 2), (6, 9), (8, 6), (9, 8)]
    itens = [item(str(p), c, v, p) for p, (c, v) in enumerate(custos_valores)]
    dp = mochila_dp(itens, 27)
    assert dp.ids == ["1", "4", "6"]
    assert dp.valor_total == 11 + 9 + 8 == 28
    assert dp.custo_total == 10 + 6 + 9 == 25
    assert 11 + 2 + 9 + 6 == 28 and 10 + 3 + 6 + 8 == 27  # o outro otimo, {1, 3, 4, 5}
    assert forca_bruta(itens, 27).valor_total == 28


def test_empate_dp_nao_depende_da_ordem_da_lista():
    # a DP ordena por source_order antes de montar a tabela
    invertida = list(reversed(EMPATE))
    embaralhada = [EMPATE[2], EMPATE[0], EMPATE[3], EMPATE[1]]
    assert mochila_dp(invertida, 10).ids == mochila_dp(EMPATE, 10).ids == ["A", "D"]
    assert mochila_dp(embaralhada, 10).ids == ["A", "D"]


def test_empate_dp_usa_source_order_e_nao_a_posicao():
    # ranking x, y, z; no livro, z vem primeiro e x por ultimo
    itens = [item("x", 5, 7, 0, 2), item("y", 5, 7, 1, 1), item("z", 5, 7, 2, 0)]
    assert mochila_dp(itens, 10).ids == ["y", "z"]  # saida na ordem do ranking


def test_empate_guloso_densidade_desempata_pelo_source_order():
    # a lista chega fora de ordem; razao e valor empatam, e decide o livro
    itens = [item("z", 5, 7, 2), item("x", 5, 7, 0), item("y", 5, 7, 1)]
    assert guloso_densidade(itens, 10).ids == ["x", "y"]
    no_livro = [item("x", 5, 7, 0, 2), item("y", 5, 7, 1, 1), item("z", 5, 7, 2, 0)]
    assert guloso_densidade(no_livro, 10).ids == ["y", "z"]


def test_empate_guloso_densidade_maior_valor_antes_do_source_order():
    # a e b tem razao 2; pelo contrato 06, o maior valor (a) vem antes,
    # mesmo com b no comeco do livro e no topo do ranking
    itens = [item("b", 1, 2, 0, 0), item("a", 2, 4, 1, 1)]
    assert guloso_densidade(itens, 2).ids == ["a"]


def test_empate_guloso_valor_desempata_pelo_ranking():
    itens = [item("z", 5, 7, 2), item("x", 5, 7, 0), item("y", 5, 7, 1)]
    assert guloso_valor(itens, 10).ids == ["x", "y"]


def test_densidade_comparada_como_fracao_exata():
    # em float, as duas razoes viram 1.0 e B (maior valor) entraria primeiro;
    # em Fraction, A e mais denso
    grande = 10**16
    itens = [item("B", 2 * grande, 2 * grande, 0), item("A", grande, grande + 1, 1)]
    assert guloso_densidade(itens, 2 * grande).ids == ["A"]


def test_empate_guloso_modificado_fica_com_o_guloso():
    # o item isolado ("grande", 9) empata com a selecao gulosa (4 + 5);
    # nesse caso, o guloso modificado fica com o guloso
    itens = [item("a", 1, 4, 0), item("b", 1, 5, 1), item("grande", 10, 9, 2)]
    assert guloso_densidade(itens, 10).valor_total == 9
    assert guloso_modificado(itens, 10).ids == ["a", "b"]


def test_empate_guloso_modificado_entre_itens_isolados():
    # g1 e g2 valem 9 sozinhos e superam o guloso (1); fica o de melhor posicao
    itens = [item("g2", 10, 9, 2), item("a", 1, 1, 0), item("g1", 10, 9, 1)]
    assert guloso_modificado(itens, 10).ids == ["g1"]


# 6. Entrada grande -----------------------------------------------------------

def test_grande_dp_respeita_orcamento_e_bate_guloso():
    rng = random.Random(42)
    itens = [item(f"c{i}", rng.randint(1, 256), rng.randint(1, 20000), i) for i in range(300)]
    W = 2048
    dp = mochila_dp(itens, W)
    assert dp.custo_total <= W
    assert dp.valor_total == dp.extras["valor_otimo"]
    for base in (prefixo_ranking, guloso_valor, guloso_densidade, guloso_modificado):
        assert dp.valor_total >= base(itens, W).valor_total
    assert dp.celulas == 301 * 2049


# 7. Dado duplicado e conversao (contratos 02, 07 e 10) -----------------------

def test_duplicado_mesmo_chunk_id_e_erro():
    # contrato 07: identificador repetido e entrada invalida, e nao some em silencio
    c = chunk("chap05-c0423", 40, 7)
    outro = chunk("chap01-c0039", 10, 3)
    with pytest.raises(ValueError):
        itens_de_resultados([(c, 2.0), (outro, 1.0), (c, 2.0)])


def test_duplicado_texto_igual_com_ids_diferentes_passa():
    # revela uma falha: a mochila nao percebe a redundancia e leva os dois
    a = SimpleNamespace(chunk_id="chap14-c1975", n_tokens=8, source_order=1975,
                        texto="a solucao vai aqui")
    b = SimpleNamespace(chunk_id="chap14-c2004", n_tokens=8, source_order=2004,
                        texto="a solucao vai aqui")
    itens = itens_de_resultados([(a, 1.0), (b, 1.0)])
    assert mochila_dp(itens, 16).ids == ["chap14-c1975", "chap14-c2004"]


@pytest.mark.parametrize("n_tokens", [0, -2, 3.0, True])
def test_conversao_custo_invalido_e_erro(n_tokens):
    with pytest.raises(ValueError):
        itens_de_resultados([(chunk("x", n_tokens, 0), 1.0)])


@pytest.mark.parametrize("escore", [-0.5, math.nan, math.inf, -math.inf, True, "2.0"])
def test_conversao_escore_invalido_e_erro(escore):
    with pytest.raises(ValueError):
        itens_de_resultados([(chunk("x", 5, 0), escore)])


def test_conversao_custo_invalido_e_erro_mesmo_com_escore_zero():
    # o custo e conferido antes de o escore zero tirar o chunk da lista
    with pytest.raises(ValueError):
        itens_de_resultados([(chunk("x", 0, 0), 0.0)])


def test_conversao_escore_que_arredonda_para_zero_e_erro():
    # nao ocorre com a formula da AV1, mas o erro deve apontar a causa
    with pytest.raises(ValueError, match="arredonda"):
        itens_de_resultados([(chunk("x", 5, 0), 0.0004)])


def test_conversao_valor_posicao_e_source_order():
    # 1.0006 e 2.9996 distinguem arredondar de truncar
    a, b, c = chunk("a", 12, 40), chunk("b", 3, 2), chunk("c", 7, 15)
    itens = itens_de_resultados([(a, 13.2004), (b, 1.0006), (c, 2.9996)])
    assert [(i.custo, i.valor, i.posicao, i.source_order, i.escore) for i in itens] == [
        (12, 13200, 0, 40, 13.2004), (3, 1001, 1, 2, 1.0006), (7, 3000, 2, 15, 2.9996)]


def test_conversao_escore_zero_sai_e_posicao_fica_com_buraco():
    # contrato 07: relevancia zero sai antes da selecao; o seguinte mantem a
    # posicao que tinha no ranking da AV1
    z, o = chunk("z", 5, 0), chunk("o", 5, 1)
    itens = itens_de_resultados([(z, 0.0), (o, 1.0)])
    assert [(i.chunk_id, i.posicao) for i in itens] == [("o", 1)]
    assert itens_de_resultados([]) == []
    assert itens_de_resultados([(z, 0)]) == []


def test_relevancia_total_soma_os_escores_originais():
    # contrato 04: V_S e a soma dos escores, sem o arredondamento do valor
    a, b = chunk("a", 4, 0), chunk("b", 4, 1)
    selecao = mochila_dp(itens_de_resultados([(a, 1.23456), (b, 2.5)]), 8)
    assert selecao.valor_total == 1235 + 2500
    assert selecao.relevancia_total == pytest.approx(1.23456 + 2.5)


# 8. Corretude contra o juiz --------------------------------------------------

@pytest.mark.parametrize("semente", range(200))
def test_dp_igual_forca_bruta(semente):
    rng = random.Random(semente)
    n = rng.randint(0, 10)
    itens = [item(f"c{i}", rng.randint(1, 15), rng.randint(1, 30), i) for i in range(n)]
    W = rng.randint(0, 40)
    dp = mochila_dp(itens, W)
    assert dp.valor_total == forca_bruta(itens, W).valor_total
    assert dp.custo_total <= W                         # a reconstrucao respeita o orcamento
    assert dp.valor_total == dp.extras["valor_otimo"]  # e chega ao valor da tabela


@pytest.mark.parametrize("semente", range(200))
def test_dp_segue_os_desempates_da_parte_a(semente):
    # valores pequenos geram muitos empates; ordem do livro sorteada a parte
    rng = random.Random(5000 + semente)
    n = rng.randint(6, 12)
    ordem_no_livro = rng.sample(range(100), n)
    itens = [item(f"c{i}", rng.randint(1, 12), rng.randint(1, 6), i, ordem_no_livro[i])
             for i in range(n)]
    W = rng.randint(0, 30)
    rng.shuffle(itens)
    assert mochila_dp(itens, W).ids == [i.chunk_id for i in otima_parte_a(itens, W)]


@pytest.mark.parametrize("semente", range(50))
def test_estrategias_respeitam_orcamento_ordem_e_nao_alteram_a_entrada(semente):
    # regras 1, 5 e 6 do contrato 11, em todas as estrategias
    rng = random.Random(9000 + semente)
    n = rng.randint(2, 12)
    ordem_no_livro = rng.sample(range(100), n)
    itens = [item(f"c{i}", rng.randint(1, 20), rng.randint(1, 50), i, ordem_no_livro[i])
             for i in range(n)]
    rng.shuffle(itens)
    lista_original = list(itens)
    W = rng.randint(10, 100)
    for estrategia in ESTRATEGIAS.values():
        selecao = estrategia(itens, W)
        assert selecao.custo_total <= W
        posicoes = [i.posicao for i in selecao.escolhidos]
        assert posicoes == sorted(posicoes)
        assert len(set(selecao.ids)) == len(selecao.ids)
        assert set(selecao.ids) <= {i.chunk_id for i in itens}
        assert itens == lista_original


# 9. Adversarial: onde o guloso erra -----------------------------------------

@pytest.mark.parametrize("W", [10, 100, 1000])
def test_adversarial_guloso_densidade_pode_ser_muito_pior(W):
    # o minusculo (densidade 2) entra e o grande deixa de caber: o guloso
    # fica em 2 e o otimo e 2W-1
    itens = [item("minusculo", 1, 2, 0), item("grande", W, 2 * W - 1, 1)]
    assert guloso_densidade(itens, W).valor_total == 2
    assert mochila_dp(itens, W).valor_total == 2 * W - 1


@pytest.mark.parametrize("semente", range(200))
def test_guloso_modificado_garante_metade_do_otimo(semente):
    # o item caro (mais da metade de W) e o caso em que S3 sozinho falha
    rng = random.Random(1000 + semente)
    W = rng.randint(4, 40)
    n = rng.randint(0, 9)
    itens = [item(f"c{i}", rng.randint(1, 15), rng.randint(1, 30), i) for i in range(n)]
    itens.append(item("caro", rng.randint(W // 2 + 1, W), rng.randint(1, 60), n))
    otimo = forca_bruta(itens, W).valor_total
    modificado = guloso_modificado(itens, W)
    assert modificado.custo_total <= W
    assert 2 * modificado.valor_total >= otimo


def test_guloso_modificado_conserta_o_contraexemplo():
    W = 1000
    itens = [item("minusculo", 1, 2, 0), item("grande", W, 2 * W - 1, 1)]
    assert guloso_modificado(itens, W).ids == ["grande"]


def test_adversarial_prefixo_trava_no_primeiro_grande():
    # a AV1 para no primeiro que nao cabe, ainda que haja espaco para outros
    itens = [item("topo", 256, 50, 0), item("b", 20, 10, 1), item("c", 20, 9, 2)]
    assert prefixo_ranking(itens, 128).escolhidos == []
    assert mochila_dp(itens, 128).ids == ["b", "c"]


# 10. Otimo no valor nao e otimo em relevancia --------------------------------
# Revela uma falha: a DP maximiza o tf-idf, nao a relevancia real (dados
# inventados, apenas para ilustrar).

def test_otimo_no_valor_nao_e_otimo_em_relevancia():
    # segundo o avaliador humano, apenas a "definicao" responde a pergunta
    relevantes = {"definicao"}
    itens = [
        item("definicao", 60, 90, 0),   # responde, mas e grande
        item("exemplo_a", 50, 70, 1),   # parece relevante pelo tf-idf
        item("exemplo_b", 50, 30, 2),
    ]
    W = 100
    dp = mochila_dp(itens, W)
    guloso = guloso_valor(itens, W)

    def acertos(selecao):
        return sum(chunk_id in relevantes for chunk_id in selecao.ids)

    assert dp.valor_total > guloso.valor_total  # 100 > 90 no valor estimado
    assert acertos(dp) == 0                      # nenhum chunk relevante
    assert acertos(guloso) == 1
    # o guloso por valor/palavra (S3), linha de base da Parte A, tambem acerta
    assert guloso_densidade(itens, W).ids == ["definicao"]


# 11. Estrutura -----------------------------------------------------------------

def test_estrategias_e_campos_da_selecao():
    # contrato 11: o dicionario tem as cinco estrategias, sem a forca bruta,
    # e apenas a DP preenche celulas e extras
    assert list(ESTRATEGIAS) == ["prefixo_ranking", "guloso_valor", "guloso_densidade",
                                 "guloso_modificado", "mochila_dp"]
    assert forca_bruta not in ESTRATEGIAS.values()
    for nome, estrategia in ESTRATEGIAS.items():
        selecao = estrategia(AULA07, 5)
        assert selecao.estrategia == nome
        if nome == "mochila_dp":
            assert selecao.celulas == 4 * 6
            assert selecao.extras == {"valor_otimo": 7}
        else:
            assert selecao.celulas == 0
            assert selecao.extras == {}


def test_forca_bruta_so_ate_20_itens():
    itens = [item(f"c{i}", 1, 1, i) for i in range(21)]
    with pytest.raises(ValueError):
        forca_bruta(itens, 5)


def test_item_nao_pode_ser_alterado():
    with pytest.raises(dataclasses.FrozenInstanceError):
        AULA07[0].valor = 99
