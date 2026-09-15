# Fixtures sintéticos

Dados inventados para desenvolver e testar antes de o corpus real estar fragmentado, e para os testes rodarem no CI sem o texto do livro, que a licença não permite versionar.

## Arquivos

| Arquivo | O que é |
| --- | --- |
| `chunks_sinteticos.jsonl` | 20 chunks no formato do contrato 01, sobre três "notebooks" fictícios: `funcoes` (source_order 0 a 6), `recursao` (7 a 13) e `listas` (14 a 19). Dois são de código. |
| `consultas_sinteticas.csv` | 3 consultas no cabeçalho do contrato 03. |
| `esperado_q01.json`, `esperado_q02.json`, `esperado_q03.json` | Os 5 melhores de cada consulta, com escore, pela fórmula do contrato 02. |
| `calcular_gabarito.py` | Script que gera os `esperado_*.json`. Implementa a fórmula de forma literal e independente de `src/`, para servir de oráculo. |

## Armadilhas plantadas de propósito

- **Empate dentro do mesmo notebook.** Para `q01` ("o que é recursão"), `recursao-c0007` e `recursao-c0008` têm exatamente as mesmas contagens dos termos da consulta e o mesmo escore. O contrato manda o 7 primeiro.
- **Empate entre notebooks com ordem alfabética invertida.** Ainda em `q01`, `recursao-c0012` e `listas-c0018` empatam. Por `source_order`, o 12 vem antes do 18. Por ordem alfabética de `chunk_id`, seria o contrário. Quem desempatar pelo id textual falha neste caso.
- **Chunk sem nenhum termo de nenhuma consulta.** `listas-c0019` (dicionários) tem escore zero nas três consultas e não pode aparecer em resultado nenhum.
- **Ordem de leitura diferente da alfabética.** Os notebooks aparecem na ordem `funcoes`, `recursao`, `listas`; alfabeticamente seria `funcoes`, `listas`, `recursao`.

## Como o gabarito foi calculado

Fórmula do contrato 02, com N = 20 chunks:

- token: `re.findall(r"\w+", texto.lower())`
- `tf(t, c) = 1 + ln f(t, c)` se o termo ocorre no chunk, senão 0
- `idf(t) = ln((N + 1) / (df(t) + 1)) + 1`
- `escore(c, q) = Σ qtf(t, q) · tf(t, c) · idf(t)` sobre os termos distintos de q
- ordem: maior escore, depois menor `source_order`; escore zero fica fora; k = 5

Conferência à mão de um caso, `q01` e o chunk `recursao-c0007`: os termos da consulta são `o`, `que`, `é`, `recursão`. No chunk, `o` ocorre 2 vezes, `que` 1, `é` 2, `recursão` 2. As frequências de documento nos 20 chunks são `o` 11, `que` 6, `é` 11, `recursão` 5. Então:

```
o:        (1 + ln 2) · (ln(21/12) + 1) = 1,6931 · 1,5596 = 2,6407
que:      (1 + ln 1) · (ln(21/7)  + 1) = 1,0000 · 2,0986 = 2,0986
é:        (1 + ln 2) · (ln(21/12) + 1) = 1,6931 · 1,5596 = 2,6407
recursão: (1 + ln 2) · (ln(21/6)  + 1) = 1,6931 · 2,2528 = 3,8143
soma                                                     = 11,1942
```

Bate com o `esperado_q01.json`: a conta foi refeita em 14/09/2026 e confere. Antes de os testes de `pontuacao.py` e de equivalência passarem a depender deste gabarito, alguém da equipe que não o gerou refaz a conta de pelo menos um chunk.

Os acentos são mantidos, então "é" e "e" são termos diferentes. Se a pontuação da equipe remover acentos, as notas mudam (sem acento, o df de "e" passa a 15 e `recursao-c0007` cai de 11,1942 para 10,7071) e este gabarito precisa ser regerado com o mesmo critério.

## Regerar

Se os chunks ou as consultas mudarem:

```
python tests/fixtures/calcular_gabarito.py
```
