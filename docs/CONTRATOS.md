# Contratos técnicos da equipe

Decisões fechadas em 04/09/2026, antes de qualquer linha de código. Cinco das seis frentes programam contra estas interfaces. Mudar qualquer item depois de o código existir obriga a avisar o grupo e a repetir os testes.

## Numeração das configurações

Segue a numeração do enunciado (seção 7.1), não a do plano inicial.

| Configuração | Recuperação | Ordenação | Corresponde no enunciado a |
| --- | --- | --- | --- |
| C1 | varredura linear de todos os chunks | Insertion Sort (equipe) | baseline: busca linear com ordenação mínima |
| C2 | índice invertido + busca binária no vocabulário | Merge Sort dos candidatos (equipe) | busca ordenada/indexada |
| C3 | varredura linear de todos os chunks | Merge Sort (equipe) | divisão e conquista |
| C4 | TF-IDF do scikit-learn | da biblioteca | biblioteca de referência, analisada à parte |

C1, C2 e C3 devem devolver a mesma lista para a mesma consulta, o mesmo corpus e o mesmo k. Isso é testado.

## Contrato 01: formato do chunk

Arquivo `data/processed/chunks.jsonl`, um objeto JSON por linha, campos obrigatórios:

| Campo | Tipo | Significado |
| --- | --- | --- |
| `chunk_id` | str | identificador único, `"<notebook>-c<índice global com 4 dígitos>"`, ex. `chap05-c0012` |
| `source_order` | int | posição de aparição no livro, de 0 a n-1, sem repetição, estável entre execuções |
| `texto` | str | texto normalizado usado na pontuação |
| `tipo` | str | `"markdown"` ou `"codigo"` |
| `arquivo` | str | caminho relativo do notebook, ex. `capitulos/chap05.ipynb` |
| `capitulo` | str | título do capítulo |
| `secao` | str | último título de seção antes do chunk, ou vazio |
| `celula_idx` | int | índice da célula de origem no notebook |
| `token_inicio` | int | offset em tokens do início do chunk dentro da célula |
| `token_fim` | int | offset em tokens do fim, exclusivo |
| `n_tokens` | int | quantidade de tokens do chunk |

Fixture sintético em `tests/fixtures/chunks_sinteticos.jsonl`, com cerca de 20 chunks no mesmo formato, incluindo pelo menos dois pares que empatam de propósito na pontuação de alguma consulta de teste. É o primeiro arquivo a existir; todas as outras frentes começam por ele.

## Contrato 02: pontuação, comparação e desempate

- Pontuação: a mesma função para C1, C2 e C3, implementada pela equipe, conforme a seção 4.2 do plano. Para um termo t e chunk c: `tf = 0` se t não ocorre, senão `1 + ln f(t, c)`; `idf = ln((N + 1) / (df(t) + 1)) + 1`; escore = soma, sobre os termos distintos da consulta, de `qtf · tf · idf`.
- Ordem total: maior escore primeiro; em empate, **menor `source_order` primeiro**. Nunca desempatar por `chunk_id` textual nem por ordem de chegada.
- Chave de ordenação, para quem usa chave: `(-escore, source_order)`.
- Chunk com escore zero não entra no resultado em nenhuma configuração.
- Retorno de uma consulta: lista de pares `(chunk_id, escore)` com no máximo `min(k, número de chunks com escore > 0)` itens.
- `k <= 0` devolve lista vazia. `k` maior que o número de candidatos devolve todos os candidatos.
- Consulta sem nenhum termo do vocabulário devolve lista vazia, sem erro.

## Contrato 03: consultas e julgamentos de relevância

`data/queries.csv`, cabeçalho:

```
query_id,texto,categoria,capitulo_esperado,autor
```

`categoria` em `conceito`, `exemplo` ou `relacao`. As 30 consultas são escritas antes de qualquer resultado ser observado.

`data/qrels.csv`, cabeçalho:

```
query_id,chunk_id,avaliador,relevancia,adjudicada
```

`relevancia` em 0, 1 ou 2. Dois avaliadores independentes, metade das consultas cada; `adjudicada` traz o valor final após conciliação. Métricas calculadas: Precision@k, Recall@k, nDCG@k e MRR, com k em 5 e 10.

## Contrato 04: log de execução

`experimentos/brutos/execucoes.jsonl`, um objeto JSON por execução, campos:

```
run_id, timestamp, commit, host, python_versao,
config, query_id, k, chunk_size, overlap, tamanho_corpus, semente, repeticao,
tempo_ingestao_ns, tempo_ordenacao_ou_indice_ns, tempo_consulta_ns, tempo_total_ns,
memoria_pico_bytes, comparacoes, trocas,
n_chunks, n_candidatos, n_resultados, resultado_vazio
```

- `config` em `C1`, `C2`, `C3`, `C4`; `tamanho_corpus` em `25`, `50`, `100` (percentual de chunks, estratificado por capítulo).
- Tempos com `time.perf_counter_ns`; memória com `tracemalloc`. Os quatro tempos separados atendem à seção 7.3 do enunciado.
- `comparacoes` e `trocas` vêm de contadores internos do Insertion Sort, do Merge Sort e da busca binária. São obrigatórios: com cerca de 330 chunks o cronômetro pode não separar C1 de C3, e a diferença assintótica aparece na contagem.
- Uma linha por consulta, configuração, tamanho, repetição e k. Nunca só médias.

## Experimento principal

3 configurações × 3 tamanhos × 5 repetições = 45 execuções, após 2 de aquecimento, na mesma máquina, sem outras cargas, ordem das configurações aleatorizada por semente registrada. Mínimo do enunciado: 12.

## Datas do enunciado

| Data | O que precisa existir |
| --- | --- |
| 05/09 | Reserva publicada no Classroom (feita) |
| 10/09 | Checkpoint em sala: programa rodando sobre pelo menos 8 notebooks, protocolo experimental de uma página |
| 23/09 | Entrega até 23h59 |
| 24/09 | Apresentação |

Combinações internas de prazo ficam em `docs/PLANEJAMENTO.md` e `docs/SEMANA1.md`, não aqui.

## Relatório e estes contratos

O rascunho do relatório trazido por Hernandison em 04/09 (`relatorio/rascunho_2026-09-04.pdf`) é a base do documento final. Três pontos dele precisam ser alinhados a este arquivo, porque o professor confere se prova, análise e código descrevem a mesma coisa:

1. Numeração das configurações: o rascunho usa C2 = Merge Sort e C3 = índice. Vale a tabela do início deste arquivo, que segue o enunciado (C2 = índice, C3 = Merge Sort).
2. Fórmula da nota: o rascunho usa `tf = 1 + log2 f` e `idf = log2(N/df)`. Vale o contrato 02 (`1 + ln f` e `ln((N+1)/(df+1)) + 1`). Motivo: é a mesma fórmula do scikit-learn, o que deixa a comparação com C4 limpa, e nunca zera um termo presente em todos os chunks.
3. Identificador do chunk: o rascunho fala em id inteiro único; aqui o inteiro é `source_order` e o `chunk_id` é texto. O desempate da prova usa `source_order`. Nada muda na prova, só o nome.

Aquecimento: duas repetições descartadas antes das cinco medidas, como no plano; o rascunho diz uma. Vale duas.
