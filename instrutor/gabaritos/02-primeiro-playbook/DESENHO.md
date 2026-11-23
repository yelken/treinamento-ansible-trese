# DESENHO — Desafio 02: Primeiro playbook idempotente

> **Preencha este arquivo ANTES de escrever qualquer YAML.** Ninguém corrige as suas respostas (o `lab verify` só avisa se ele continuar em branco):
> serve para você pensar. Pode rascunhar no papel e resumir aqui. Respostas curtas e objetivas bastam.
> O método completo, com um exemplo resolvido, está em `docs/metodo.md`.

## 1. Estado desejado

> O que precisa ser verdade ao final? Como você vai provar que está verdade?
> - O que deve estar instalado e o que deve estar rodando? Como você prova isso em cada nó, sem confiar no playbook?
> - O que a segunda execução deve mostrar no recap?

**Sua resposta:**

<!-- escreva abaixo desta linha -->
Em web1 e web2: 4 pacotes instalados e crond ativo e habilitado. Prova: rpm -q, systemctl is-active e is-enabled; 2ª execução com changed=0.

## 2. Inventário

> Quem são os alvos e como estão agrupados?
> - Em quais hosts o play age? Quais hosts NÃO podem ser tocados?

**Sua resposta:**

<!-- escreva abaixo desta linha -->
Só o grupo web. db1 e lb1 não podem ser tocados.

## 3. Variáveis

> O que muda entre hosts ou ambientes? Em qual camada cada valor mora?
> - A lista de pacotes é um valor fixo ou algo que mudaria entre ambientes? Onde ela deveria morar numa automação maior?

**Sua resposta:**

<!-- escreva abaixo desta linha -->
Lista de pacotes e nome do serviço: valores fixos aqui; numa automação maior viriam de variáveis (group_vars).

## 4. Estrutura

> Quais plays, tasks ou roles, e em que ordem?
> - Quantos plays? Quais tasks, em que ordem? Existe dependência entre elas?

**Sua resposta:**

<!-- escreva abaixo desta linha -->
Um play em web com become. Task 1: pacotes (lista, state present). Task 2: serviço (started e enabled).

## 5. Risco

> O que pode falhar? Como validar antes de aplicar? Como voltar atrás?
> - Que privilégio o play precisa e onde ele é declarado? Que comando mostra o que o playbook faria sem alterar nada?

**Sua resposta:**

<!-- escreva abaixo desta linha -->
Falta de privilégio: become no play. Valido com --check --diff antes; para voltar atrás, state absent nos pacotes e parar o serviço.

