
#!/usr/bin/env python3

from __future__ import annotations

import csv
import json
import statistics
from collections import defaultdict
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
BASE = RAIZ / 'experimentos/av2'
FONTE = BASE / 'brutos/execucoes.jsonl'
PROCESSADOS = BASE / 'processados'
FIGURAS = BASE / 'figuras'


def median(xs):
    return statistics.median(xs) if xs else None


def main():
    if not FONTE.is_file():
        raise SystemExit(f'Nao encontrei {FONTE}; execute rodar_av2.py sem --rapido')
    linhas = [json.loads(x) for x in FONTE.read_text(encoding='utf-8').splitlines() if x.strip()]
    if not linhas:
        raise SystemExit('Arquivo de medicoes vazio')
    PROCESSADOS.mkdir(parents=True, exist_ok=True)
    FIGURAS.mkdir(parents=True, exist_ok=True)
    grupos = defaultdict(list)
    for r in linhas:
        grupos[(r['query_id'], int(r['n_solicitado']), int(r['W']), r['estrategia'])].append(r)
    por_caso = []
    for (qid, n, W, estrategia), rs in sorted(grupos.items()):
        primeiro = rs[0]
        por_caso.append({
            'query_id': qid, 'n': n, 'n_real': primeiro['n_real'], 'W': W,
            'estrategia': estrategia, 'repeticoes': len(rs),
            'tempo_mediano_ms': median([r['tempo_selecao_ns'] / 1e6 for r in rs]),
            'memoria_pico_kib': primeiro['memoria_pico_selecao_bytes'] / 1024,
            'valor_quantizado': primeiro['valor_quantizado'],
            'razao_aproximacao': primeiro['razao_aproximacao'],
            'relevancia_tfidf': primeiro['relevancia_tfidf'],
            'fracao_orcamento': primeiro['fracao_orcamento'],
            'itens_julgados': primeiro['itens_julgados'],
            'itens_nao_julgados': primeiro['itens_nao_julgados'],
            'precisao_entre_julgados': primeiro['precisao_entre_julgados'],
        })
    with (PROCESSADOS/'resumo_por_caso.csv').open('w', newline='', encoding='utf-8') as f:
        w = csv.DictWriter(f, fieldnames=list(por_caso[0]), lineterminator='\n'); w.writeheader(); w.writerows(por_caso)

    grupos_resumo = defaultdict(list)
    for r in por_caso:
        grupos_resumo[(r['n'], r['W'], r['estrategia'])].append(r)
    agregados = []
    for (n, W, estrategia), rs in sorted(grupos_resumo.items()):
        prec = [r['precisao_entre_julgados'] for r in rs if r['precisao_entre_julgados'] is not None]
        agregados.append({
            'n': n, 'W': W, 'estrategia': estrategia, 'consultas': len(rs),
            'mediana_tempos_ms': median([r['tempo_mediano_ms'] for r in rs]),
            'mediana_memoria_kib': median([r['memoria_pico_kib'] for r in rs]),
            'media_razao_aproximacao': statistics.mean(r['razao_aproximacao'] for r in rs),
            'media_uso_orcamento': statistics.mean(r['fracao_orcamento'] for r in rs),
            'consultas_com_selecionados_julgados': len(prec),
            'media_precisao_entre_julgados': statistics.mean(prec) if prec else '',
        })
    with (PROCESSADOS/'resumo_por_configuracao.csv').open('w', newline='', encoding='utf-8') as f:
        w = csv.DictWriter(f, fieldnames=list(agregados[0]), lineterminator='\n'); w.writeheader(); w.writerows(agregados)

    try:
        import matplotlib
        matplotlib.use('Agg')
        import matplotlib.pyplot as plt
    except ImportError:
        print('matplotlib ausente: CSVs foram gerados, figuras nao')
        return

    for W in sorted({r['W'] for r in agregados}):
        fig, ax = plt.subplots(figsize=(8, 5))
        for estrategia in sorted({r['estrategia'] for r in agregados}):
            rs = sorted((r for r in agregados if r['W'] == W and r['estrategia'] == estrategia), key=lambda r:r['n'])
            ax.plot([r['n'] for r in rs], [r['mediana_tempos_ms'] for r in rs], marker='o', label=estrategia)
        ax.set(xlabel='Candidatos solicitados (n)', ylabel='Mediana do tempo de selecao (ms)', title=f'Tempo de selecao por n (W={W})')
        ax.grid(alpha=.25); ax.legend(fontsize=8); fig.tight_layout()
        fig.savefig(FIGURAS / f'tempo_por_n_W{W}.png', dpi=160)
        plt.close(fig)

    for n in sorted({r['n'] for r in agregados}):
        fig, ax = plt.subplots(figsize=(8, 5))
        for estrategia in sorted({r['estrategia'] for r in agregados}):
            rs = sorted((r for r in agregados if r['n'] == n and r['estrategia'] == estrategia), key=lambda r:r['W'])
            ax.plot([r['W'] for r in rs], [r['mediana_memoria_kib'] for r in rs], marker='o', label=estrategia)
        ax.set(xlabel='Orcamento (palavras)', ylabel='Mediana do pico rastreado (KiB)', title=f'Memoria de selecao por W (n={n})')
        ax.grid(alpha=.25); ax.legend(fontsize=8); fig.tight_layout()
        fig.savefig(FIGURAS / f'memoria_por_W_n{n}.png', dpi=160)
        plt.close(fig)

    fig, ax = plt.subplots(figsize=(8, 5))
    for estrategia in sorted({r['estrategia'] for r in agregados}):
        rs = sorted((r for r in agregados if r['estrategia'] == estrategia and r['W'] == 512), key=lambda r:r['n'])
        ax.plot([r['n'] for r in rs], [r['media_razao_aproximacao'] for r in rs], marker='o', label=estrategia)
    ax.set(xlabel='Candidatos solicitados (n)', ylabel='Media de valor / valor DP', title='Qualidade do objetivo quantizado (W=512)')
    ax.grid(alpha=.25); ax.legend(fontsize=8); fig.tight_layout()
    fig.savefig(FIGURAS / 'razao_aproximacao_W512.png', dpi=160)
    plt.close(fig)
    print(f'{len(linhas)} medicoes; {len(por_caso)} pares consulta/configuracao/estrategia; {len(agregados)} agregados')
    print(f'Arquivos em {PROCESSADOS.relative_to(RAIZ)} e {FIGURAS.relative_to(RAIZ)}')


if __name__ == '__main__':
    main()
