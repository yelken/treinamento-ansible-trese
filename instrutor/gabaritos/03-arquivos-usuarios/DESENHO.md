# DESENHO — Desafio 03: Arquivos, usuários e permissões

> **Preencha este arquivo ANTES de escrever qualquer YAML.** Ninguém corrige as suas respostas (o `lab verify` só avisa se ele continuar em branco):
> serve para você pensar. Pode rascunhar no papel e resumir aqui. Respostas curtas e objetivas bastam.
> O método completo, com um exemplo resolvido, está em `docs/metodo.md`.

## 1. Estado desejado

> O que precisa ser verdade ao final? Como você vai provar que está verdade?
> - Liste cada item que precisa existir (arquivo, diretório, grupo, usuário, regra) com dono, grupo e modo esperados.
> - Como você provaria cada item em um nó, sem olhar o playbook?

**Sua resposta:**

<!-- escreva abaixo desta linha -->
Em todos os nós: banner no motd, 3 diretórios com dono e modo, grupo e 3 usuários, sudoers do grupo, PASS_MAX_DAYS 90, marcos removido. Prova: stat, getent, sudo -l -U, visudo -c.

## 2. Inventário

> Quem são os alvos e como estão agrupados?
> - Em quais nós o play age? Os dois sistemas (Rocky e Debian) precisam de tratamento diferente em algum item?

**Sua resposta:**

<!-- escreva abaixo desta linha -->
Os 4 nós (all). Os dois sistemas aceitam os mesmos módulos e caminhos desta missão.

## 3. Variáveis

> O que muda entre hosts ou ambientes? Em qual camada cada valor mora?
> - A lista de usuários administrativos é um dado ou uma decisão de código? Onde ela deveria morar numa automação com 30 administradores?

**Sua resposta:**

<!-- escreva abaixo desta linha -->
A lista de admins deveria ser variável (group_vars) e a task faria loop. Hoje fica na própria task por ser pequena.

## 4. Estrutura

> Quais plays, tasks ou roles, e em que ordem?
> - O que precisa existir antes do quê? Desenhe as dependências (grupo, usuário, diretório, regra de sudo).

**Sua resposta:**

<!-- escreva abaixo desta linha -->
Grupo antes de diretórios e usuários; sudoers depois dos usuários; remoção do marcos independente; motd e login.defs em qualquer ordem.

## 5. Risco

> O que pode falhar? Como validar antes de aplicar? Como voltar atrás?
> - Qual item, se estiver errado, pode trancar o acesso administrativo dos nós? Como você valida esse item antes de ele valer? E a remoção de usuário: o que se perde junto?

**Sua resposta:**

<!-- escreva abaixo desta linha -->
Sudoers errado tranca o acesso: uso validate com visudo. Remover marcos apaga o home dele: conferir antes se há algo a preservar. Voltar atrás: reverter o commit e reaplicar.

