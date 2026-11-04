"""Testes das novas metricas, sem modificar corpus ou medicoes reais."""
import importlib.util
import json
import sys
import types
from pathlib import Path
from types import SimpleNamespace

import pytest


def carregar_modulo(monkeypatch):
    """Isola somente os imports de integracao (sem exigir o corpus real)."""
    pasta = sys.modules.get('paa_context')
    if pasta is None:
        monkeypatch.setitem(sys.modules, 'paa_context', types.ModuleType('paa_context'))
    for nome, simbolo in [('modelos', 'carregar_chunks'), ('pipeline', 'retrieve'),
                         ('relevance', 'build_statistics')]:
        modulo = types.ModuleType('paa_context.' + nome)
        setattr(modulo, simbolo, lambda *a, **kw: None)
        monkeypatch.setitem(sys.modules, 'paa_context.' + nome, modulo)
    selecao = types.ModuleType('paa_context.selecao')
    selecao.ESTRATEGIAS = {}
    selecao.itens_de_resultados = lambda xs: xs
    monkeypatch.setitem(sys.modules, 'paa_context.selecao', selecao)
    arq = Path(__file__).resolve().parents[2] / 'scripts/av2/completar_contrato08.py'
    spec = importlib.util.spec_from_file_location('completar_contrato08_testado', arq)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture
def mod(monkeypatch):
    return carregar_modulo(monkeypatch)


def registro(est, valor, ids, rep=1, q='Q01', n=10, W=256):
    return dict(query_id=q, n_solicitado=n, n_real=n, W=W, estrategia=est,
                repeticao=rep, valor_quantizado=valor, ids_selecionados=ids,
                custo_total=20)


def test_jaccard_duplicacao_textual(mod):
    r = mod.redundancia(['a', 'b', 'c'], {'a':'Casa boa', 'b':'casa boa', 'c':'outro assunto'})
    assert r == {'pares_possiveis':3, 'pares_redundantes':1, 'taxa_pares_redundantes':1/3}


@pytest.mark.parametrize('ids', [[], ['a']])
def test_jaccard_sem_pares(mod, ids):
    r = mod.redundancia(ids, {'a': 'texto'})
    assert r['pares_possiveis'] == 0 and r['taxa_pares_redundantes'] is None


def test_jaccard_fronteira_inclusiva(mod):
    corpus={'a':'a b c d e', 'b':'a b c d f'}
    assert mod.redundancia(['a','b'], corpus, .6)['pares_redundantes'] == 1
    assert mod.redundancia(['a','b'], corpus, .8)['pares_redundantes'] == 0


def test_jaccard_rejeita_ids_duplicados(mod):
    with pytest.raises(ValueError): mod.redundancia(['a','a'], {'a':'texto'})


def test_jaccard_rejeita_chunk_desconhecido(mod):
    with pytest.raises(KeyError): mod.redundancia(['nao'], {})


def test_delta_e_repeticoes(mod):
    rs = [registro('mochila_dp', 100, ['a','b'], i) for i in (1,2)]
    rs += [registro('guloso_densidade', 80, ['a'], i) for i in (1,2)]
    linhas = mod.calcular_metricas_complementares(rs, {'a':'texto', 'b':'texto'})
    assert len(linhas) == 2
    guloso = next(r for r in linhas if r['estrategia']=='guloso_densidade')
    assert guloso['delta_valor_quantizado'] == 20
    assert guloso['delta_valor_tfidf_aproximado'] == .02
    assert guloso['repeticoes_originais'] == 2
    assert next(r for r in linhas if r['estrategia']=='mochila_dp')['delta_valor_quantizado'] == 0


def test_delta_nao_permite_guloso_superar_dp(mod):
    with pytest.raises(ValueError, match='Valor > DP'):
        mod.calcular_metricas_complementares([registro('mochila_dp', 100, ['a']),
          registro('guloso_densidade', 110, ['a'])], {'a':'texto'})


def test_delta_exige_dp(mod):
    with pytest.raises(ValueError, match='sem referencia'):
        mod.calcular_metricas_complementares([registro('guloso_densidade', 10, ['a'])], {'a':'texto'})


def test_delta_rejeita_nao_determinismo(mod):
    rs = [registro('mochila_dp', 100, ['a']), registro('guloso_densidade', 80, ['a'], 1),
          registro('guloso_densidade', 70, ['a'], 2)]
    with pytest.raises(ValueError, match='nao deterministica'):
        mod.calcular_metricas_complementares(rs, {'a':'texto'})


def test_gravar_csv_lf(mod, tmp_path):
    alvo=tmp_path/'t.csv'
    mod.gravar_csv(alvo, [{'x':'1'}, {'x':'2'}])
    assert alvo.read_bytes()==b'x\n1\n2\n'


def test_resumo_fluxo_medianas(mod):
    rs=[]
    for t in [1_000_000, 3_000_000, 2_000_000]:
        rs.append({'n':10,'W':256,'estrategia':'mochila_dp',
                   'tempo_recuperacao_ns':t,'tempo_conversao_ns':t,
                   'tempo_selecao_ns':t,'tempo_fluxo_consulta_ns':3*t})
    linhas=mod.resumir_fluxos(rs)
    assert len(linhas)==1
    assert linhas[0]['mediana_fluxo_consulta_ms']==6.0
    assert linhas[0]['mediana_recuperacao_ms']==2.0


def test_fluxo_mede_separado(mod, monkeypatch):
    def retrieve(*a, **kw): return ['item']
    def converter(rs): return rs
    def algoritmo(itens, W): return SimpleNamespace(ids=['a'], valor_total=12, custo_total=6)
    monkeypatch.setattr(mod, 'retrieve', retrieve)
    monkeypatch.setattr(mod, 'itens_de_resultados', converter)
    monkeypatch.setattr(mod, 'ESTRATEGIAS', {'mochila_dp':algoritmo})
    r=mod.fluxo('pergunta', [], {}, 10, 256, 'mochila_dp')
    assert r['ids_escolhidos']==['a'] and r['valor_quantizado']==12
    assert r['tempo_fluxo_consulta_ns']==sum(r[f'tempo_{k}_ns'] for k in ('recuperacao','conversao','selecao'))


def test_sha256_arquivo(mod, tmp_path):
    f=tmp_path/'x'; f.write_bytes(b'abc')
    assert mod.sha256(f)=='ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad'
