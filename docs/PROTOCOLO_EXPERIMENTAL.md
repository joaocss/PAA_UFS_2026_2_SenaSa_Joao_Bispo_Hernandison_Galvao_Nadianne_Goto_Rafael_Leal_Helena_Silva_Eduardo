# Protocolo experimental

Versão para o checkpoint de 10/09/2026. Segue os contratos 02 e 04 de `docs/CONTRATOS.md`.

## Pergunta e hipóteses

Queremos saber quanto custa recuperar os k trechos mais relevantes do livro Pense Python com cada uma das três configurações, e se esse custo cresce como a análise assintótica prevê. Três hipóteses guiam as medições.

H1, equivalência: C1, C2 e C3 devolvem a mesma lista para a mesma consulta, o mesmo corpus e o mesmo k. Qualquer divergência é bug, não resultado.

H2, comparações: com P candidatos de escore maior que zero, o Insertion Sort de C1 faz até P(P-1)/2 comparações e o Merge Sort de C3 faz cerca de P log P. A razão entre os dois cresce com P.

H3, tempo: no corpus inteiro o cronômetro separa C1 de C3, mas em corpus pequeno a diferença some no custo fixo do interpretador. A contagem de comparações é a evidência principal; o tempo é secundário.

## Fatores e níveis

| Fator | Níveis |
| --- | --- |
| Configuração | C1 (varredura + Insertion), C2 (índice + busca binária + Merge), C3 (varredura + Merge) |
| Tamanho do corpus | 25 %, 50 % e 100 % dos chunks, sorteados por capítulo com semente fixa |
| Consulta | as 30 consultas de `data/queries.csv`, escritas antes de qualquer resultado |
| k | 5 e 10 |
| Repetição | 5 medidas, precedidas de 2 execuções de aquecimento descartadas |

Com 256 tokens por chunk e sobreposição de 32, o corpus inteiro tem 2.737 chunks, o que dá cerca de 684, 1.368 e 2.737 chunks nos três tamanhos. O experimento principal são 3 configurações × 3 tamanhos × 5 repetições, 45 execuções por consulta e valor de k. O mínimo do enunciado é 12.

C4, o TF-IDF do scikit-learn, roda nas mesmas consultas como referência externa. Como pontua por cosseno com normalização L2, sua lista pode diferir da nossa; ela é analisada à parte e não entra em H1.

## O que se mede em cada execução

Uma linha em `experimentos/brutos/execucoes.jsonl` por consulta, configuração, tamanho, repetição e k, nunca só médias. Tempos com `time.perf_counter_ns`, separados em ingestão, ordenação ou construção do índice, consulta e total. Memória de pico com `tracemalloc`. Comparações e trocas vêm dos contadores internos do Insertion Sort, do Merge Sort e da busca binária. Também ficam registrados número de chunks, candidatos com escore maior que zero, resultados devolvidos e se o resultado saiu vazio. Quando os julgamentos de relevância existirem, entram Precision@k, Recall@k, nDCG@k e MRR.

## Controle

Mesma máquina em todas as execuções, sem outras cargas. A ordem das configurações dentro de cada bloco é sorteada com semente registrada, para que aquecimento de cache e variação térmica não favoreçam sempre a mesma. Cada execução grava hostname, processador, memória, sistema operacional, versão do Python, versões das bibliotecas, commit e linha de comando completa em `experimentos/logs`.

## Análise

Mediana e intervalo interquartil por célula do desenho, porque cinco repetições com um pico de coletor de lixo distorcem a média e não a mediana. Uma tabela por métrica e configuração. Gráfico principal: comparações em função do número de chunks, uma curva por configuração, eixos logarítmicos, para que n² e n log n apareçam como retas de inclinações diferentes. Gráfico secundário: tempo total pelas mesmas variáveis.

## Limites

Três tamanhos não provam a ordem assintótica; mostram tendência. O cronômetro mede o Python tanto quanto o algoritmo. Um único livro introdutório é um estudo de caso, não uma amostra de materiais educacionais abertos.
