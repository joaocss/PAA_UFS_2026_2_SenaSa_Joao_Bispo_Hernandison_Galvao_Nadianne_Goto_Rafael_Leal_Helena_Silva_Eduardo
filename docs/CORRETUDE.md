# Justificativa de corretude

## O que se deseja provar

Dada uma lista finita de registros válidos e uma ordem total definida por pontuação decrescente e, em caso de empate, identificador de origem crescente, o Merge Sort implementado pela equipe termina e devolve uma permutação da entrada ordenada por essa relação. Como consequência, os primeiros min(k, n) elementos do resultado são exatamente os k mais relevantes.

## Hipóteses

Para que a justificativa de corretude seja válida, consideram-se as seguintes condições:

1. A entrada do algoritmo é uma lista finita de candidatos.
2. Cada candidato possui um `score` numérico válido, definido e comparável.
3. Cada candidato possui um valor de `source_order` válido, utilizado como critério de desempate quando dois candidatos apresentam o mesmo `score`.
4. A regra de ordenação considera primeiro o maior `score` e, em caso de empate, o menor `source_order`.
5. A relação de comparação utilizada é consistente e transitiva. Isso significa que, se um elemento deve aparecer antes de um segundo elemento, e esse segundo deve aparecer antes de um terceiro, então o primeiro também deve aparecer antes do terceiro.
6. O procedimento de merge recebe duas listas previamente ordenadas segundo essa mesma regra.

Essas hipóteses garantem que os elementos possam ser comparados de forma consistente durante a execução do algoritmo e que exista uma ordem bem definida para o resultado final.

## Prova por indução

Para demonstrar a corretude do Merge Sort implementado no projeto, utiliza-se uma prova por indução sobre o tamanho da lista de candidatos. Esse tipo de raciocínio é compatível com a estrutura recursiva do algoritmo: o problema é dividido em subproblemas menores até atingir casos triviais e, em seguida, os resultados são combinados. Essa organização segue o paradigma de divisão e conquista apresentado por Cormen et al. (2001, Seção 2.3).

Seja `P(n)` a seguinte proposição:

> Para toda lista válida de tamanho `n`, o algoritmo `merge_sort` termina e retorna uma permutação da entrada ordenada segundo a regra definida por `sort_key`.

A função `sort_key` utiliza como critério `(-score, source_order)`, isto é, maior `score` primeiro e, em caso de empate, menor `source_order`. :contentReference[oaicite:0]{index=0}

### Caso base

Para listas de tamanho `n <= 1`, não é necessário realizar nenhuma divisão adicional. Uma lista vazia ou contendo apenas um elemento já está ordenada por definição.

Na implementação da equipe, quando o tamanho da entrada é menor ou igual a um, a função retorna diretamente uma cópia da própria lista. :contentReference[oaicite:1]{index=1}

Portanto, para `n = 0` e `n = 1`, o algoritmo:

- termina;
- preserva os elementos da entrada;
- retorna uma lista já ordenada.

Assim, a proposição `P(n)` é verdadeira nos casos base.

### Hipótese de indução

Assume-se que a proposição seja verdadeira para todas as listas de tamanho menor que `n`.

Em outras palavras, considera-se que, para qualquer lista válida de tamanho `j < n`, o algoritmo `merge_sort`:

- termina;
- preserva todos os elementos da entrada;
- retorna esses elementos ordenados segundo `sort_key`.

Essa hipótese permite analisar o comportamento do algoritmo para uma lista de tamanho `n`.

### Passo indutivo

Considere agora uma lista válida de tamanho `n > 1`.

O algoritmo divide essa lista em duas partes menores, `left` e `right`. Como ambas possuem tamanho inferior a `n`, aplica-se a hipótese de indução: as chamadas recursivas `merge_sort(left)` e `merge_sort(right)` terminam e produzem duas listas corretamente ordenadas.

Na implementação da equipe, essas duas chamadas recursivas são executadas antes da etapa de combinação. :contentReference[oaicite:2]{index=2}

Em seguida, o procedimento `_merge` combina as duas listas já ordenadas. A cada comparação, é selecionado o elemento que deve aparecer primeiro segundo `sort_key`, mantendo a ordem definida pelo projeto. :contentReference[oaicite:3]{index=3}

Como todos os elementos das duas metades são copiados para a lista resultante, sem alteração do conjunto de elementos da entrada, o resultado final é uma permutação da lista original. Os elementos restantes de uma das metades, após o término do laço principal, também são adicionados ao resultado. :contentReference[oaicite:4]{index=4}

Portanto, se o algoritmo funciona corretamente para os dois subproblemas menores, então também funciona corretamente para a lista de tamanho `n`.

Assim, `P(n)` é verdadeira.

Conclui-se, por indução, que o Merge Sort implementado pela equipe termina e retorna uma permutação da entrada ordenada segundo a relação definida por `sort_key`, para toda lista finita que satisfaça as hipóteses estabelecidas.

## Invariante do merge

Para demonstrar que o procedimento `_merge` mantém a ordenação correta durante a combinação de duas listas já ordenadas, considera-se o seguinte invariante de laço:

> Antes de cada iteração do laço principal, a lista `merged` contém exatamente os elementos já consumidos de `left` e `right`, na ordem correta segundo `sort_key`.

Além disso, todos os elementos já inseridos em `merged` aparecem antes dos elementos ainda não consumidos, de acordo com a mesma relação de ordenação.

Na implementação da equipe, `_merge` compara os elementos atuais das duas listas e acrescenta ao resultado aquele que deve aparecer primeiro segundo `sort_key`. :contentReference[oaicite:0]{index=0}

### Inicialização

Antes da primeira iteração:

- `merged` está vazia;
- nenhum elemento de `left` foi consumido;
- nenhum elemento de `right` foi consumido.

Logo, o invariante é verdadeiro nesse momento, pois a lista `merged` contém exatamente os elementos já processados — nesse caso, nenhum — e está trivialmente ordenada.

A demonstração por inicialização, manutenção e término segue a estrutura de prova por invariante de laço apresentada por Cormen et al. (2001, Seção 2.1).

### Manutenção

Suponha que o invariante seja verdadeiro no início de uma determinada iteração.

Como `left` e `right` já estão ordenadas, seus primeiros elementos ainda não consumidos são os próximos candidatos possíveis segundo a relação de ordenação utilizada no projeto.

O algoritmo compara esses dois elementos por meio de `sort_key` e acrescenta a `merged` aquele que deve aparecer primeiro. Em seguida, o índice correspondente é incrementado. :contentReference[oaicite:1]{index=1}

Dessa forma:

- nenhum elemento já inserido precisa ser reposicionado;
- `merged` continua ordenada;
- `merged` continua contendo exatamente os elementos já consumidos de `left` e `right`.

Portanto, o invariante é preservado após cada iteração.

### Término

O laço principal termina quando todos os elementos de uma das duas listas foram consumidos.

Nesse momento, os elementos restantes pertencem apenas à outra lista. Como essa lista já está ordenada, seus elementos podem ser acrescentados ao final de `merged` sem violar a ordem estabelecida. A implementação realiza essa etapa por meio dos laços que copiam os elementos restantes de `left` ou `right`. :contentReference[oaicite:2]{index=2}

Ao término do procedimento:

- todos os elementos de `left` e `right` estão presentes em `merged`;
- nenhum elemento é perdido;
- nenhum elemento é duplicado;
- a lista resultante permanece ordenada segundo `sort_key`.

Assim, o invariante permite justificar que o procedimento `_merge` combina corretamente duas listas previamente ordenadas, produzindo uma única lista também ordenada.

## Término

A prova de término considera separadamente a recursão do `merge_sort` e os laços do procedimento `_merge`.

### Término das chamadas recursivas

Para uma lista com mais de um elemento, o `merge_sort` divide a entrada em duas partes menores.

Essas partes possuem tamanho estritamente menor que o tamanho da lista original. O processo de divisão continua até que sejam alcançadas listas de tamanho zero ou um, que correspondem ao caso base do algoritmo. Na implementação da equipe, quando `len(items) <= 1`, a função retorna diretamente uma cópia da lista. :contentReference[oaicite:0]{index=0}

Como o tamanho do problema diminui a cada chamada recursiva, não é possível ocorrer uma sequência infinita de divisões. Assim, as chamadas recursivas terminam.

Esse comportamento é compatível com a estratégia de divisão e conquista descrita por Cormen et al. (2001, Seção 2.3), na qual o problema é dividido em subproblemas menores até atingir casos simples.

### Término do procedimento `_merge`

No procedimento `_merge`, dois índices são utilizados para percorrer as listas `left` e `right`.

A cada iteração do laço principal, pelo menos um desses índices é incrementado, indicando que um elemento foi consumido de uma das listas. :contentReference[oaicite:1]{index=1}

Como `left` e `right` são listas finitas, os índices não podem ser incrementados indefinidamente. O laço principal termina quando uma das listas é completamente consumida.

Em seguida, os elementos restantes da outra lista são copiados para o resultado por meio de laços que também avançam seus respectivos índices a cada iteração. :contentReference[oaicite:2]{index=2}

Portanto, todos os laços executados por `_merge` também terminam.

Dessa forma, como tanto as chamadas recursivas quanto os laços de combinação possuem progresso finito e alcançam uma condição de parada, conclui-se que o Merge Sort implementado pela equipe termina para toda entrada finita que satisfaça as hipóteses estabelecidas.

## Limites do argumento

A prova apresentada garante propriedades relacionadas ao funcionamento do algoritmo de ordenação, mas não garante que todo o processo de recuperação de informação esteja semanticamente correto.

Em particular, a prova garante que:

- o `merge_sort` termina para toda entrada finita que satisfaça as hipóteses estabelecidas;
- os elementos da entrada são preservados durante a ordenação;
- nenhum candidato é perdido ou duplicado pelo procedimento de ordenação;
- a saída é ordenada segundo a regra definida por `sort_key`;
- o critério de desempate por `source_order` é respeitado.

A regra usada pelo projeto prioriza maior `score` e, em caso de empate, menor `source_order`. Essa relação é implementada diretamente pela função `sort_key`. :contentReference[oaicite:0]{index=0}

Entretanto, essa demonstração não garante que o valor de `score` represente perfeitamente a intenção do usuário. Um candidato pode estar corretamente ordenado segundo a função de relevância utilizada e, ainda assim, não ser o trecho semanticamente mais adequado para responder à consulta.

Também não se pode concluir, apenas pela corretude da ordenação, que:

- todos os chunks recuperados sejam semanticamente relevantes;
- o corpus contenha todas as informações necessárias para responder à consulta;
- a função de relevância escolhida seja a melhor possível;
- o primeiro resultado ordenado seja necessariamente o melhor do ponto de vista humano;
- uma etapa posterior de geração de resposta produza conteúdo correto.

Assim, a prova demonstra a corretude do processo de ordenação em relação à regra definida pelo sistema, mas não a corretude semântica de todo o processo de recuperação.

Em outras palavras, o algoritmo pode ordenar corretamente os candidatos segundo o `score` calculado, mesmo que esse `score` não represente de forma perfeita o que o usuário pretendia encontrar.

## Casos em que a prova não se aplica

A prova não se aplica, por exemplo, nos seguintes casos:

- quando algum candidato possui `score` indefinido, inválido ou não comparável;
- quando o campo `source_order` está ausente ou não pode ser comparado;
- quando a relação de comparação deixa de ser consistente ou transitiva;
- quando o procedimento `_merge` recebe listas que não estão previamente ordenadas segundo `sort_key`;
- quando as chamadas recursivas deixam de produzir subproblemas menores;
- quando a implementação utiliza um critério de comparação diferente daquele definido em `sort_key`;
- quando a estrutura dos elementos de entrada não corresponde ao formato esperado pelo algoritmo.

Na implementação atual, a ordenação depende da chave `(-score, source_order)`. Portanto, qualquer alteração nessa regra exige uma nova análise de corretude, pois a relação de ordem considerada na prova também mudaria. :contentReference[oaicite:0]{index=0}

Da mesma forma, a prova do Merge Sort pressupõe que cada metade seja ordenada antes da chamada ao procedimento `_merge`. Essa condição é satisfeita pela implementação atual por meio das chamadas recursivas realizadas antes da combinação das duas partes. :contentReference[oaicite:1]{index=1}

Assim, a demonstração é válida para a implementação e para as condições analisadas neste trabalho, não podendo ser generalizada automaticamente para versões modificadas do algoritmo.


## Testes que ancoram o argumento

A prova formal de corretude apresentada neste trabalho é baseada em indução, invariante de laço e argumento de término. Os testes automatizados não substituem essa demonstração, mas funcionam como evidência prática de que a implementação respeita as propriedades assumidas na prova.

### Teste específico da relação de ordenação

Como parte desta análise, foi criado o arquivo:

```text
tests/unit/test_sort_key.py
```

Esse arquivo testa diretamente a regra de ordenação definida em:

```text
src/paa_context/sort_key.py
```

A função `sort_key` utiliza a chave:

```python
(-score, source_order)
```

Essa regra estabelece que:

- candidatos com maior `score` devem aparecer primeiro;
- em caso de empate de `score`, o menor `source_order` deve aparecer primeiro.

Essa relação é a mesma utilizada ao longo da prova formal para definir quando um candidato deve aparecer antes de outro.

Foram implementados três testes específicos:

