# AV2 — Parte A: Especificação do problema

**Disciplina:** Projeto e Análise de Algoritmos (PAA) — PROCC/UFS, 2026.2 
**Projeto:** Recuperação e seleção de contexto para IA generativa em materiais educacionais abertos 
**Trilha A:** Programação dinâmica para seleção de contexto 
**Responsáveis pela Parte A:** Hernandison da Silva Bispo e Nadianne Maria dos Santos Galvão 
**Situação:** especificação elaborada; implementação, testes e resultados da AV2 ainda pendentes.

> **Escopo deste documento:** estabelecer o contrato conceitual da seleção de contexto para orientar a implementação (Parte B), a análise de complexidade (Parte C), os experimentos (Parte D) e a discussão sobre IA generativa (Parte E). Este documento não relata resultados experimentais da AV2.

## 1. Definição do problema

Dada uma consulta em português e uma lista de *chunks* recuperados de um livro-texto aberto, selecionar um subconjunto cuja soma das pontuações de relevância seja máxima, sem ultrapassar um orçamento de contexto.

O problema é modelado como **mochila 0/1**: cada *chunk* é incluído por inteiro ou excluído. Não são permitidas inclusões parciais nem múltiplas seleções de um mesmo identificador.

## 2. Corpus e continuidade com a AV1

O corpus é o livro *Pense Python*, tradução de Rodrigo Castelan Carlson da terceira edição de *Think Python*, de Allen B. Downey. O recorte processado na AV1 reúne **21 notebooks Jupyter** e **2.737 chunks**, dos quais **1.405 são Markdown** e **1.332 são código**.

A AV2 reutilizará o corpus produzido pela AV1, sem substituir ou alterar `data/processed/chunks.jsonl`. A recuperação será mantida fixa na **configuração C3 da AV1: busca linear e Merge Sort**. Os candidatos serão ordenados por maior pontuação lexical e, em empates, menor `source_order`.

O cadastro de *chunks* contém, entre outros, `chunk_id`, `source_order`, `texto`, `tipo`, `arquivo`, `capitulo`, `secao` e `n_tokens`. A pontuação de relevância é **calculada em função da consulta**, não é um campo persistente do corpus.

### Representação de candidato na AV2

| Campo lógico | Significado | Fonte |
| --- | --- | --- |
| `chunk_id` | Identificador único | Corpus AV1 |
| `texto` | Conteúdo normalizado | Corpus AV1 |
| `source_order` | Ordem original no livro | Corpus AV1 |
| `n_tokens` / `w_i` | Custo lexical positivo | Corpus AV1 |
| `score_relevancia` / `v_i` | Relevância da consulta para o chunk | Recuperação C3 |
| `origem` | Referência/metadados de localização do chunk | Corpus AV1 |

> `n_tokens` é usado como **aproximação lexical de custo**, não como número exato de tokens de um LLM. A regra efetiva de contagem deve ser conferida no código da AV1, para não confundir a tokenização de relevância com a contagem utilizada na fragmentação.

## 3. Função de relevância

Manter a pontuação lexical da AV1. Para termo `t` e *chunk* `c`:

\[
\operatorname{tf}(t,c)=
\begin{cases}
1+\ln f(t,c), & f(t,c)>0,\\
0, & f(t,c)=0.
\end{cases}
\]

\[
\operatorname{idf}(t)=\ln\left(\frac{N+1}{\operatorname{df}(t)+1}\right)+1.
\]

\[
\operatorname{score}(q,c)=\sum_{t\in\operatorname{Termos}(q)}qtf_t\,\operatorname{tf}(t,c)\,\operatorname{idf}(t).
\]

Aqui, `N` é a quantidade de chunks do corpus, `df(t)` é a quantidade de chunks que contêm o termo e `qtf_t` é sua frequência na consulta. **Somente candidatos com pontuação positiva** serão submetidos à seleção.

A pontuação é uma medida lexical estimada. Sua soma não representa necessariamente cobertura semântica, diversidade ou qualidade de uma resposta de LLM.

## 4. Entrada formal

Para uma consulta `q`, seja:

\[
C_q=\{c_1,c_2,\ldots,c_n\},\qquad n=|C_q|.
\]

Cada candidato `c_i` possui:

- valor `v_i = score(q,c_i)`, finito e não negativo;
- custo `w_i ∈ ℕ⁺`, baseado em `n_tokens`;
- identificador único e `source_order` para rastreabilidade e desempate.

O orçamento é `W ∈ ℕ₀` e a quantidade `n` é o número de **candidatos recuperados**, não o número total `N` de chunks do corpus.

Pré-condições: tipos válidos, custos inteiros positivos, valores finitos não negativos, IDs únicos e orçamento inteiro não negativo.

## 5. Saída formal

A saída é um subconjunto `S ⊆ C_q`, acompanhado de:

\[
W_S=\sum_{c_i\in S}w_i \quad\text{e}\quad V_S=\sum_{c_i\in S}v_i.
\]

Também deverão ser preservados os identificadores dos candidatos escolhidos, permitindo reconstituir a seleção. As pós-condições são `S ⊆ C_q`, cada candidato selecionado no máximo uma vez e `W_S ≤ W`.

## 6. Função objetivo

Definindo `x_i ∈ {0,1}` para indicar se `c_i` foi selecionado:

\[
\max\sum_{i=1}^{n}v_i x_i
\]

sujeito a:

\[
\sum_{i=1}^{n}w_i x_i\le W,\qquad x_i\in\{0,1\}.
\]

O objetivo é maximizar a **soma das relevâncias lexicais**, não comprovar melhoria na qualidade das respostas geradas por IA.

## 7. Corretude

Uma implementação correta da programação dinâmica deve satisfazer:

1. **Viabilidade:** selecionar apenas candidatos distintos de `C_q` e respeitar o orçamento (`W_S ≤ W`).
2. **Otimalidade:** obter o maior valor `V_S` entre todas as soluções viáveis.

Se `ℱ = {S′ ⊆ C_q | ∑_{c_i∈S′} w_i ≤ W}`, então uma solução ótima `S*` satisfaz:

\[
\sum_{c_i\in S^*}v_i\ge\sum_{c_i\in S'}v_i
\quad\forall S'\in\mathcal F.
\]

A demonstração formal da programação dinâmica e os testes contra entradas pequenas com resultado conhecido pertencem à Parte B. A abordagem gulosa precisa ser **viável**, mas não necessariamente ótima.

## 8. Baseline guloso

A linha de base ordenará os candidatos em ordem decrescente da razão:

\[
r_i=\frac{v_i}{w_i}.
\]

Cada candidato será examinado uma única vez nessa ordem. Caso `w_i` caiba no orçamento restante, será selecionado integralmente e seu custo descontado; caso contrário, será ignorado, **sem encerrar** a avaliação dos candidatos seguintes.

Desempates na razão: **(1)** maior valor absoluto `v_i`; **(2)** menor `source_order`.

A estratégia é determinística sob uma entrada válida, mas não garante o máximo global para a mochila 0/1.

## 9. Desempates da programação dinâmica

Entre soluções com a mesma relevância ótima, escolher:

1. a solução com **menor custo total**;
2. persistindo o empate, o conjunto cuja **sequência de `source_order` ordenada crescentemente** seja lexicograficamente menor.

A implementação deve manter esse critério consistente inclusive na reconstrução da solução.

## 10. Casos de borda

| Cenário | Comportamento esperado |
| --- | --- |
| `C_q` vazio | `S = ∅`, `W_S = 0` e `V_S = 0` |
| Consulta sem resultados positivos | Retornar seleção vazia |
| `W = 0` | Retornar seleção vazia (custos positivos) |
| Todos os `w_i > W` | Retornar seleção vazia |
| A soma dos custos cabe no orçamento | Selecionar todos os candidatos de relevância positiva |
| Candidato individual `w_i > W` | Não selecionar esse item; outros continuam elegíveis |
| Mesmo `chunk_id` repetido | Rejeitar como entrada inválida |
| Mesmo texto com IDs diferentes | Preservar candidatos; analisar redundância nos experimentos |
| Duas ou mais soluções ótimas | Aplicar desempate da programação dinâmica |
| Razões `v_i/w_i` empatadas | Aplicar desempate do guloso |
| `v_i = 0` | Pode ser removido antes da seleção |

Esses são **requisitos de teste**, não resultados já verificados.

## 11. Parâmetros experimentais preliminares

| Parâmetro | Proposta inicial |
| --- | --- |
| Corpus | 2.737 chunks da AV1 |
| Consultas | 30 consultas de `data/queries.csv` |
| Recuperação | C3: busca linear + Merge Sort, configuração fixa |
| Orçamentos `W` | 256, 512 e 1.024 unidades lexicais |
| Candidatos por consulta `n` | 10, 30 e 50, limitados à quantidade de resultados positivos |
| Repetições | No mínimo 3 por cenário |
| Algoritmo principal | Programação dinâmica, mochila 0/1 |
| Baseline | Guloso por relevância/custo |
| Qualidade | `V_S`, `W_S`, utilização do orçamento, redundância e diferença de relevância |
| Computação | Tempo de seleção, tempo do fluxo completo e memória aproximada |

A diferença de relevância pode ser expressa como `ΔV = V_DP − V_guloso`; uma comparação relativa requer tratamento explícito do caso em que `V_DP = 0`.

A configuração de recuperação, os scores, os custos, os candidatos e os orçamentos devem ser iguais para ambos os algoritmos em cada cenário. A execução dos experimentos ocorrerá na Parte D. Os valores da tabela ainda estão sujeitos à validação de viabilidade e de contagem dos custos.

## 12. Decisões metodológicas e limitações

- **Continuidade com a AV1:** reutilização do corpus, das consultas e da configuração C3.
- **Comparabilidade:** os dois seletores recebem precisamente a mesma entrada por cenário.
- **Unidade de custo:** `n_tokens` como contagem lexical aproximada, **não** tokens reais de LLM.
- **Determinismo:** desempates definidos para os dois algoritmos.
- **Interpretação:** maximizar a soma de TF-IDF não implica maximizar cobertura de tópicos, eliminar redundância ou melhorar automaticamente as respostas geradas.
- **Status:** especificação e planejamento, sem alegação de implementação ou resultados já realizados para a AV2.

## 13. Relação com as próximas partes

| Etapa | Uso desta especificação |
| --- | --- |
| **Parte B** | Implementar DP e guloso; provar corretude; validar pré e pós-condições |
| **Parte C** | Analisar tempo, memória e comportamento com `n` e `W` |
| **Parte D** | Executar experimentos controlados, medir métricas e discutir resultados |
| **Parte E** | Relacionar o modelo ao contexto de IA generativa e às limitações semânticas |

## 14. Referências e rastreabilidade

- **Downey, Allen B.** *Think Python*, 3ª ed.; tradução brasileira *Pense Python*, Rodrigo Castelan Carlson. Fonte: <https://rodrigocarlson.github.io/PensePython3ed/>.
- **Kleinberg, Jon; Tardos, Éva.** *Algorithm Design*. Pearson/Addison-Wesley, 2005/2006. Referência conceitual para mochila 0/1 e comparação com decisões gulosas.
- **Manning, Christopher D.; Raghavan, Prabhakar; Schütze, Hinrich.** *Introduction to Information Retrieval*. Cambridge University Press, 2008. Referência para recuperação lexical.
- Artefatos da AV1: `data/processed/chunks.jsonl`, `data/queries.csv`, `docs/CONTRATOS.md`, `data/README.md` e código de recuperação C3.

> **Nota de integração:** esta versão Markdown resume e operacionaliza as decisões da Parte A. O texto LaTeX/PDF aprovado pelo grupo permanece a referência formal do relatório; eventuais mudanças de parâmetros ou nomenclatura precisam ser refletidas nos dois artefatos.
