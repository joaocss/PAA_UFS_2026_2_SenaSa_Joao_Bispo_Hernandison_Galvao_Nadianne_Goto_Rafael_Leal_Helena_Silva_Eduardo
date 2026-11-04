#!/usr/bin/env python3
"""Auditoria independente dos JSONL reais da Parte D (nao modifica arquivos).

Execute da raiz do projeto:
    python scripts/av2/auditar_av2.py
    python scripts/av2/auditar_av2.py --arquivo caminho/alternativo.jsonl
"""
from __future__ import annotations

import argparse
import json
import math
import sys
from collections import defaultdict
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
DEFAULT = RAIZ / 'experimentos/av2/brutos/execucoes.jsonl'
ESTRATEGIAS = {
    'prefixo_ranking', 'guloso_valor', 'guloso_densidade',
    'guloso_modificado', 'mochila_dp',
}
NS = {10, 30, 50}
WS = {256, 512, 1024}
REPETICOES = {1, 2, 3, 4, 5}


def auditar(caminho: Path, consultas_esperadas=30):
    """Retorna relatorio; falha com ValueError na primeira inconsistencia."""
    if not caminho.is_file():
        raise ValueError(f'Arquivo nao encontrado: {caminho}')
    grupos = defaultdict(list)
    run_ids = set()
    consultas = set()
    total = 0
    with caminho.open(encoding='utf-8') as f:
        for linha_n, texto in enumerate(f, 1):
            if not texto.strip():
                raise ValueError(f'Linha vazia na posicao {linha_n}')
            try:
                r = json.loads(texto)
            except json.JSONDecodeError as exc:
                raise ValueError(f'JSON invalido na linha {linha_n}') from exc
            try:
                qid = str(r['query_id'])
                n = int(r['n_solicitado'])
                n_real = int(r['n_real'])
                W = int(r['W'])
                estr = str(r['estrategia'])
                rep = int(r['repeticao'])
                run_id = str(r['run_id'])
                ids = r['ids_selecionados']
                valor = int(r['valor_quantizado'])
                otimo = int(r['otimo_valor_quantizado_dp'])
                custo = int(r['custo_total'])
                razao = float(r['razao_aproximacao'])
                selecionados = int(r['selecionados'])
                julgados = int(r['itens_julgados'])
                nao_julgados = int(r['itens_nao_julgados'])
                tempo = int(r['tempo_selecao_ns'])
                memoria = int(r['memoria_pico_selecao_bytes'])
                fracao = float(r['fracao_orcamento'])
            except (KeyError, TypeError, ValueError) as exc:
                raise ValueError(f'Campo ausente ou invalido na linha {linha_n}: {exc}') from exc
            if n not in NS or W not in WS or estr not in ESTRATEGIAS or rep not in REPETICOES:
                raise ValueError(f'Configuracao inesperada na linha {linha_n}')
            if not qid or not (0 <= n_real <= n):
                raise ValueError(f'Consulta/n_real invalido na linha {linha_n}')
            if not isinstance(ids, list) or len(ids) != selecionados or len(ids) != len(set(ids)):
                raise ValueError(f'IDs duplicados ou quantidade inconsistente na linha {linha_n}')
            if any(not isinstance(cid, str) or not cid for cid in ids):
                raise ValueError(f'chunk_id invalido na linha {linha_n}')
            if not (0 <= custo <= W and 0 <= selecionados <= n_real and valor >= 0 and otimo >= 0):
                raise ValueError(f'Orcamento/valor/quantidade inconsistente na linha {linha_n}')
            if julgados < 0 or nao_julgados < 0 or julgados + nao_julgados != selecionados:
                raise ValueError(f'Cobertura qrels inconsistente na linha {linha_n}')
            if tempo < 0 or memoria < 0:
                raise ValueError(f'Tempo/memoria negativos na linha {linha_n}')
            if not math.isclose(fracao, custo/W, rel_tol=1e-10, abs_tol=1e-12):
                raise ValueError(f'Fracao de orcamento inconsistente na linha {linha_n}')
            esperado = valor/otimo if otimo else 1.0
            if not math.isclose(razao, esperado, rel_tol=1e-10, abs_tol=1e-12):
                raise ValueError(f'Razao de aproximacao incorreta na linha {linha_n}')
            if not 0 <= razao <= 1:
                raise ValueError(f'Razao fora de [0, 1] na linha {linha_n}')
            if estr == 'mochila_dp' and valor != otimo:
                raise ValueError(f'DP difere do proprio otimo na linha {linha_n}')
            if run_id in run_ids:
                raise ValueError(f'run_id duplicado na linha {linha_n}: {run_id}')
            run_ids.add(run_id)
            consultas.add(qid)
            grupos[(qid, n, W, estr)].append(r)
            total += 1

    esperado_total = consultas_esperadas * len(NS) * len(WS) * len(ESTRATEGIAS) * len(REPETICOES)
    if total != esperado_total:
        raise ValueError(f'Total incorreto: {total}, esperado {esperado_total}')
    if len(consultas) != consultas_esperadas:
        raise ValueError(f'Consultas: {len(consultas)}, esperadas {consultas_esperadas}')

    propriedades = ('ids_selecionados', 'n_real', 'valor_quantizado',
                    'otimo_valor_quantizado_dp', 'custo_total',
                    'itens_julgados', 'itens_nao_julgados', 'razao_aproximacao')
    for key, rs in grupos.items():
        if {int(r['repeticao']) for r in rs} != REPETICOES or len(rs) != 5:
            raise ValueError(f'Repeticoes ausentes ou duplicadas em {key}')
        for campo in propriedades:
            if any(r[campo] != rs[0][campo] for r in rs[1:]):
                raise ValueError(f'Selecao nao deterministica em {key}, campo {campo}')

    empates = defaultdict(int)
    pior = {e: 1.0 for e in ESTRATEGIAS}
    for qid in consultas:
        for n in NS:
            for W in WS:
                grp = {s: grupos.get((qid, n, W, s)) for s in ESTRATEGIAS}
                if not all(grp.values()):
                    raise ValueError(f'Estrategia ausente no cenario {(qid, n, W)}')
                otimos = {int(rs[0]['otimo_valor_quantizado_dp']) for rs in grp.values()}
                if len(otimos) != 1:
                    raise ValueError(f'Referencia DP varia no cenario {(qid, n, W)}')
                if int(grp['guloso_modificado'][0]['valor_quantizado']) < int(grp['guloso_densidade'][0]['valor_quantizado']):
                    raise ValueError(f'S4 pior que S3 no cenario {(qid, n, W)}')
                for s, rs in grp.items():
                    ratio = float(rs[0]['razao_aproximacao'])
                    pior[s] = min(pior[s], ratio)
                    if math.isclose(ratio, 1, abs_tol=1e-12):
                        empates[s] += 1
    return {
        'consultas': len(consultas), 'cenarios': len(consultas)*len(NS)*len(WS),
        'pares_cenario_estrategia': len(grupos), 'medicoes': total,
        'empates': dict(sorted(empates.items())),
        'menor_razao': dict(sorted(pior.items())),
    }


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--arquivo', type=Path, default=DEFAULT)
    args = p.parse_args()
    try:
        resultado = auditar(args.arquivo)
    except ValueError as exc:
        print(f'AUDITORIA FALHOU: {exc}', file=sys.stderr)
        return 1
    print('AUDITORIA AV2: APROVADA')
    print(json.dumps(resultado, indent=2, ensure_ascii=False))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
