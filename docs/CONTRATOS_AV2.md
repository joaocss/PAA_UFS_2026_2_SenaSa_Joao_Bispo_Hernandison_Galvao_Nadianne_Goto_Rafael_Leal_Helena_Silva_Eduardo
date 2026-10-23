# AV2 — Contratos técnicos de seleção de contexto

**Projeto:** Recuperação e seleção de contexto para IA generativa em materiais educacionais abertos 
**Disciplina:** Projeto e Análise de Algoritmos (PAA) — PROCC/UFS, 2026.2 
**Trilha A:** Programação dinâmica para seleção de contexto 
**Estado:** contrato proposto a partir da Parte A; implementação e validação da AV2 pendentes.

> **Como utilizar:** este documento orienta a Parte B (implementação), a Parte C (análise) e a Parte D (experimentos). Em caso de divergência, alinhar com `docs/ESPECIFICACAO_AV2.md` e com o relatório da Parte A **antes de modificar o código**. Os contratos existentes de `docs/CONTRATOS.md` continuam valendo para a AV1.

## Contrato 01 — Continuidade com a AV1

- **Corpus:** `data/processed/chunks.jsonl`, produzido pela AV1, sem sobrescrevê-lo na AV2.
- **Consultas:** `data/queries.csv`, com as 30 consultas predefinidas.
- **Recuperação:** configuração **C3** — busca linear e Merge Sort da AV1.
- **Pontuação:** TF-IDF lexical da AV1, sem refazer a fórmula para cada seletor.
- **Ordenação dos resultados recuperados:** score decrescente; empate pelo menor `source_order`.
- **Candidatos elegíveis:** apenas chunks com score de relevância positivo.
- **Separação de responsabilidades:** recuperação forma candidatos; seleção (DP ou guloso) escolhe subconjunto. Não alterar a recuperação para favorecer qualquer seletor.

A quantidade `N` de chunks do corpus (2.737 no recorte da AV1) **não** é a mesma variável `n`, que indica a quantidade de candidatos submetidos ao seletor em uma consulta.

## Contrato 02 — Dados de entrada para a seleção

Entrada lógica de cada chamada:

| Campo | Tipo esperado | Regra |
| --- | --- | --- |
| `candidatos` | sequência de candidatos | Pode ser vazia; cada `chunk_id` deve ser único |
| `chunk_id` | `str` | Identifica o chunk original da AV1 |
| `source_order` | `int` | Índice de origem usado no desempate |
| `texto` | `str` | Texto normalizado original, se necessário para exibição ou redundância |
| `origem` | metadados opcionais | Referência de arquivo/capítulo/seção, para rastreabilidade |
| `score_relevancia` (`v_i`) | número real finito, não negativo | Gerado para a consulta; candidatos de score zero são filtrados antes da seleção |
| `n_tokens` (`w_i`) | inteiro positivo | Custo do candidato, obtido do corpus AV1 |
| `orcamento` (`W`) | inteiro não negativo | Limite máximo de custo da seleção |

**Pré-condições:** `W >= 0`, `w_i >= 1`, valores finitos, identificadores não repetidos. Valores `NaN`, infinitos, custos fracionários ou negativos, orçamento negativo e IDs duplicados são inválidos e deverão produzir erro explícito, em vez de um resultado silenciosamente inconsistente.

`n_tokens` é tratado como **unidade lexical aproximada** de custo de contexto, **não** como quantidade exata de tokens de um LLM. A regra efetiva de contagem deve ser conferida no código da AV1 antes da integração.

> **Importante:** `score_relevancia` não é um campo armazenado originalmente em `chunks.jsonl`: é associado ao candidato depois da recuperação, para uma consulta específica. O nome das classes/funções Python é uma decisão da Parte B; os campos e comportamentos deste contrato são a interface lógica obrigatória.

## Contrato 03 — Problema de otimização (mochila 0/1)

Para `n` candidatos, cada item `i` tem valor `v_i`, custo `w_i` e variável de decisão `x_i ∈ {0,1}`.

Maximizar:

\[
V_S = \sum_{i=1}^{n}v_ix_i
\]

Sujeito a:

\[
W_S = \sum_{i=1}^{n}w_ix_i \leq W.
\]

Cada chunk é selecionado **integralmente ou não selecionado**. O mesmo `chunk_id` nunca pode aparecer duas vezes na saída. Não existe seleção parcial de um chunk.

## Contrato 04 — Saída de ambos os algoritmos

A saída lógica deve permitir recuperar:

| Campo | Significado |
| --- | --- |
| `chunk_ids_selecionados` | Identificadores distintos dos chunks escolhidos |
| `custo_total` (`W_S`) | Soma dos `n_tokens` escolhidos |
| `relevancia_total` (`V_S`) | Soma dos scores escolhidos |

**Pós-condições comuns:**

1. `S ⊆ C_q` e nenhum identificador selecionado se repete.
2. `0 <= W_S <= W`.
3. `V_S` e `W_S` correspondem às somas dos itens efetivamente selecionados.
4. Para entrada vazia ou sem item viável, a saída é vazia, com `W_S = 0` e `V_S = 0`.
5. A apresentação final pode ordenar os itens selecionados por `source_order` crescente; isso não altera as somas nem o conjunto selecionado.

## Contrato 05 — Programação dinâmica (algoritmo principal)

A DP deve produzir uma solução **viável e ótima** para a função objetivo definida.

Uma recorrência de referência para o valor ótimo é:

\[
DP[i,b] =
\begin{cases}
DP[i-1,b], & w_i > b,\\
\max\bigl(DP[i-1,b],\;v_i+DP[i-1,b-w_i]\bigr), & w_i\le b.
\end{cases}
\]

Com condições-base `DP[0,b] = 0` e `DP[i,0] = 0`. Esta recorrência expressa os valores ótimos; o algoritmo também deve reconstruir os itens selecionados e respeitar o critério de desempate.

**Desempate entre soluções ótimas:**

1. maior relevância total (`V_S`);
2. em igualdade de `V_S`, menor custo total (`W_S`);
3. persistindo a igualdade, sequência **crescente** dos `source_order` selecionados **lexicograficamente menor**.

A Parte B deve explicitar como trata empates numéricos de valores calculados em ponto flutuante e assegurar que a política usada na reconstrução corresponde ao resultado apresentado. Uma abordagem que armazene apenas valores ótimos sem informações suficientes para desempatar/reconstruir **não satisfaz sozinha** esse contrato.

A prova de corretude e a análise formal ficarão, respectivamente, nas Partes B e C.

## Contrato 06 — Estratégia gulosa (baseline)

Para cada candidato, calcular:

\[
r_i = \frac{v_i}{w_i}.
\]

Ordenar os candidatos por:

1. `r_i` decrescente;
2. em empate, `v_i` decrescente;
3. persistindo empate, `source_order` crescente.

Percorrer **todos** os candidatos nessa ordem:

- Se o candidato couber no orçamento restante, selecioná-lo integralmente e descontar o custo.
- Se não couber, ignorá-lo e **continuar** para o próximo.

O guloso deve respeitar o orçamento, mas **não precisa alcançar o ótimo** da mochila 0/1. Não utilizar a versão fracionária da mochila.

## Contrato 07 — Casos obrigatórios de teste

| Caso | Resultado esperado |
| --- | --- |
| Lista de candidatos vazia | Seleção vazia, custo 0 e valor 0 |
| Consulta sem score positivo | Seleção vazia |
| `W = 0` | Seleção vazia |
| Todos os itens com `w_i > W` | Seleção vazia |
| Soma dos custos de todos os itens positivos `<= W` | Selecionar todos os itens positivos |
| Um item com `w_i > W` | Ignorar o item, mantendo os demais elegíveis |
| Identificador repetido | Rejeitar entrada inválida |
| Mesmo texto com IDs distintos | Tratar como itens distintos; avaliar redundância posteriormente |
| `v_i = 0` | Filtrar antes da seleção, sem perda de valor objetivo |
| Empates de solução ótima da DP | Aplicar desempate por custo e `source_order` |
| Empates de razão do guloso | Aplicar desempate por valor e `source_order` |
| Entradas inválidas (`W < 0`, custos não positivos, `NaN`) | Rejeitar explicitamente |

**Exemplo sintético para diferenciar os algoritmos:** com orçamento `W=50` e candidatos `(w,v) = (10,60), (20,100), (30,120)`, o guloso pela razão escolhe os dois primeiros (`W_S=30`, `V_S=160`), enquanto a solução ótima escolhe o segundo e o terceiro (`W_S=50`, `V_S=220`). Usar como fixture didática; **não é resultado do corpus**.

Também comparar a DP com enumeração exaustiva em instâncias pequenas, para verificar a otimalidade e os critérios de desempate.

## Contrato 08 — Experimentos planejados (Parte D)

| Parâmetro | Valores preliminares |
| --- | --- |
| Consultas | 30, de `data/queries.csv` |
| Quantidade de candidatos | 10, 30 e 50 por consulta, limitada aos resultados positivos |
| Orçamentos | `W ∈ {256, 512, 1024}` unidades lexicais |
| Repetições | No mínimo 3 por cenário |
| Algoritmos | Programação dinâmica e guloso |
| Indicadores de seleção | `V_S`, `W_S`, utilização `W_S/W` quando `W>0`, redundância e `ΔV = V_DP − V_guloso` |
| Indicadores computacionais | Tempo de seleção, tempo total do fluxo e consumo aproximado de memória |

Ambos os algoritmos deverão receber **exatamente os mesmos candidatos, scores, custos e orçamento** em cada cenário. A configuração C3 deve permanecer fixa, para que os resultados comparem os seletores, não os recuperadores.

- Definir previamente metodologia de medição de tempo e memória, ambiente, aquecimento (se usado) e semente.
- Registrar resultados por consulta, orçamento, tamanho dos candidatos, algoritmo e repetição, antes de agregar estatísticas.
- Para `W = 0`, a taxa `W_S/W` é indefinida; não dividir por zero.
- A diferença `ΔV` é não negativa se a DP estiver correta e receber a mesma entrada válida; comparações relativas devem tratar `V_DP = 0`.
- Os valores são **preliminares**: validar viabilidade antes do experimento definitivo, registrando quaisquer mudanças.

## Contrato 09 — Organização e compatibilidade

- **Preservar** o pipeline e os arquivos da AV1. Não substituir `docs/CONTRATOS.md` por este documento.
- Implementar o seletor em módulo isolado do recuperador, com testes unitários próprios e interfaces importáveis.
- Não registrar no README/relatório como concluída uma implementação ou medição ainda não realizada.
- Versionar decisões novas, mantendo a Parte A (`docs/ESPECIFICACAO_AV2.md`), os contratos, a implementação e os resultados coerentes.
- Sempre que for alterado o significado do custo, a política de desempate ou a seleção de candidatos, alinhar com o grupo e atualizar os testes e a documentação.

## Responsabilidades e próximos passos

- **Parte B:** implementar DP, guloso, reconstrução, validação da entrada e testes.
- **Parte C:** analisar complexidade em função de `n` e `W`, inclusive custos de memória e de reconstrução/desempate.
- **Parte D:** executar protocolo comparativo e discutir métricas.
- **Parte E:** relacionar os resultados ao uso em IA generativa, sem confundir soma lexical com avaliação da resposta de um LLM.

**Referências internas:** `docs/ESPECIFICACAO_AV2.md`, `docs/CONTRATOS.md`, `data/README.md`, `data/queries.csv` e `data/processed/chunks.jsonl`.
