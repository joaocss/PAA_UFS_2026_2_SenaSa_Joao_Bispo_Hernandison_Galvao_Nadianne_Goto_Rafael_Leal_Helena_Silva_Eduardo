# AV2 — Contratos técnicos de seleção de contexto

**Projeto:** Recuperação e seleção de contexto para IA generativa em materiais educacionais abertos
**Disciplina:** Projeto e Análise de Algoritmos (PAA) — PROCC/UFS, 2026.2
**Trilha A:** Programação dinâmica para seleção de contexto
**Estado (23/10/2026):** contratos 01–09 definidos na Parte A; implementação da Parte B em revisão/integração; validação experimental da Parte D pendente.

> **Como utilizar:** este documento orienta a Parte B (implementação), a Parte C (análise) e a Parte D (experimentos). Em caso de divergência, alinhar com `docs/ESPECIFICACAO_AV2.md` e com o relatório da Parte A **antes de modificar o código**. Os contratos existentes de `docs/CONTRATOS.md` continuam valendo para a AV1.

## Contrato 01 — Continuidade com a AV1

- **Corpus usado pela AV2:** `data/chunks.jsonl`, arquivo versionado. Sua equivalência ao corpus processado da AV1 (`data/processed/chunks.jsonl`) deve ser conferida pelo SHA-256 registrado em `data/README.md`; não modificar o conteúdo do corpus.
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
| `source_order` | `int` único entre os candidatos | Índice de origem usado no desempate; repetições invalidam a entrada |
| `texto` | `str` | Texto normalizado original, se necessário para exibição ou redundância |
| `origem` | metadados opcionais | Referência de arquivo/capítulo/seção, para rastreabilidade |
| `score_relevancia` (`v_i`) | número real finito, não negativo | Gerado para a consulta; candidatos de score zero são filtrados antes da seleção |
| `n_tokens` (`w_i`) | inteiro positivo | Custo do candidato, obtido do corpus AV1 |
| `orcamento` (`W`) | inteiro não negativo | Limite máximo de custo da seleção |

**Pré-condições:** `W >= 0`, `w_i >= 1`, valores finitos, identificadores e valores de `source_order` não repetidos. Valores `NaN`, infinitos, custos fracionários ou negativos, orçamento negativo e IDs duplicados são inválidos e deverão produzir erro explícito, em vez de um resultado silenciosamente inconsistente.

`n_tokens` é tratado como **unidade lexical aproximada** de custo de contexto, **não** como quantidade exata de tokens de um LLM. Na fragmentação da AV1, as unidades são identificadas pela expressão regular `\w+` sobre o texto normalizado. A pontuação lexical pode utilizar normalização/tokenização diferente: custo e relevância não medem exatamente a mesma representação.

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
| `source_order` repetido em candidatos distintos | Rejeitar entrada inválida |
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

**Referências internas:** `docs/ESPECIFICACAO_AV2.md`, `docs/CONTRATOS.md`, `data/README.md`, `data/queries.csv`, `data/chunks.jsonl` e `data/processed/chunks.jsonl` (origem gerada).


---

# Parte B: implementação da seleção (contratos 10 a 15)

**Responsáveis pela Parte B:** João Cosme Sena Sá, Eduardo Henrique do Lago Silva e Rafael Takeguma Goto.
**Estado em 28/10/2026:** `src/paa_context/selecao.py` e `tests/unit/test_selecao.py` implementados por João e alinhados à Parte A (PR 3, em revisão por Eduardo e Rafael), já incorporados à branch da Parte C (`av2-analise-assintotica`, PR 4). Pendentes até a entrega: os dois testes calculados à mão (contrato 14) e o `consultar.py` com `--orcamento` (contrato 15). A prova de corretude vai para as Seções 6.1 a 6.3 do relatório.

Os contratos 01 a 09 acima, da Parte A, continuam valendo integralmente. Os contratos 10 a 15 registram **como** a Parte B os cumpre: os nomes adotados no código, as decisões que a Parte A deixou para a implementação (contrato 02: "o nome das classes/funções Python é uma decisão da Parte B"; contrato 05: tratamento de empates em ponto flutuante) e os testes que conferem cada requisito. Havendo divergência entre esta parte e os contratos 01 a 09, prevalecem os contratos da Parte A, e o código deve ser corrigido.

**Pontos que dependem de acordo do grupo.** A Parte B não altera o texto dos contratos 01 a 09, mas quatro escolhas vão além do que eles fixam e precisam de aprovação explícita (contrato 09: "alinhar com o grupo"):
1. o escore convertido em inteiro × 1000 antes da seleção, o que torna a DP ótima para o valor arredondado, com a cota declarada no contrato 10;
2. a leitura de `data/chunks.jsonl` (versionado) em vez de `data/processed/chunks.jsonl` (fora do Git), que têm o mesmo conteúdo (contrato 15);
3. a exigência de posição e `source_order` distintos entre os candidatos (contrato 11, regra 2);
4. as estratégias complementares S1, S2 e S4 (contrato 12).

Se o grupo recusar algum deles, o código é ajustado.

Para evitar confusão com `docs/CONTRATOS.md`, que também numera seus contratos a partir de 01, as remissões aos contratos da AV1 trazem sempre a indicação "da AV1".

## Símbolos usados na Parte B

- **N** = número de chunks do corpus (2.737), o mesmo N da fórmula do idf.
- **n** = número de candidatos submetidos à seleção, formado pelos n primeiros do ranking C3.
- **W** = orçamento, em unidades lexicais (palavras; ver contrato 10).
- `w_i`, `v_i` = custo e valor do candidato i, como na Parte A. No código, os campos chamam-se `custo` e `valor`.
- `p_i` = posição do candidato no ranking da AV1 (0 é o primeiro), distinta do `source_order`, que é a posição do chunk no livro.

## Contrato 10: o candidato como item da mochila

O módulo converte a saída de `retrieve(consulta, chunks, estatisticas, n, algoritmo="merge")`, que corresponde à configuração C3 do contrato 01, em uma lista de `Item`. A conversão é feita por `itens_de_resultados(resultados)`, que recebe `[(Chunk, escore), ...]` e aplica as regras abaixo.

| Campo de `Item` | Campo lógico (contrato 02) | Origem e regra |
| --- | --- | --- |
| `chunk_id` | `chunk_id` | copiado do chunk; repetido gera `ValueError` (contrato 07) |
| `custo` | `n_tokens` (`w_i`) | `n_tokens` do chunk, inteiro ≥ 1; fora disso, `ValueError` |
| `valor` | `score_relevancia` (`v_i`) | `round(escore × ESCALA_VALOR)`, com `ESCALA_VALOR = 1000` e o `round` do Python, que leva os empates exatos ao par |
| `escore` | `score_relevancia` (`v_i`) | o escore original, sem arredondamento, usado em `relevancia_total` |
| `source_order` | `source_order` | copiado do chunk; usado nos desempates dos contratos 05 e 06 |
| `posicao` | (sem correspondente) | lugar do chunk no ranking C3, a partir de 0; define a ordem da saída |

Os campos `texto` e `origem` do contrato 02 não são copiados para o `Item`, porque nenhuma estratégia os usa. Quem precisar deles (exibição, medida de redundância) os obtém do corpus pelo `chunk_id`.

- **Escore:** escore zero sai da lista antes da seleção (contrato 07); escore negativo, `NaN` ou infinito gera `ValueError` (contrato 02). O custo é conferido antes, de modo que um `n_tokens` inválido gera erro mesmo com escore zero. Pela fórmula da Parte A, todo escore positivo é pelo menos 1, já que `tf`, `idf` e `qtf` valem pelo menos 1 quando o termo aparece; logo, todo `valor` é pelo menos 1.000. Se, ainda assim, um escore positivo arredondar para 0, a conversão gera `ValueError` com essa causa.
- **Custo:** o `n_tokens` da AV1 conta as palavras que a expressão `\w+` da fragmentação (`PALAVRA` em `fragmentacao.py`) encontra no texto normalizado, com acentos preservados e sem a pontuação. O texto gravado no corpus já é formado por essas palavras unidas por espaço, de modo que contar por espaços sobre o texto gravado dá o mesmo número (2.737 de 2.737 chunks). A pontuação, por sua vez, usa outro tokenizador (`preprocessing.normalize`, que remove acentos), e custo e valor não contam exatamente as mesmas unidades. No corpus, `n_tokens` vai de 1 a 256.
- **Por que o valor é inteiro (proposta da Parte B, ponto 1 da lista acima):** o contrato 05 pede que a Parte B explicite como trata empates de valores em ponto flutuante. A proposta é converter o escore em inteiro antes da seleção. Com isso, empate passa a significar igualdade exata, a comparação com a força bruta nos testes fica livre de erro de arredondamento, e o custo Θ(n·W) não muda, porque a tabela é indexada pelo custo. A tabela, por si, só exige custo inteiro; o valor inteiro é exigido pelo desempate, porque a chave do contrato 11 (regra 4) só separa valor e custo quando valores distintos diferem em pelo menos 1. Com valor real, uma diferença de 0,0001 no valor, multiplicada por W + 1, pode ficar menor que uma diferença de custo. Há, porém, um preço, que o grupo precisa aceitar: o arredondamento muda a função objetivo do contrato 03. A DP passa a ser ótima para o valor arredondado, e não para a soma dos escores reais, e diferenças de escore menores que 0,001 podem virar empate. Como cada escore muda no máximo 0,0005, a seleção S devolvida pela DP satisfaz `V_real(S) ≥ OPT_real − k·0,001`, em que k é o maior número de chunks que cabem em W. A soma dos escores originais da seleção é informada em `relevancia_total`; para que o `ΔV` do contrato 08 continue nunca negativo por construção, ele deve ser calculado sobre `valor_total`, ou então o relatório registra a cota. Uma escala maior (10^6, por exemplo) reduziria a cota na mesma proporção sem mudar o custo assintótico.
- **Efeito do arredondamento no corpus:** em 23/10, nas 270 combinações da grade preliminar do contrato 08 (n ∈ {10, 30, 50} × W ∈ {256, 512, 1024} × 30 consultas), a DP com valor arredondado escolheu exatamente os mesmos chunks que uma DP com o escore real e os desempates do contrato 05, e o guloso com valor arredondado escolheu os mesmos chunks que o guloso do contrato 06 com o escore real. A conferência não usou o gabarito (`qrels.csv`).

## Contrato 11: interface das estratégias

```python
ESCALA_VALOR = 1000

@dataclass(frozen=True)
class Item:
    chunk_id: str
    custo: int          # >= 1
    valor: int          # >= 1
    posicao: int        # 0 = primeiro do ranking C3
    source_order: int   # posicao no livro
    escore: float       # > 0, finito

def itens_de_resultados(resultados: list[tuple[Chunk, float]]) -> list[Item]

def estrategia(itens: list[Item], W: int) -> Selecao   # as cinco
ESTRATEGIAS: dict[str, Callable]                        # nome -> função; sem forca_bruta
```

A classe `Selecao` guarda `estrategia` (nome), `escolhidos` (lista de `Item`), `celulas` e `extras`, e oferece as propriedades da saída do contrato 04:

| Contrato 04 | `Selecao` |
| --- | --- |
| `chunk_ids_selecionados` | `ids` |
| `custo_total` (`W_S`) | `custo_total` |
| `relevancia_total` (`V_S`) | `relevancia_total` (soma dos escores originais) |

A propriedade `valor_total` devolve a soma dos valores inteiros, que é a grandeza otimizada pela DP. Apenas a DP preenche `celulas`, com (n + 1)·(W + 1), e `extras`, com `valor_otimo`; nas demais estratégias, `celulas = 0` e `extras = {}`. O runner e o `consultar.py` acessam as estratégias exclusivamente pelo dicionário `ESTRATEGIAS`.

Valem para todas as estratégias as seguintes regras.

1. **Respeito ao orçamento:** `custo_total <= W` sempre.
2. **Entrada inválida levanta `ValueError`** (contrato 02):
   - W, custo ou valor que não sejam `int`, inclusive `float` e `bool` (em Python, `True` é `int`, de modo que `bool` é excluído explicitamente);
   - W negativo;
   - custo ou valor menor que 1; escore que não seja número finito maior que zero;
   - posição ou `source_order` que não sejam inteiros ≥ 0, ou que se repitam;
   - `chunk_id` repetido.

   W = 0 é válido e devolve seleção vazia. A exigência de posição e `source_order` distintos não consta do contrato 02 e é proposta pela Parte B (ponto 3 da lista do início): sem ela, os desempates dependeriam da ordem da lista. No fluxo normal, ela já é garantida, pois o contrato 01 da AV1 exige `source_order` exatamente igual a {0, ..., N − 1}, e a posição é o índice no ranking.
3. **Desempate do guloso (S3), conforme o contrato 06:** razão `valor/custo` decrescente; no empate, maior `valor`; persistindo o empate, menor `source_order`. A razão é comparada como fração exata (`Fraction(valor, custo)`), nunca como `float`. As estratégias complementares S1 e S2 desempatam pela posição no ranking, e S4 herda a ordem de S3 (contrato 12).
4. **Desempate da DP (S5), conforme o contrato 05.** A DP:
   - ordena os itens por `source_order` antes de montar a tabela, de modo que o resultado não depende da ordem em que a lista chega;
   - guarda em cada célula uma chave que junta valor e custo, `chave(S) = valor(S) · (W + 1) − custo(S)`. Como o custo de qualquer seleção viável fica entre 0 e W, comparar chaves equivale a comparar primeiro o valor e, havendo empate, preferir o menor custo, que é o desempate 2 do contrato 05;
   - é construída sobre sufixos, com `E[i][w]` = maior chave possível usando apenas os itens i..n − 1 (em ordem de `source_order`) com no máximo w palavras, e `E[n][w] = 0`. A recorrência é a do contrato 05, com a chave no lugar do valor;
   - reconstrói a solução do menor `source_order` para o maior, com a regra "leva o item i quando `w_i ≤ w` e `E[i][w] = chave_i + E[i+1][w − w_i]`".

   Com isso, entre as soluções de maior valor e, entre estas, de menor custo, a DP devolve aquela cuja sequência crescente de `source_order` é lexicograficamente menor, que é o desempate 3 do contrato 05. Em termos concretos, ela leva o item de menor `source_order` se alguma dessas soluções o leva; em seguida, leva o próximo, se alguma solução compatível com a escolha anterior o leva; e assim sucessivamente. Uma sequência nunca é prefixo próprio de outra com o mesmo custo, porque todo custo é pelo menos 1. O valor ótimo sai da própria tabela, `valor_otimo = (E[0][W] + W) // (W + 1)`. Contando a ordenação, o tempo é Θ((n + 1)(W + 1)) + O(n log n), ou seja, Θ(nW + n log n) no pior caso, e a memória é Θ((n + 1)(W + 1)), já que a ordenação só acrescenta O(n). Este parágrafo é um esboço; a prova com invariante e indução vai para as Seções 6.1 a 6.3 do relatório, e a análise formal de complexidade é da Parte C (contrato 05). O contrato 05 adverte que guardar só os valores ótimos não basta para desempatar; a chave resolve isso sem uma segunda tabela.

   Dois contraexemplos ficam registrados nos testes:
   - **Contraexemplo 1**, com itens (custo, valor, `source_order`) A (6, 5, 0), B (5, 4, 1), C (5, 4, 2), D (4, 3, 3) e W = 10. {A, D} e {B, C} valem 8 e custam 10; decide a sequência de `source_order`, (0, 3) antes de (1, 2), e a DP devolve {A, D}. Com B e C no começo do livro (A 2, B 0, C 1, D 3), a mesma regra devolve {B, C}.
   - **Contraexemplo 2**, com W = 27 e itens (custo, valor) (10, 4), (10, 11), (7, 2), (3, 2), (6, 9), (8, 6), (9, 8), em que o `source_order` acompanha a posição. Os conjuntos {1, 3, 4, 5} e {1, 4, 6} valem 28, mas custam 27 e 25; pelo desempate 2, a DP devolve {1, 4, 6}, embora a ordem lexicográfica, sozinha, preferisse {1, 3, 4, 5}.
5. **Ordem da saída:** os escolhidos saem na ordem do ranking da AV1 (posição crescente), que é a ordem em que o contexto seria enviado ao LLM. O contrato 04 não fixa a ordem da saída (o item 5 menciona a ordenação por `source_order` como possibilidade da apresentação final); esta regra é uma escolha da Parte B, que não altera o conjunto nem as somas.
6. **Pureza:** nenhuma estratégia altera a lista recebida nem lê qualquer dado fora dela.

## Contrato 12: estratégias complementares

A comparação exigida pela Parte A é **S5 (DP) × S3 (guloso por relevância/custo)**, sobre os mesmos candidatos, escores, custos e orçamentos (contrato 08). O módulo implementa ainda três estratégias que não fazem parte da Parte A. Elas estão testadas e disponíveis em `ESTRATEGIAS`, mas só entram nos experimentos se o grupo aprovar a proposta da Parte D, ao fim deste documento.

| Estratégia | Nome no código | Regra | Papel |
| --- | --- | --- | --- |
| S1 | `prefixo_ranking` | desce o ranking C3 e para no primeiro chunk que não cabe | o que a AV1 faria com um orçamento; permite medir a melhora sobre a AV1 |
| S2 | `guloso_valor` | maior valor primeiro, pula quem não cabe; empate pela posição | o ranking da AV1 pulando em vez de parar |
| S3 | `guloso_densidade` | contrato 06 | **linha de base da Parte A** |
| S4 | `guloso_modificado` | o melhor entre S3 e o item de maior valor que cabe sozinho; no empate, fica S3 | guloso com garantia de pelo menos metade do ótimo (para o valor arredondado) |
| S5 | `mochila_dp` | contrato 05 | **algoritmo principal da Parte A** |

A busca exaustiva (`forca_bruta`, até 20 itens) serve apenas de juiz nos testes e não integra `ESTRATEGIAS`.

## Contrato 13: casos obrigatórios do contrato 07 e onde são testados

| Caso do contrato 07 | Comportamento implementado | Teste |
| --- | --- | --- |
| Lista de candidatos vazia | seleção vazia, custo 0 e relevância 0, nas cinco estratégias | `test_vazio_sem_candidatos` |
| Consulta sem score positivo | `itens_de_resultados` descarta escore zero e devolve lista vazia | `test_conversao_escore_zero_sai_e_posicao_fica_com_buraco` |
| `W = 0` | seleção vazia | `test_vazio_orcamento_zero` |
| Todos os itens com `w_i > W` | seleção vazia, sem erro | `test_fronteira_nenhum_item_cabe` |
| Soma dos custos `<= W` | as cinco estratégias levam todos | `test_fronteira_todos_cabem_todos_entram`, `test_fronteira_guloso_enche_o_orcamento_exatamente` |
| Um item com `w_i > W` | o item fica de fora e os demais continuam elegíveis | `test_fronteira_item_maior_que_o_orcamento_nao_bloqueia_os_demais` |
| Identificador repetido | `ValueError` na conversão e nas estratégias | `test_duplicado_mesmo_chunk_id_e_erro`, `test_validacao_chunk_id_repetido_e_erro` |
| Mesmo texto com IDs distintos | itens distintos; os dois podem entrar | `test_duplicado_texto_igual_com_ids_diferentes_passa` |
| `v_i = 0` | descartado na conversão; nas estratégias, valor < 1 é `ValueError` | `test_conversao_escore_zero_sai_e_posicao_fica_com_buraco`, `test_validacao_item_invalido_e_erro` |
| Empates de solução ótima da DP | contrato 11, regra 4 | `test_empate_dp_*`, `test_dp_segue_os_desempates_da_parte_a` |
| Empates de razão do guloso | contrato 11, regra 3 | `test_empate_guloso_densidade_*` |
| Entradas inválidas | `ValueError` | `test_validacao_*`, `test_conversao_custo_invalido_e_erro`, `test_conversao_custo_invalido_e_erro_mesmo_com_escore_zero`, `test_conversao_escore_invalido_e_erro` |
| Exemplo sintético W = 50 | S3 dá `W_S = 30`, `V_S = 160`; S5 dá `W_S = 50`, `V_S = 220` | `test_falha_gulosa_da_aula08` |
| DP contra enumeração exaustiva | valor igual ao da força bruta e desempates conferidos | `test_dp_igual_forca_bruta`, `test_dp_segue_os_desempates_da_parte_a` |

Cumpre registrar dois comportamentos que aparecem nos dados reais. O livro tem 413 chunks em 100 grupos de texto idêntico; na Q25 com n = 200, dois desses pares entram juntos em S3, S4 e S5. E, com n = 200 e W = 2^15, a tabela tem 6.586.569 células: em 23/10, numa execução com a primeira consulta, a DP levou cerca de 0,36 s, com pico de 255 MB medido pelo `tracemalloc` em execução separada (a versão de 22/10, sem o desempate por custo, levou 0,28 s e 238 MB na mesma medição; a diferença provavelmente vem dos inteiros maiores da chave, que ocupam mais bytes). Em 22/10, com o `tracemalloc` ligado, a execução levou cerca de 4 s, motivo pelo qual a memória deve ser medida fora do cronômetro.

## Contrato 14: testes

Os testes ficam em `tests/unit/test_selecao.py` e importam de `paa_context.selecao`. São 50 funções que, com as parametrizações, somam 748 execuções; a suíte inteira do repositório passa de 131 para 879. Desta lista parte a tabela de evidências do relatório (esperado, observado, evidência, status, requisito).

| Categoria do enunciado | Testes | Requisito avaliado |
| --- | --- | --- |
| normal | `test_normal_exemplo_da_aula07`, `test_normal_exemplo_rag_da_aula07` | S5 ótimo nos exemplos do professor |
| normal / adversarial | `test_falha_gulosa_da_aula08` | exemplo sintético do contrato 07; guloso sem garantia |
| vazio | `test_vazio_sem_candidatos`, `test_vazio_orcamento_zero` | contrato 07, nas cinco estratégias |
| fronteira | `test_fronteira_item_que_cabe_exatamente`, `test_fronteira_guloso_enche_o_orcamento_exatamente`, `test_fronteira_todos_cabem_todos_entram`, `test_fronteira_nenhum_item_cabe`, `test_fronteira_item_maior_que_o_orcamento_nao_bloqueia_os_demais` | respeito ao orçamento; contrato 07 |
| entrada inválida | `test_validacao_orcamento_invalido_e_erro`, `test_validacao_item_invalido_e_erro` (o item ruim no começo, no meio e no fim), `test_validacao_escore_invalido_e_erro`, `test_validacao_posicao_invalida_e_erro`, `test_validacao_source_order_invalido_e_erro`, `test_validacao_posicao_repetida_e_erro`, `test_validacao_source_order_repetido_e_erro`, `test_validacao_chunk_id_repetido_e_erro` | contratos 02 e 11 (regra 2) |
| empate | `test_empate_dp_itens_identicos_ficam_os_de_menor_source_order`, `test_empate_dp_mesmo_valor_e_custo_decide_o_source_order` (contraexemplo 1), `test_empate_dp_mesmo_valor_fica_o_menor_custo` (contraexemplo 2), `test_empate_dp_nao_depende_da_ordem_da_lista`, `test_empate_dp_usa_source_order_e_nao_a_posicao`, `test_empate_guloso_densidade_desempata_pelo_source_order`, `test_empate_guloso_densidade_maior_valor_antes_do_source_order`, `test_empate_guloso_valor_desempata_pelo_ranking`, `test_densidade_comparada_como_fracao_exata`, `test_empate_guloso_modificado_fica_com_o_guloso`, `test_empate_guloso_modificado_entre_itens_isolados` | contratos 05 e 06; contrato 11, regras 3 e 4 |
| entrada grande | `test_grande_dp_respeita_orcamento_e_bate_guloso` (300 itens, W = 2048) | S5 ≥ S1 a S4 no valor |
| duplicado e conversão | `test_duplicado_mesmo_chunk_id_e_erro`, `test_duplicado_texto_igual_com_ids_diferentes_passa`, `test_conversao_custo_invalido_e_erro`, `test_conversao_custo_invalido_e_erro_mesmo_com_escore_zero`, `test_conversao_escore_invalido_e_erro`, `test_conversao_escore_que_arredonda_para_zero_e_erro`, `test_conversao_valor_posicao_e_source_order` (arredondar, e não truncar), `test_conversao_escore_zero_sai_e_posicao_fica_com_buraco`, `test_relevancia_total_soma_os_escores_originais` | contratos 02, 04, 07 e 10 |
| propriedade | `test_dp_igual_forca_bruta` (200 instâncias), `test_dp_segue_os_desempates_da_parte_a` (200, com ordem do livro sorteada à parte e lista embaralhada; 63 instâncias têm mais de uma solução de valor ótimo, 44 delas com custos diferentes e 26 em que decide o `source_order`), `test_guloso_modificado_garante_metade_do_otimo` (200), `test_estrategias_respeitam_orcamento_ordem_e_nao_alteram_a_entrada` (50) | corretude de S5; contrato 04 (pós-condições); contrato 11, regras 1, 4, 5 e 6; garantia de S4 |
| adversarial | `test_adversarial_guloso_densidade_pode_ser_muito_pior`, `test_adversarial_prefixo_trava_no_primeiro_grande`, `test_guloso_modificado_conserta_o_contraexemplo` | sem garantia em S3 e S1 |
| revela falha | `test_otimo_no_valor_nao_e_otimo_em_relevancia`, `test_duplicado_texto_igual_com_ids_diferentes_passa` | a DP maximiza a soma de tf-idf, não a relevância nem a diversidade (contrato 03 e Parte E) |
| estrutura | `test_estrategias_e_campos_da_selecao`, `test_forca_bruta_so_ate_20_itens`, `test_item_nao_pode_ser_alterado` | contrato 11 (interface) |

**Mutações.** Para conferir se os testes detectam erros, cada mudança abaixo foi aplicada isoladamente numa cópia temporária do código, contando-se quantas das 748 execuções falham. Todas as 21 foram detectadas. A tabela é reproduzida por `python scripts/mutacoes_selecao.py` (todas) ou `python scripts/mutacoes_selecao.py 15` (só a 15); o script trabalha numa cópia temporária de `src/`, `tests/` e `pyproject.toml` e não altera o repositório.

| # | Mudança | Falhas |
| --- | --- | --- |
| 1 | mochila ilimitada (lê a linha atual em vez da seguinte) | 320 |
| 2 | `custo <= w` → `custo < w` na tabela | 131 |
| 3 | `<= W` → `< W` nos gulosos | 5 |
| 4 | reconstrução "deixa de fora quando empata" | 30 |
| 5 | a DP sem ordenar a lista | 16 |
| 6 | aceitar `bool` como inteiro | 10 |
| 7 | aceitar valor 0 | 3 |
| 8 | S2 sem a posição no desempate | 1 |
| 9 | razão de S3 em `float` | 1 |
| 10 | truncar em vez de arredondar o escore | 2 |
| 11 | S4 sem o item isolado | 3 |
| 12 | validar só o primeiro item | 37 |
| 13 | a DP do laboratório de estudo (prefixos, só valor) | 44 |
| 14 | a DP de 22/10 (regra "leva" por posição, só valor) | 40 |
| 15 | a DP sem o desempate por custo | 318 |
| 16 | a DP desempatando pela posição, e não pelo `source_order` | 16 |
| 17 | S3 sem o maior valor no desempate | 1 |
| 18 | S3 desempatando pela posição, e não pelo `source_order` | 1 |
| 19 | conversão descartando `chunk_id` repetido em silêncio | 1 |
| 20 | conversão deixando passar escore zero | 1 |
| 21 | valor ótimo lido da chave sem compensar o custo | 173 |

As mutações pegas por um único teste (8, 9, 17 a 20) tratam de detalhes que, no corpus, quase nunca mudam o resultado.

Pendente em 28/10: dois testes independentes, com valores calculados à mão numa tabela pequena (aula 03, slide 16), que entram em arquivo separado.

## Contrato 15: integração, nomes e versão

- **`consultar.py` (a implementar; responsável a combinar, a proposta inicial é o Rafael):** deve receber `--orcamento W`, `--estrategia` (`choices` = chaves de `ESTRATEGIAS`, padrão `mochila_dp`) e `--candidatos n` (padrão 50). O `--k` não serve para isso, porque vale 5 por padrão. Com `--orcamento`, o ranking usado é sempre o C3, qualquer que seja o `--config`. Sem `--orcamento`, o comportamento da AV1 permanece intacto. A saída mostra os escolhidos na ordem do ranking, com `custo_total`, `relevancia_total`, `valor_otimo` e `celulas`.
- **Corpus lido (ponto 2 da lista do início):** `data/chunks.jsonl`, o arquivo versionado, idêntico byte a byte ao `data/processed/chunks.jsonl` citado no contrato 01 (o SHA-256 consta de `data/README.md`). A troca se explica porque `data/processed/` está no `.gitignore`: quem clona o repositório só tem o arquivo versionado. Nenhum dos dois é sobrescrito.
- **Nomes:** o código novo da AV2 é escrito em português, sem acentos. Nada da AV1 é renomeado.
- **Versão:** a tag `v2.0.0` marca o commit da entrega, e a `v1.0.0` permanece intacta, assim como `experimentos/brutos/execucoes.jsonl`, `docs/RESULTADOS.md` e o relatório da AV1.
- **Revisão:** toda PR da AV2 passa por outro integrante antes do merge (`PLANEJAMENTO_AV2.md`, seção 7, item 3).

---

# Proposta da Parte D (João), pendente de acordo do grupo

Esta seção **não altera** o contrato 08. Ela registra uma proposta de João, que integra a Parte D com Eduardo e Helena, para ser discutida antes de qualquer medição definitiva. Enquanto o grupo não a aprovar, vale o contrato 08.

**Motivação.** A seção 9.1 do enunciado lista, entre as métricas mínimas, a "qualidade de recuperação: Precision@k ou avaliação manual simples com relevâncias justificadas" e o "tempo de pré-processamento e construção de estrutura/índice", que o contrato 08 não traz. A seção 1 pede ainda que se demonstre como o algoritmo "melhora uma propriedade mensurável do sistema de recuperação de contexto". Como o próprio contrato 08 registra, `ΔV` nunca é negativa quando a DP está correta; a magnitude dela, a frequência das divergências e o custo de tempo e memória continuam informativos, mas não dizem se a seleção melhora a qualidade do contexto. A proposta acrescenta, por isso, uma medida de qualidade baseada no gabarito da AV1 (`data/qrels.csv`, os pares consulta-chunk com relevância justificada que a seção 9.1 aceita), o tempo de pré-processamento e hipóteses fixadas antes da execução. O teste exigido pela seção 11 ("pelo menos um teste que possa refutar a hipótese da equipe ou revelar uma falha da estratégia") já está coberto na Parte B pelos testes marcados como "revela falha" no contrato 14.

A Parte D é de João, Eduardo e Helena; esta proposta ainda não passou pelos outros dois. Convém também avaliar a viabilidade até 04/11, sobretudo da amostra cega e da série de escala, que podem ser cortadas sem prejuízo das hipóteses.

## D1. Desenho

1. **Cenários exploratórios:** S1 a S5 × n ∈ {50, 200} × W ∈ {256, 512, 2048} × 30 consultas. Uma sondagem de 18/10, feita com o laboratório de estudo, já rodou esses cenários; como a qualidade é determinística, os números dela (D4) são resultados exploratórios, e não previsões.
2. **Cenários confirmatórios:** n ∈ {50, 100, 200} × W ∈ {1024, 4096}, nos quais se pede que ninguém calcule qualidade (gabarito) antes de esta proposta ser decidida. Neles se testam as hipóteses de D4. O alcance é limitado, e o relatório deve dizê-lo: são as mesmas 30 consultas e o mesmo gabarito da sondagem, W = 1024 fica entre valores já explorados (512 e 2048), e as margens das hipóteses foram fixadas depois da sondagem. Até 23/10, só se mediram nesses cenários tempo, memória, soma de custos e, na conferência do contrato 10, quais chunks cada seleção escolhe com n = 50 e W = 1024, sem o gabarito.
3. **Relação com a grade do contrato 08** (n ∈ {10, 30, 50} × W ∈ {256, 512, 1024}): a grade pode ser mantida como está para `V_S`, `W_S`, `ΔV`, tempo e memória. O cenário n = 50, W = 1024 aparece nas duas grades; a qualidade pelo gabarito, nele, só deve ser calculada depois do commit desta proposta.
4. **Repetições:** 5 medidas por cenário, precedidas de 2 de aquecimento, como na AV1. A qualidade não varia entre repetições; as repetições servem para o tempo.
5. **Ordem:** um único `random.Random(2026)` sorteia, a cada repetição de cada consulta, a ordem das estratégias e a dos W.
6. **Memória:** medida com `tracemalloc` em execução separada, fora do cronômetro.
7. **Série de escala da DP:** n = 200 e W ∈ {2^9, ..., 2^15}, só tempo e memória, com S3 no mesmo gráfico, para mostrar Θ(n·W) contra O(n log n). Cada bit a mais em W dobra o tamanho da tabela: o tempo é polinomial no valor numérico de W, mas exponencial no número de bits usados para escrevê-lo, que é o sentido de pseudo-polinomial. Nas consultas medidas, em W = 2^15 todos os candidatos cabem (a maior soma de custos com n = 200 é 24.800), e a DP paga n·W mesmo assim.
8. **Ambiente:** `experimentos/logs/ambiente_av2.json`, com sistema, versões, commit, SHA-256 do corpus, semente, parâmetros fixos (`chunk_size` 256, `overlap` 32, `n_chunks` 2.737, C3, `ESCALA_VALOR` 1000) e o tempo de pré-processamento (carregar os chunks e calcular as estatísticas), medido 5 vezes após 2 aquecimentos, como pede a seção 9.1.

## D2. Log

Arquivo novo `experimentos/brutos/selecao.jsonl`, sem tocar no `execucoes.jsonl` da AV1, uma linha por medida:

```
run_id, timestamp, commit, host, python_versao, semente,
experimento, medida, estrategia, query_id, categoria, n, W, repeticao,
n_itens, n_escolhidos, ids_escolhidos, custos_escolhidos,
custo_total, valor_total, relevancia_total, valor_otimo, respeita_orcamento, uso_orcamento, celulas,
tempo_recuperacao_ns, tempo_itens_ns, tempo_selecao_ns, tempo_fluxo_consulta_ns,
memoria_pico_selecao_bytes
```

`experimento` ∈ {`principal`, `confirmatorio`, `escala`}; `medida` ∈ {`tempo`, `memoria`}. `uso_orcamento` fica `null` quando W = 0 (contrato 08). Os tempos usam `time.perf_counter_ns`, e nunca se gravam apenas médias. Um arquivo complementar, `experimentos/brutos/candidatos.jsonl`, guarda por consulta e n os `ids`, `custos`, `valores`, `posicoes` e `source_order` dos candidatos, o que permite refazer qualquer seleção sem rodar `retrieve` de novo.

## D3. Métricas de qualidade

O gabarito é o `data/qrels.csv` da AV1: 146 pares consulta-chunk, de relevância 1, escolhidos pela Helena antes de qualquer ranking e justificados par a par. R(q) designa os relevantes da consulta q, e E, os escolhidos.

| Métrica | Definição |
| --- | --- |
| fração de tokens relevantes (**principal**) | soma, nas 30 consultas, do custo dos escolhidos que estão em R(q), dividida pela soma dos `custo_total` |
| relevantes escolhidos | \|E ∩ R(q)\|, por consulta e somado |
| precisão do conjunto escolhido | \|E ∩ R(q)\| ÷ \|E\| (não é a Precision@k da AV1, porque cada estratégia escolhe um k diferente) |
| cobertura | \|E ∩ R(q)\| ÷ \|R(q)\| |
| cobertura máxima alcançável | \|top-n ∩ R(q)\| ÷ \|R(q)\| (44 de 146 com n = 50; 86 com n = 200) |
| razão de valor | `valor_total ÷ valor_otimo` (vale 1 na DP por construção) |
| uso do orçamento | `custo_total ÷ W` |
| redundância | pares de escolhidos com similaridade de Jaccard entre os conjuntos de palavras ≥ 0,8 |

A fração nunca decide sozinha, porque premia seleções pequenas, e vai sempre acompanhada de relevantes e cobertura. Uma amostra cega de 100 pares escolhidos que não estão no gabarito, julgada sem saber a estratégia, estima quantos relevantes faltam no `qrels.csv`; é análise descritiva, não teste de hipótese.

## D4. O que já se sabe e o que seria testado

**Sondagem de 18/10** (exploratória, 30 consultas):

| n | W | relevantes S1 / S3 / S5 | fração S3 / S5 | consultas em que S5 e S3 diferem em relevantes |
| --- | --- | --- | --- | --- |
| 50 | 256 | 5 / 30 / 30 | 0,255 / 0,232 | 2 |
| 50 | 512 | 7 / 35 / 36 | 0,150 / 0,146 | 1 |
| 50 | 2048 | 24 / 44 / 43 | 0,056 / 0,050 | 1 |
| 200 | 256 | 5 / 34 / 38 | 0,172 / 0,200 | 6 |
| 200 | 512 | 7 / 53 / 54 | 0,153 / 0,156 | 3 |
| 200 | 2048 | 24 / 75 / 75 | 0,063 / 0,062 | 0 |

Em 23/10, a implementação alinhada à Parte A escolheu, nesses 6 cenários, exatamente os mesmos chunks que o laboratório em todas as 900 seleções (30 consultas × 5 estratégias × 6 cenários), de modo que a tabela continua valendo. O laboratório e o script dessa comparação estão fora do repositório; se a proposta for aceita, a tabela deve ser refeita pelo runner oficial.

**Hipóteses propostas** (só nos cenários confirmatórios):

- **H1 (melhora sobre a AV1):** S5 escolhe mais relevantes que S1 e tem fração de tokens relevantes maior que a de S1. A parte dos relevantes funciona como controle; a parte da fração pode falhar, porque a vantagem encolhe à medida que W cresce.
- **H2a (concordância):** S5 e S3 escolhem o mesmo número de relevantes em pelo menos 24 das 30 consultas.
- **H2b (direção):** o saldo (consultas em que S5 escolhe mais relevantes que S3, menos o contrário) é no máximo 3.
- As margens foram escolhidas depois da sondagem, e o relatório declararia isso. Basta um cenário confirmatório em que uma desigualdade falhe para refutar a hipótese, e o resultado entraria no relatório tal como saísse.

---

## Histórico da Parte B

- **18 a 22/10:** João manteve, fora do repositório, um laboratório de estudo e um rascunho de contrato (versões 1 a 4). A versão 4 usava a regra "leva" pela posição no ranking, sem desempate por custo.
- **23/10:** com a Parte A publicada, a implementação foi alinhada aos contratos 01 a 09: desempate da DP por menor custo e depois por `source_order` (contrato 05), desempate do guloso por maior valor e depois por `source_order` (contrato 06), `chunk_id` repetido, escore inválido e custo menor que 1 rejeitados na conversão, escore zero descartado (contratos 02 e 07) e `relevancia_total` na saída (contrato 04). O rascunho foi incorporado a este arquivo como Parte B, e as partes experimentais passaram a figurar como proposta da Parte D.

---

## Questões para deliberação do grupo (não alteram os contratos 01–09)

1. **Representação dos escores na Parte B.** Foi proposta a quantização `round(1000 * v_i)` para tratar empates. A programação dinâmica assim implementada seria ótima em relação aos **valores quantizados**, não necessariamente aos escores TF-IDF reais previstos no Contrato 03. Os testes relatados em 270 cenários não substituem a garantia geral. **Pendente:** decidir entre manter os escores originais com política numérica documentada ou formalizar a quantização, seu erro e a nova função objetivo. A DP indexada por capacidade exige custos inteiros, não valores inteiros.
2. **Estratégias adicionais.** Corte do ranking da AV1, guloso por valor e guloso modificado podem integrar análises complementares. A comparação principal permanece DP versus guloso por relevância/custo. Suas regras precisam ser documentadas antes da coleta definitiva.
3. **Qualidade independente do TF-IDF (Parte D).** Proposta de avaliar a seleção com `data/qrels.csv`, além de `V_S`, `ΔV`, custo, tempo e memória. É necessário definir cobertura dos julgamentos, tratamento de chunks não julgados e métrica antes de consultar os resultados confirmatórios. Não interpretar automaticamente "sem julgamento" como "irrelevante". Registrar tempo de preparação/recuperação separadamente do tempo de seleção.
4. **Separação experimental.** Foi proposto reservar `n = 50, W = 1024` até o fechamento do protocolo de qualidade. Não relatar esse cenário como validação confirmatória após usá-lo para calibrar hipóteses.
