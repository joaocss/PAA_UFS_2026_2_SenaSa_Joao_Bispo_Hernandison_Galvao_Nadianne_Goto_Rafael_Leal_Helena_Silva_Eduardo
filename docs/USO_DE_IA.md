# Declaração de uso de IA generativa

Este arquivo é preenchido durante o trabalho, não na véspera da entrega. Cada uso relevante entra aqui no dia em que aconteceu, com o que foi verificado e por quem.

## Ferramentas e modelos

| Ferramenta | Modelo exibido na interface | Período de uso |
| --- | --- | --- |
| OpenAI Codex (João) | conferir na interface | 01/09/2026 |
| Claude Code, Anthropic (João) | Claude Fable 5.1; Claude Opus 5.5 | 02/09/2026 a 24/09/2026 |
| ChatGPT, OpenAI (João) | GPT-6 Astra | setembro de 2026 |
| ChatGPT, OpenAI (Nadianne) | GPT-5.6 Sol | 18/09/2026 a 19/09/2026 |
| a preencher | a preencher | a preencher |

## Finalidade de cada uso

| Data | Integrante | Finalidade | Onde entrou no trabalho |
| --- | --- | --- | --- |
| 01/09 | João | Rascunho do plano de 19 seções a partir do enunciado | Planejamento interno, não versionado |
| 02/09 a 04/09 | João | Estrutura do repositório, script de aquisição com manifesto de hashes, contratos técnicos e divisão de frentes | `README.md`, `scripts/baixar_corpus.py`, `docs/CONTRATOS.md`, `docs/SEMANA1.md` |
| 14/09 a 16/09 | João | Fixtures sintéticos com gabarito, fragmentação, índice invertido e revisão do código de pontuação e desempate | `tests/fixtures/`, `src/paa_context/fragmentacao.py`, `indice.py`, `relevance.py`, `sort_key.py` |
| 19/09 | João | Medição dos contadores contra a previsão assintótica e teste de mutação do Merge Sort, em cópia descartável | Números usados na análise e em `tests/README.md` |
| 22/09 | João | Conversão das 30 perguntas para `data/queries.csv`, com as seções conferidas contra o corpus, e redação de `tests/README.md` | `data/queries.csv`, `docs/CONTRATOS.md`, `tests/README.md` |
| 23/09 | João | Levantamento das pendências da entrega, reprodução completa em máquina limpa, script de ingestão e sensibilidade ao tamanho do chunk, atualização da documentação | `scripts/medir_ingestao.py`, `experimentos/processados/ingestao_e_sensibilidade.md`, `docs/RESULTADOS.md`, `data/README.md`, `tests/README.md` |
| 23/09 a 24/09 | João | Conferência do relatório contra o código e o enunciado, importação do gabarito de relevância para `qrels.csv`, roteiro do vídeo, apresentação em slides gerada a partir dos resultados | `scripts/montar_qrels.py`, `data/qrels.csv`, `slides/apresentacao_av1.pdf`, `VIDEO.md` |
| 18/09 a 19/09 | Nadianne | Apoio na análise formal de corretude do Merge Sort, definição das hipóteses, prova por indução, invariante de `_merge`, término e limites do argumento | `docs/CORRETUDE.md` |
| 18/09 a 19/09 | Nadianne | Apoio na análise no modelo RAM, melhor/pior/médio caso e recorrências dos algoritmos | documento de análise em `docs/` e slides |
| 19/09 | Nadianne | Apoio na elaboração de testes específicos da relação de ordenação por `score` e `source_order` | `tests/unit/test_sort_key.py` |
| a preencher | a preencher | a preencher | a preencher |

## Prompts relevantes

O enunciado admite até cinco. Registrar o texto real enviado, não uma reconstrução aproximada.

1. (João, 22/09) "Você analisou o [repositório] preciso saber o que realmente interfere na nota, pois não quero ficar sendo o chato pedindo pra o pessoal corrigir"
2. (João, 22/09) "converte o PDF para o queries.csv, veja o que mais posso fazer pelo grupo"
3. (Nadianne, 19/09) "Como ligar esse trecho e a  análise teórica as configurações C1, C2 e C3?"
4. a preencher
5. a preencher

## Sugestões aproveitadas

| Sugestão | Por que foi aceita | Quem validou |
| --- | --- | --- |
| Postings como listas de posições crescentes e vocabulário ordenado, para que a busca binária tenha papel real na C2 | Com dicionário na consulta a busca binária seria decorativa | João, com os testes de `test_indice.py` e a equivalência C1 = C2 = C3 |
| Registrar `secao_esperada` com o nome exato da seção no corpus | Permite montar o julgamento de relevância a partir das seções | João, conferindo as 30 linhas contra `data/processed/chunks.jsonl` |
| Estruturar a prova do Merge Sort com hipótese, indução, invariante e término | A estrutura corresponde ao comportamento recursivo da implementação e à metodologia estudada na disciplina | Nadianne, comparando a análise com `merge_sort.py`, `sort_key.py` e os testes existentes |
| Criar testes específicos para `sort_key`, cobrindo maior `score`, desempate por `source_order` e transitividade | As propriedades são usadas diretamente como hipóteses na prova formal | Nadianne, executando `test_sort_key.py` e a suíte completa com 118 testes aprovados |
| a preencher | a preencher | a preencher |

## Sugestões corrigidas ou rejeitadas

| Sugestão | Problema identificado | O que a equipe fez no lugar |
| --- | --- | --- |
| Integração contínua no GitHub como item obrigatório | O enunciado não exige CI | Mantida fora do escopo |
| Numeração do plano inicial: C2 = Merge Sort, C3 = índice | Invertida em relação ao enunciado | Adotada a numeração do professor em `docs/CONTRATOS.md` |
| Descrever o comportamento de empate apenas como “estabilidade” do Merge Sort | A ordem entre candidatos com mesmo `score` não depende simplesmente da ordem de entrada, há um critério explícito de desempate por `source_order` | A análise passou a usar “desempate determinístico por `source_order`”, mantendo estabilidade clássica separada desse conceito |
| a preencher | a preencher | a preencher |

## Erros identificados

Registrar erros concretos de corretude, complexidade, casos de borda, estabilidade de ordenação ou desempate que a equipe encontrou em saída de IA. Este é o item que o enunciado cobra com mais rigor, porque distingue uso crítico de uso passivo.

| Erro | Como foi detectado | Correção aplicada |
| --- | --- | --- |
| (João) Na revisão da análise de complexidade, a fórmula da C2 não trazia o termo Θ(P(m + n)) da pontuação dos candidatos | Medição do tempo por etapa em 19/09, feita com apoio de IA: a pontuação é 96% do tempo da consulta e a ordenação, 4% | Termo apontado para inclusão no relatório; os números estão em `docs/RESULTADOS.md` |
| Plano de 01/09 com as configurações C2 e C3 trocadas | Conferência contra o PDF do enunciado em 04/09 | Numeração corrigida antes de qualquer código |
| (Nadianne) Tratamento inicial do desempate como simples estabilidade da ordenação | Conferência da implementação de `sort_key`, que usa explicitamente `(-score, source_order)` | A prova passou a descrever o comportamento como desempate determinístico por `source_order` |
| a preencher | a preencher | a preencher |

## Verificação

Descrever os testes, provas, execuções e revisões por pares usados para validar cada trecho aproveitado. Código, prova ou análise sugerida por IA e não verificada não entra no trabalho.

João: cada módulo entrou com testes próprios (131 no total em 23/09, `python -m pytest`). O gabarito dos fixtures foi calculado à parte em `tests/fixtures/calcular_gabarito.py` e conferido à mão para um escore. A equivalência C1 = C2 = C3 é testada em `tests/integration/test_equivalencia.py`. Os contadores de comparações foram confrontados com a previsão assintótica (Merge Sort a 1% de P log₂ P; Insertion Sort a 9% de P²/4). O teste de mutação de 19/09 mostrou um limite da suíte, registrado em `tests/README.md`.

Nadianne: a análise formal foi conferida contra a implementação de `merge_sort.py` e `sort_key.py`. Foram adicionados três testes em `tests/unit/test_sort_key.py`, verificando prioridade por maior `score`, desempate por menor `source_order` e um caso de transitividade. Os testes específicos passaram (`3 passed`) e, em seguida, a suíte completa foi executada com `118 passed`, sem regressões.

## Contribuição individual no uso de IA

| Integrante | O que fez com apoio de IA | O que fez sem apoio de IA |
| --- | --- | --- |
| João Cosme Sena Sá | Estrutura do repositório, fixtures, fragmentação, índice invertido, conversão das consultas, documentação de testes | Decisões de escopo e divisão de frentes, revisão de cada trecho antes do commit, execução dos testes e das medições |
| Nadianne Maria dos Santos Galvão | Estruturação e revisão textual da prova de corretude; apoio na análise RAM, complexidade e recorrências, elaboração inicial dos testes de `sort_key` | Conferência da análise com o código da equipe, execução e validação dos testes, revisão das hipóteses da prova, adaptação do conteúdo ao trabalho e gravação da própria participação no vídeo |
| a preencher | a preencher | a preencher |


# Atividade 2 (AV2) — Registro complementar de uso de IA generativa

> **Escopo deste complemento:** registra apenas atividades da AV2 que puderam ser identificadas nas interações e nos artefatos examinados. As entradas da AV1 acima permanecem preservadas. Modelos exatos, usos dos demais integrantes, datas de intervenções específicas e verificações não documentadas devem ser confirmados pelos respectivos responsáveis; não se presume que a IA tenha executado ou validado autonomamente os experimentos.

## 1. Ferramentas e modelos utilizados

| Ferramenta | Integrante | Modelo | Período e observação |
| --- | --- | --- | --- |
| ChatGPT (OpenAI) | Nadianne | GPT-6 | Apoio à especificação, análise de algoritmos, revisão de documentação e preparação da apresentação, durante o desenvolvimento da AV2 (setembro–novembro de 2026). |
| Outras ferramentas eventualmente utilizadas | Cada integrante responsável | **A confirmar** | Inserir somente após confirmação de uso efetivo. |

## 2. Finalidades e localização das contribuições

| Etapa | Uso de IA como apoio | Material relacionado | Limites da atribuição |
| --- | --- | --- | --- |
| Parte A — Especificação | Organização/revisão de explicações sobre seleção de contexto sob orçamento e mochila 0/1. | `docs/ESPECIFICACAO_AV2.md` e relatório técnico. | A especificação e as decisões técnicas são de responsabilidade da equipe. |
| Parte C — Análise assintótica | Apoio à redação e explicação de complexidade, recorrências, Teorema Mestre e interpretação dos gráficos da DP e do Merge Sort. | Documentação da Parte C, gráficos e slides 7–8. | Os gráficos e resultados devem ser conferidos contra os scripts/dados produzidos pela equipe. |
| Parte D — Interpretação experimental | Apoio à leitura e revisão de métricas, às ressalvas sobre TF-IDF, `qrels` e à comunicação dos resultados. | `docs/AV2_PARTE_D_EXPERIMENTOS.md` e tabelas experimentais. | Não atribuir à IA a execução dos experimentos ou a produção dos julgamentos humanos. |
| Parte E — RAG | Revisão textual de sua relação conceitual com a seleção de contexto e explicitação de limites de uso com LLMs. | `docs/AV2_PARTE_E_RAG.md`. | O trabalho não testou geração de respostas com LLM. |
| Relatório, GitHub e apresentação | Apoio à revisão de consistência, interpretação dos comentários das PRs e estruturação de roteiro/slides. | Relatório técnico da AV2, PRs e apresentação em PDF. | A equipe verifica conteúdo, resultados, histórico de commits e versão final entregue. |

## 3. Prompts relevantes da AV2

O registro geral acima já contém três exemplos da AV1 e informa limite de até cinco prompts. Para respeitar esse limite, seguem **dois exemplos literais adicionais**, enviados por Nadianne durante a preparação da apresentação:

4. (Nadianne, AV2) "Revise a seguinte audiotoria: ===== AUDITORIA APROFUNDADA — PARTE D ===== Registros de fluxo: 1620 ..."
5. (Nadianne, AV2) "O seguinte resultado fecha ΔV e redundância na Parte D?"

Esses prompts documentam o apoio à **comunicação do trabalho**, não a geração ou a validação de resultados experimentais. Caso o enunciado exija especificamente prompts técnicos de análise/código, a equipe deve selecionar outros registros **reais** e revisar a lista total, sem reconstruir ou inventar mensagens.

## 4. Sugestões aproveitadas

| Sugestão de apoio | Como foi utilizada | Verificação necessária/responsabilidade |
| --- | --- | --- |
| Separar nos slides a análise teórica da DP e do Merge Sort da avaliação experimental de tempo e memória. | Organização dos slides da Parte C e do roteiro de apresentação. | Conferir fórmulas com as análises e figuras efetivamente versionadas. |
| Distinguir a otimização do valor TF-IDF quantizado da qualidade semântica ou da resposta de LLM. | Revisão da documentação da Parte E e dos slides sobre RAG. | Conferir formulação contra os contratos, experimentos e revisões por pares. | Ajustes de linguagem no material técnico e na apresentação. | Conferir definições nos scripts e na documentação experimental. |

## 5. Sugestões corrigidas ou rejeitadas

| Ponto revisado | Problema | Tratamento adotado |
| --- | --- | --- |
| Classificar 0,3030 ms e 7,2771 ms como "tempos médios" e 7,34/854,07 KiB como médias de memória. | Os revisores da PR #8 identificaram que os números correspondem a **medianas agregadas**, enquanto 97,78% é **média da razão de aproximação**. | Revisar os rótulos no `docs/AV2_PARTE_E_RAG.md`, na tabela do relatório em PDF e nos slides. O ajuste do Markdown foi registrado na PR #8; a conferência do PDF final continua necessária. |
| Tratar a precisão de 1,0 entre itens julgados em `qrels.csv` como evidência de superioridade semântica. | O gabarito disponível registra apenas julgamentos positivos; a ausência de um par não equivale a julgamento negativo. | Preservar a interpretação descritiva e a ressalva metodológica documentadas na revisão da Parte D (PR #9). |

## 6. Erros identificados, origem e correção

As duas questões acima foram **identificadas ou fundamentadas em revisões humanas e nos dados do projeto**; não devem ser descritas como erros produzidos pela IA sem evidência de uma saída específica. O papel da IA documentado aqui foi auxiliar na análise e redação das correções. Se houver um erro concreto em resposta de IA da AV2, anexar o prompt/saída correspondente e registrar quem o detectou e como foi validado.

## 7. Verificação e validação

- **Análise assintótica:** verificar as relações de crescimento e as fórmulas contra o código, os contratos e os gráficos da Parte C; distinguir contagens teóricas de estados de tempos realmente medidos.
- **Métricas experimentais:** confrontar afirmações com os CSVs de `experimentos/av2/processados/` e a documentação da Parte D, preservando a distinção entre média e mediana.
- **Julgamentos humanos:** o arquivo `data/qrels.csv` é uma evidência de relevância julgada, não de execução de LLM; evitar considerar automaticamente não julgados como irrelevantes.
- **Revisão por pares:** registrar as aprovações, ressalvas e correções na PR correspondente; não substituir o processo de revisão por uma resposta de IA.
- **Validação técnica:** as execuções de testes e os números reportados precisam ser vinculados aos logs/commits da equipe; este registro não afirma nova execução de testes.

## 8. Contribuição individual no uso de IA — AV2

| Integrante | Apoio de IA identificado neste registro | Decisões, verificações e entregas sob responsabilidade humana |
| --- | --- | --- |
| Nadianne Maria dos Santos Galvão | Apoio à especificação da Parte A, à interpretação/apresentação da Parte C, à revisão de documentação e métricas, e à preparação dos slides e falas. | Conferência e ajustes do conteúdo, revisão das PRs, controle dos arquivos versionados e gravação de sua participação no vídeo. |
| João Cosme Sena Sá | | Implementação/testes e revisões atribuídos ao integrante no projeto; descrever aqui somente usos reais de IA. |
| Eduardo Henrique do Lago Silva | | Confirmar atividades e verificações específicas. |
| Helena Carvalho Leal || Julgamentos e revisão da qualidade documentados no projeto não devem ser atribuídos à IA. |
| Hernandison da Silva Bispo |  | Confirmar atividades e verificações específicas. |
| Rafael Takeguma Goto | | Confirmar atividades e verificações específicas. |

**Antes da entrega:** confirmar modelos e períodos exatos, acrescentar usos dos demais integrantes quando houver, verificar a exigência de prompts do enunciado e alinhar este registro à versão oficial do relatório da AV2.
