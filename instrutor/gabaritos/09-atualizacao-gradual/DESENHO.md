# DESENHO — Desafio 09: Atualização gradual

> **Preencha este arquivo ANTES de escrever qualquer YAML.** Ninguém corrige as suas respostas (o `lab verify` só avisa se ele continuar em branco):
> serve para você pensar. Pode rascunhar no papel e resumir aqui. Respostas curtas e objetivas bastam.
> O método completo, com um exemplo resolvido, está em `docs/metodo.md`.

## 1. Estado desejado

> O que precisa ser verdade ao final? Como você vai provar que está verdade?
> - O que precisa ser verdade para quem usa o portal durante toda a atualização? E ao final, em cada servidor e no balanceador?

**Sua resposta:**

Durante toda a execução, o balanceador responde 200 a todas as requisições. Ao final: web1 e web2 na versão 2 e os dois servidores de novo em rotação (UP) no HAProxy.

## 2. Inventário

> Quem são os alvos e como estão agrupados?
> - Em quais hosts a atualização roda? Onde roda a ação de tirar e devolver um servidor do balanceador, e em qual host ela precisa ser executada de fato?

**Sua resposta:**

O play roda em `web` (web1 e web2). A ação do balanceador é executada em `lb1` (`delegate_to`), porque é lá que está o socket do HAProxy, mas sobre o servidor do nó em curso (`inventory_hostname`).

## 3. Variáveis

> O que muda entre hosts ou ambientes? Em qual camada cada valor mora?
> - O que muda de um nó para o outro (nome do servidor no balanceador, URL de saúde)? De onde vêm esses valores (fatos do inventário, variáveis do play)?

**Sua resposta:**

O nome do servidor no balanceador é o próprio `inventory_hostname` (web1, web2). A URL de saúde também usa `inventory_hostname`. Valores fixos do ambiente (backend `web`, caminho do socket, host do balanceador) ficam em `vars:` do play para não repetir.

## 4. Estrutura

> Quais plays, tasks ou roles, e em que ordem?
> - Qual a sequência para um nó? Quantos nós de cada vez? O que acontece com os outros nós enquanto um é atualizado? E se um nó falhar no meio?

**Sua resposta:**

Para cada nó: (1) tirar do balanceador esperando ele sair da rotação (`wait`), (2) atualizar com a role, (3) validar `/saude` com tentativas, (4) devolver e esperar ele voltar a UP. `serial: 1`, para que o outro nó siga atendendo. `max_fail_percentage: 0`: se um nó falhar, o play para e o outro não é tocado.

## 5. Risco

> O que pode falhar? Como validar antes de aplicar? Como voltar atrás?
> - Quanto tempo cada nó fica fora do ar? O que o balanceador faz com requisições em andamento quando você tira o servidor? O que acontece se a nova versão estiver com defeito: quem percebe e quando?

**Sua resposta:**

Cada nó fica fora ~8 s (pausa da role). Ao desabilitar, o HAProxy para de mandar requisições novas e deixa as em andamento terminarem. Com release com defeito, `/saude` devolve 503 e a task de validação falha depois das tentativas: o nó nunca é devolvido e o play para, deixando o outro nó na versão antiga em rotação.
