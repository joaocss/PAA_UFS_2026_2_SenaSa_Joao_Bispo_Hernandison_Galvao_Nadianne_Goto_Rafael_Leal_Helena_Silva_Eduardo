# Declaração de uso de IA generativa

Este arquivo é preenchido durante o trabalho, não na véspera da entrega. Cada uso relevante entra aqui no dia em que aconteceu, com o que foi verificado e por quem.

## Ferramentas e modelos

| Ferramenta | Modelo exibido na interface | Período de uso |
| --- | --- | --- |
| OpenAI Codex (João) | conferir na interface | 01/09/2026 |
| Claude Code, Anthropic (João) | Claude Fable 5.1; Claude Opus 5.5 | 02/09/2026 a 22/09/2026 |
| a preencher | a preencher | a preencher |

## Finalidade de cada uso

| Data | Integrante | Finalidade | Onde entrou no trabalho |
| --- | --- | --- | --- |
| 01/09 | João | Rascunho do plano de 19 seções a partir do enunciado | Planejamento interno, não versionado |
| 02/09 a 04/09 | João | Estrutura do repositório, script de aquisição com manifesto de hashes, contratos técnicos e divisão de frentes | `README.md`, `scripts/baixar_corpus.py`, `docs/CONTRATOS.md`, `docs/SEMANA1.md` |
| 14/09 a 16/09 | João | Fixtures sintéticos com gabarito, fragmentação, índice invertido e revisão do código de pontuação e desempate | `tests/fixtures/`, `src/paa_context/fragmentacao.py`, `indice.py`, `relevance.py`, `sort_key.py` |
| 19/09 | João | Medição dos contadores contra a previsão assintótica e teste de mutação do Merge Sort, em cópia descartável | Números usados na análise e em `tests/README.md` |
| 22/09 | João | Conversão das 30 perguntas para `data/queries.csv`, com as seções conferidas contra o corpus, e redação de `tests/README.md` | `data/queries.csv`, `docs/CONTRATOS.md`, `tests/README.md` |
| a preencher | a preencher | a preencher | a preencher |

## Prompts relevantes

O enunciado admite até cinco. Registrar o texto real enviado, não uma reconstrução aproximada.

1. (João, 22/09) "Você analisou o [repositório] preciso saber o que realmente interfere na nota, pois não quero ficar sendo o chato pedindo pra o pessoal corrigir"
2. (João, 22/09) "converte o PDF para o queries.csv, veja o que mais posso fazer pelo grupo"
3. a preencher
4. a preencher
5. a preencher

## Sugestões aproveitadas

| Sugestão | Por que foi aceita | Quem validou |
| --- | --- | --- |
| Postings como listas de posições crescentes e vocabulário ordenado, para que a busca binária tenha papel real na C2 | Com dicionário na consulta a busca binária seria decorativa | João, com os testes de `test_indice.py` e a equivalência C1 = C2 = C3 |
| Registrar `secao_esperada` com o nome exato da seção no corpus | Permite montar o julgamento de relevância a partir das seções | João, conferindo as 30 linhas contra `data/processed/chunks.jsonl` |
| a preencher | a preencher | a preencher |

## Sugestões corrigidas ou rejeitadas

| Sugestão | Problema identificado | O que a equipe fez no lugar |
| --- | --- | --- |
| Integração contínua no GitHub como item obrigatório | O enunciado não exige CI | Mantida fora do escopo |
| Numeração do plano inicial: C2 = Merge Sort, C3 = índice | Invertida em relação ao enunciado | Adotada a numeração do professor em `docs/CONTRATOS.md` |
| a preencher | a preencher | a preencher |

## Erros identificados

Registrar erros concretos de corretude, complexidade, casos de borda, estabilidade de ordenação ou desempate que a equipe encontrou em saída de IA. Este é o item que o enunciado cobra com mais rigor, porque distingue uso crítico de uso passivo.

| Erro | Como foi detectado | Correção aplicada |
| --- | --- | --- |
| (João) Na revisão da análise de complexidade, a fórmula da C2 não trazia o termo Θ(P(m + n)) da pontuação dos candidatos | Medição do tempo por etapa em 19/09, feita com apoio de IA: a pontuação é 96% do tempo da consulta e a ordenação, 4% | Termo apontado para inclusão no relatório; os números estão em `docs/RESULTADOS.md` |
| Plano de 01/09 com as configurações C2 e C3 trocadas | Conferência contra o PDF do enunciado em 04/09 | Numeração corrigida antes de qualquer código |
| a preencher | a preencher | a preencher |

## Verificação

Descrever os testes, provas, execuções e revisões por pares usados para validar cada trecho aproveitado. Código, prova ou análise sugerida por IA e não verificada não entra no trabalho.

João: cada módulo entrou com testes próprios (118 no total, `python -m pytest`). O gabarito dos fixtures foi calculado à parte em `tests/fixtures/calcular_gabarito.py` e conferido à mão para um escore. A equivalência C1 = C2 = C3 é testada em `tests/integration/test_equivalencia.py`. Os contadores de comparações foram confrontados com a previsão assintótica (Merge Sort a 1% de P log₂ P; Insertion Sort a 9% de P²/4). O teste de mutação de 19/09 mostrou um limite da suíte, registrado em `tests/README.md`.

## Contribuição individual no uso de IA

| Integrante | O que fez com apoio de IA | O que fez sem apoio de IA |
| --- | --- | --- |
| João Cosme Sena Sá | Estrutura do repositório, fixtures, fragmentação, índice invertido, conversão das consultas, documentação de testes | Decisões de escopo e divisão de frentes, revisão de cada trecho antes do commit, execução dos testes e das medições |
| a preencher | a preencher | a preencher |
