# DESENHO — Desafio 09: Atualização gradual

> **Preencha este arquivo ANTES de escrever qualquer YAML.** Ninguém corrige as suas respostas (o `lab verify` só avisa se ele continuar em branco):
> serve para você pensar. Pode rascunhar no papel e resumir aqui. Respostas curtas e objetivas bastam.
> O método completo, com um exemplo resolvido, está em `docs/metodo.md`.

## 1. Estado desejado

> O que precisa ser verdade ao final? Como você vai provar que está verdade?
> - O que precisa ser verdade para quem usa o portal durante toda a atualização? E ao final, em cada servidor e no balanceador?

**Sua resposta:**

<!-- escreva abaixo desta linha -->

## 2. Inventário

> Quem são os alvos e como estão agrupados?
> - Em quais hosts a atualização roda? Onde roda a ação de tirar e devolver um servidor do balanceador, e em qual host ela precisa ser executada de fato?

**Sua resposta:**

<!-- escreva abaixo desta linha -->

## 3. Variáveis

> O que muda entre hosts ou ambientes? Em qual camada cada valor mora?
> - O que muda de um nó para o outro (nome do servidor no balanceador, URL de saúde)? De onde vêm esses valores (fatos do inventário, variáveis do play)?

**Sua resposta:**

<!-- escreva abaixo desta linha -->

## 4. Estrutura

> Quais plays, tasks ou roles, e em que ordem?
> - Qual a sequência para um nó? Quantos nós de cada vez? O que acontece com os outros nós enquanto um é atualizado? E se um nó falhar no meio?

**Sua resposta:**

<!-- escreva abaixo desta linha -->

## 5. Risco

> O que pode falhar? Como validar antes de aplicar? Como voltar atrás?
> - Quanto tempo cada nó fica fora do ar? O que o balanceador faz com requisições em andamento quando você tira o servidor? O que acontece se a nova versão estiver com defeito: quem percebe e quando?

**Sua resposta:**

<!-- escreva abaixo desta linha -->
