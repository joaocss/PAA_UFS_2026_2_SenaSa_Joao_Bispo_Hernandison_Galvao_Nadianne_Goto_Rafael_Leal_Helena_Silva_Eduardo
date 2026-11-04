
# AV2 — Parte E: Relação com IA generativa e RAG

## 1. Objetivo

Esta etapa discute a aplicação dos algoritmos de seleção de contexto desenvolvidos na AV2 em sistemas de geração aumentada por recuperação (*Retrieval-Augmented Generation* — RAG).

O objetivo é analisar como a programação dinâmica para mochila 0/1 e a estratégia gulosa por densidade podem apoiar a escolha de fragmentos textuais (*chunks*) sob um orçamento limitado de contexto.

A Parte E utiliza os resultados experimentais da Parte D. Não foram realizados experimentos de geração de respostas com modelos de linguagem nesta etapa.

## 2. Integração com o pipeline RAG

A AV2 reutiliza a configuração de recuperação C3 da AV1, composta por busca linear, pontuação lexical TF-IDF e ordenação por Merge Sort.

O fluxo conceitual é:

1. Receber uma consulta do usuário.
2. Recuperar e ranquear os chunks do corpus.
3. Selecionar candidatos relevantes.
4. Aplicar a estratégia de seleção sob orçamento.
5. Organizar os chunks escolhidos para compor o contexto de um prompt.
6. Encaminhar o contexto a um LLM, em uma integração futura.

A implementação e os experimentos desta atividade abrangem o fluxo até a etapa de seleção. A utilização do contexto por um LLM é discutida como possibilidade de integração, não como funcionalidade experimentalmente validada.

## 3. Formulação da seleção de contexto

Cada candidato possui um custo lexical `w_i`, uma pontuação de relevância TF-IDF `v_i` e metadados de origem.

A seleção busca maximizar:

`V(S) = soma(v_i), para i pertencente a S`

sujeita a:

`Soma(w_i) <= W`

em que `W` representa o orçamento máximo de unidades lexicais.

A programação dinâmica resolve a mochila 0/1 de acordo com os valores computacionais quantizados por `round(1000 * v_i)`. Portanto, sua garantia de otimalidade corresponde à função objetivo quantizada.

A estratégia gulosa por densidade ordena os candidatos pela razão entre valor quantizado e custo lexical, selecionando aqueles que cabem no orçamento restante. Essa abordagem é computacionalmente menos custosa, mas não garante a solução ótima da mochila 0/1.

## 4. Resultados experimentais relevantes

A Parte D avaliou cinco estratégias de seleção em 270 cenários, considerando:

- 30 consultas da AV1;
- `n = {10, 30, 50}` candidatos;
- `W = {256, 512, 1024}` unidades lexicais;
- 6.750 medições individuais de seleção;
- 1.620 medições complementares do fluxo completo.

A comparação principal envolve S3, guloso por densidade, e S5, programação dinâmica.

Para `n = 50` e `W = 1024`, foram observados:

| Métrica | S3 — Guloso | S5 — DP |
|---|---:|---:|
| Mediana do tempo de seleção | 0,3030 ms | 7,2771 ms |
| Mediana do pico de alocações Python rastreadas | 7,34 KiB | 854,07 KiB |
| Razão média de aproximação ao ótimo quantizado | 97,78% | 100% |

A programação dinâmica alcançou o valor ótimo quantizado. O guloso por densidade apresentou menor custo de seleção, mantendo, nesse cenário, uma aproximação média elevada em relação à solução ótima.

Os valores de tempo e alocações rastreadas apresentados na tabela são medianas agregadas; a razão de aproximação é uma média. Esses resultados caracterizam o cenário experimental informado e não devem ser generalizados automaticamente para outros corpora, tamanhos de entrada ou modelos de linguagem.

## 5. Implicações para aplicações com LLMs

### 5.1 Orçamento de contexto

A seleção sob orçamento pode auxiliar no controle da quantidade de conteúdo encaminhado a um modelo de linguagem.

Entretanto, o custo `n_tokens` utilizado na AV2 corresponde a unidades lexicais e não necessariamente à tokenização de um LLM específico.

Assim, os resultados não permitem estimar diretamente custos de API, quantidade exata de tokens processados ou redução financeira.

### 5.2 Custo computacional

Na seleção isolada, a programação dinâmica apresentou maior custo temporal e maior pico de alocações Python rastreadas do que a estratégia gulosa no cenário destacado.

Na avaliação do fluxo completo, a recuperação C3 representou uma parcela predominante do tempo de processamento. Consequentemente, diferenças entre seletores podem ser menos relevantes para a latência total do fluxo avaliado.

Não foram medidos tempos de inferência, geração de tokens ou latência de respostas de um LLM. Sem a geração e a avaliação das respostas, também não foi validado se o contexto selecionado fornece evidências suficientes para fundamentar corretamente as afirmações de um modelo de linguagem.

### 5.3 Qualidade do contexto

A maximização da relevância TF-IDF favorece candidatos com maior correspondência lexical à consulta.

Todavia, relevância lexical não é equivalente a relevância semântica, cobertura de evidências ou utilidade efetiva para a geração de respostas.

A avaliação complementar não identificou pares de chunks selecionados com similaridade lexical de Jaccard igual ou superior a 0,8 nas condições examinadas. Isso não comprova ausência de redundância semântica.

## 6. Riscos e limitações

Os principais riscos de utilizar a abordagem diretamente em RAG incluem:

- **Perda de evidências:** chunks relevantes que não foram recuperados por C3 não podem ser selecionados posteriormente.
- **Viés lexical:** a pontuação TF-IDF pode favorecer coincidências de palavras sem representar adequadamente o significado.
- **Dependência entre fragmentos:** um trecho isolado pode depender de definições, exemplos ou código presentes em outros chunks.
- **Redundância semântica:** a função objetivo aditiva não penaliza explicitamente informações semanticamente repetidas.
- **Diferença de tokenização:** o orçamento lexical não garante respeito ao limite real de tokens de um modelo específico.
- **Custo da programação dinâmica:** a dependência pseudopolinomial de `W` pode limitar a escalabilidade para orçamentos elevados.

Além disso, os experimentos utilizaram um único corpus educacional, restringindo a generalização dos resultados.

## 7. Critérios para escolha da estratégia

A programação dinâmica é adequada quando a prioridade é maximizar a função objetivo quantizada e quando os limites de candidatos, orçamento e memória permitem seu processamento.

A estratégia gulosa por densidade constitui uma alternativa quando tempo de seleção e consumo de memória são fatores prioritários e uma solução aproximada é aceitável.

A escolha depende do cenário operacional. Os experimentos desta AV2 não estabelecem superioridade de uma estratégia quanto à qualidade das respostas produzidas por LLMs.

## 8. Trabalhos futuros

Uma avaliação posterior poderá:

1. Integrar os seletores a um pipeline RAG com um LLM real.
2. Utilizar a tokenização específica do modelo empregado.
3. Medir relevância das evidências, fidelidade factual e cobertura das respostas.
4. Comparar latência total, custo de inferência e quantidade de tokens.
5. Investigar critérios de diversidade e redução de redundância semântica.
6. Avaliar a generalização com outros corpora e consultas.

## 9. Síntese

A AV2 demonstra experimentalmente um compromisso entre otimalidade da função objetivo quantizada e custo computacional da seleção de contexto.

A programação dinâmica fornece uma referência ótima para a formulação adotada, enquanto o guloso por densidade apresentou elevada aproximação média e menor custo de seleção no cenário destacado.

Para aplicações em RAG, os resultados fornecem evidências sobre a etapa de seleção, mas não comprovam melhorias na geração de respostas. Essa distinção é essencial para uma interpretação metodologicamente adequada do trabalho.

## Referências

- CORMEN, T. H. et al. *Introduction to Algorithms*. 4. ed. MIT Press, 2022.
- KLEINBERG, J.; TARDOS, É. *Algorithm Design*. Pearson/Addison-Wesley, 2006.
- LEWIS, P. et al. *Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks*. NeurIPS, 2020. https://arxiv.org/abs/2005.11401
- MANNING, C. D.; RAGHAVAN, P.; SCHÜTZE, H. *Introduction to Information Retrieval*. Cambridge University Press, 2008.

## Evidências no repositório

- `docs/ESPECIFICACAO_AV2.md`
- `docs/AV2_PARTE_D_EXPERIMENTOS.md`
- `experimentos/av2/`
- `scripts/av2/`
