# Planejamento da Atividade 2 (AV2)

**Disciplina:** Projeto e Análise de Algoritmos (PAA) — PROCC/UFS, 2026.2 
**Tema:** Recuperação e seleção de contexto para IA generativa em materiais educacionais abertos 
**Trilha:** A — Programação dinâmica para seleção de contexto 
**Branch de trabalho:** `av2-programacao-dinamica` 
**Entrega final prevista:** 04/11/2026 
**Apresentação prevista:** 05/11/2026

> Este planejamento registra a divisão de trabalho e os prazos internos acordados pela equipe. Os prazos internos não substituem o cronograma oficial da disciplina. As atribuições indicam responsabilidades, não entregas já concluídas.

## 1. Objetivo da AV2

Estender o protótipo desenvolvido na AV1 com uma etapa de **seleção de chunks sob orçamento limitado de unidades lexicais**, formulada como o problema da **mochila 0/1**.

Serão comparadas duas estratégias sobre os mesmos dados de entrada:

- **Programação dinâmica (PD):** maximização exata da soma dos escores de relevância sob o orçamento, considerando o modelo definido.
- **Baseline guloso:** processamento dos candidatos por ordem decrescente da razão relevância/custo (`v_i / w_i`), selecionando integralmente cada chunk que couber no orçamento restante.

A AV2 reutiliza o corpus e as consultas da AV1. A recuperação será mantida fixa na **configuração C3** (busca linear e Merge Sort), de modo a concentrar a comparação nas estratégias de seleção.

## 2. Equipe e responsabilidades

| Parte | Atividade | Responsáveis | Prazo interno | Situação |
| --- | --- | --- | --- | --- |
| A | Especificação formal do problema, baseline e parâmetros experimentais | Hernandison da Silva Bispo; Nadianne Maria dos Santos Galvão | 23/10/2026 | Documento elaborado; disponibilização e revisão pelo grupo |
| B | Implementação da programação dinâmica e do guloso; testes e prova de corretude | João Cosme Sena Sá; Eduardo Henrique do Lago Silva; Rafael Takeguma Goto | 26/10/2026 | Planejada |
| C | Análise de complexidade temporal e espacial das estratégias | Eduardo Henrique do Lago Silva; Nadianne Maria dos Santos Galvão | 28/10/2026 | Planejada |
| D | Execução dos experimentos, tabelas, gráficos e discussão quantitativa | João Cosme Sena Sá; Eduardo Henrique do Lago Silva; Helena Carvalho Leal | 30/10/2026 | Planejada |
| E | Relação com IA generativa, limitações, interpretação dos resultados | Helena Carvalho Leal; Hernandison da Silva Bispo; Rafael Takeguma Goto | 02/11/2026 | Planejada |
| Integração | Revisão cruzada, consolidação do relatório, reprodutibilidade e apresentação | Toda a equipe | Até 04/11/2026 | Planejada |

**Atenção:** concluir uma parte exige não só enviar o texto, mas disponibilizar os arquivos correspondentes e comunicar eventuais mudanças nos contratos.

## 3. Dependências e sequência de integração

```text
AV1: corpus + queries + pontuação lexical + recuperação C3
                        |
                        v
Parte A: especificação e contratos da AV2
                        |
                        v
Parte B: programação dinâmica + guloso + testes
           |                         |
           v                         v
Parte C: complexidade         Parte D: experimentos
           |                         |
           +------------+------------+
                        |
                        v
Parte E: análise da relação com IA generativa
                        |
                        v
Relatório, revisão, apresentação e entrega
```

A Parte C pode começar sobre o pseudocódigo e as recorrências, mas suas conclusões devem ser conferidas contra a implementação efetiva da Parte B. A Parte D depende de algoritmos testados e de entradas equivalentes.

## 4. Contratos metodológicos compartilhados

1. **Dados fixos:** corpus da AV1, com 2.737 chunks gerados a partir de 21 notebooks, e 30 consultas registradas em `data/queries.csv`.
2. **Recuperação fixa:** configuração C3 da AV1; utilizar apenas candidatos com escore lexical positivo, preservando `chunk_id` e `source_order`.
3. **Valor do candidato:** `v_i`, escore lexical não negativo relativo à consulta.
4. **Custo:** `w_i`, obtido inicialmente de `n_tokens` da AV1. É uma contagem de **unidades lexicais**, não uma medição exata de tokens de LLM.
5. **Orçamento:** `W`, inteiro não negativo, com seleção inteira de chunks (`x_i` em `{0,1}`).
6. **Objetivo:** maximizar `V_S = Σ(v_i x_i)`, sujeito a `W_S = Σ(w_i x_i) ≤ W`.
7. **Comparação justa:** programação dinâmica e guloso devem receber a mesma lista de candidatos, escores, custos e orçamento em cada cenário.
8. **Empates na PD:** entre soluções com relevância total máxima, preferir menor custo; persistindo empate, preferir a sequência crescente de `source_order` lexicograficamente menor.
9. **Empates no guloso:** maior razão `v_i/w_i`; em empate, maior `v_i`; persistindo, menor `source_order`.
10. **Identificadores duplicados:** rejeitar entradas com `chunk_id` repetido. Textos idênticos com identificadores distintos permanecem como candidatos distintos; a redundância deve ser discutida nos experimentos.

A especificação conceitual fica em `docs/ESPECIFICACAO_AV2.md`; as interfaces e os testes obrigatórios ficam em `docs/CONTRATOS_AV2.md`. Os contratos originais da AV1 permanecem em `docs/CONTRATOS.md`.

## 5. Entregáveis por parte

### Parte A — Especificação

- [x] Definir problema de seleção e motivação no contexto do protótipo da AV1.
- [x] Formalizar candidatos, custos, relevância, orçamento, função objetivo e restrições.
- [x] Descrever o baseline guloso e os critérios de corretude.
- [x] Documentar casos de borda, empates e parâmetros experimentais preliminares.
- [ ] Revisar coletivamente a especificação e registrar eventuais mudanças acordadas.
- [ ] Versionar a especificação e os contratos na branch da AV2, com evidências no histórico de commits.

### Parte B — Implementação e corretude

- [ ] Integrar candidatos produzidos pela recuperação C3 sem alterar a pontuação da AV1.
- [ ] Implementar a seleção por programação dinâmica para mochila 0/1.
- [ ] Implementar o baseline guloso por relevância/custo.
- [ ] Aplicar regras de desempate de forma determinística.
- [ ] Implementar testes unitários e de integração, incluindo todos os casos de borda.
- [ ] Conferir o valor ótimo da PD em instâncias pequenas por enumeração exaustiva ou casos com solução conhecida.
- [ ] Registrar prova ou argumento formal de corretude coerente com o algoritmo implementado.

### Parte C — Complexidade

- [ ] Analisar a complexidade de tempo da programação dinâmica em função de `n` e `W`.
- [ ] Analisar consumo de memória, distinguindo a tabela completa de possíveis otimizações efetivamente implementadas.
- [ ] Analisar o custo da ordenação e da seleção gulosa.
- [ ] Diferenciar o custo de recuperação C3 do custo exclusivo da seleção.
- [ ] Conferir a análise contra as estruturas de dados e os laços reais da implementação.

### Parte D — Experimentos

- [ ] Confirmar os conjuntos de candidatos e orçamentos viáveis antes das medições.
- [ ] Executar os cenários sobre as mesmas 30 consultas e entradas equivalentes para PD e guloso.
- [ ] Registrar tempos, memória, relevância acumulada, custo usado e utilização do orçamento.
- [ ] Medir a diferença de relevância entre PD e guloso e analisar empates.
- [ ] Examinar redundância entre chunks quando houver método explícito de avaliação.
- [ ] Gerar tabelas, gráficos e arquivos brutos reprodutíveis.
- [ ] Relatar limitações e ameaças à validade, sem inferir melhora de respostas de LLM a partir apenas de TF-IDF acumulado.

### Parte E — IA generativa e conclusão

- [ ] Explicar como a seleção sob orçamento pode anteceder a composição de contexto em um pipeline RAG.
- [ ] Diferenciar relevância lexical aditiva de cobertura semântica, diversidade e qualidade final de resposta.
- [ ] Discutir as limitações do custo em unidades lexicais frente aos tokenizadores de LLMs.
- [ ] Consolidar os resultados efetivamente medidos e as conclusões suportadas pelos dados.
- [ ] Preparar a comunicação dos resultados para apresentação.

## 6. Planejamento experimental inicial

| Dimensão | Planejamento |
| --- | --- |
| Consultas | 30, reutilizadas da AV1 |
| Corpus | 2.737 chunks da AV1 |
| Recuperação | C3, mantida fixa |
| Candidatos por consulta | `n = 10, 30, 50`, limitados aos resultados com escore positivo |
| Orçamentos | `W = 256, 512, 1.024` unidades lexicais |
| Repetições | No mínimo três por cenário |
| Estratégias | Programação dinâmica e guloso |
| Qualidade da seleção | `V_S`, `W_S`, utilização do orçamento, diferença de relevância e redundância quando mensurável |
| Custo computacional | Tempo de seleção, tempo total do fluxo e consumo aproximado de memória |

Esses valores são **preliminares**, não resultados. A Parte D verificará se os parâmetros são suficientes para gerar cenários informativos e computacionalmente viáveis.

## 7. Fluxo de trabalho no GitHub

1. Utilizar `av2-programacao-dinamica` como branch de integração da AV2, mantendo a AV1 preservada na `main`.
2. Para tarefas paralelas, preferir branches de trabalho derivadas da branch da AV2, quando acordado pelo grupo.
3. Abrir pull requests ou realizar integrações revisadas; evitar sobrescrever arquivos compartilhados sem comunicar aos demais.
4. Manter commits com escopo claro, por exemplo: `docs(av2): adiciona planejamento`, `feat(av2): implementa mochila 0-1` e `test(av2): cobre casos de borda`.
5. Atualizar `docs/CONTRIBUICOES.md` com arquivos, commits/PRs e evidências individuais da AV2, mantendo o histórico da AV1.
6. Antes da entrega, executar a suíte de testes, conferir reprodutibilidade, consolidar relatório e registrar a versão final acordada pela equipe.

## 8. Critérios de integração antes da entrega

- [ ] Documentação e código descrevem as mesmas fórmulas, interfaces e políticas de desempate.
- [ ] PD e guloso utilizam candidatos idênticos em cada comparação.
- [ ] Nenhuma seleção ultrapassa `W`.
- [ ] A PD foi verificada em casos pequenos com ótimo conhecido.
- [ ] Testes de borda aprovados.
- [ ] Experimentos documentam configuração, ambiente, repetições e dados brutos.
- [ ] Relatório distingue resultados obtidos de hipóteses e parâmetros planejados.
- [ ] Contribuições individuais revisadas e registradas.
- [ ] Entrega e apresentação organizadas dentro dos prazos oficiais.

---

**Documentos relacionados:** `README.md`, `docs/ESPECIFICACAO_AV2.md`, `docs/CONTRATOS_AV2.md`, `docs/CONTRATOS.md` (AV1) e `docs/CONTRIBUICOES.md`.
