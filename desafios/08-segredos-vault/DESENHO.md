# DESENHO — Desafio 08: Segredos com Ansible Vault

> **Preencha este arquivo ANTES de escrever qualquer YAML.** Ninguém corrige as suas respostas (o `lab verify` só avisa se ele continuar em branco):
> serve para você pensar. Pode rascunhar no papel e resumir aqui. Respostas curtas e objetivas bastam.
> O método completo, com um exemplo resolvido, está em `docs/metodo.md`.

## 1. Estado desejado

> O que precisa ser verdade ao final? Como você vai provar que está verdade?
> - O que precisa ser verdade nos nós web ao final? E o que precisa ser verdade (e falso!) na pasta do projeto e na saída do Ansible?

**Sua resposta:**

<!-- escreva abaixo desta linha -->

## 2. Inventário

> Quem são os alvos e como estão agrupados?
> - Em quais hosts a conta deve existir? E em quais ela não pode aparecer?

**Sua resposta:**

<!-- escreva abaixo desta linha -->

## 3. Variáveis

> O que muda entre hosts ou ambientes? Em qual camada cada valor mora?
> - Quais valores são secretos e quais não são? Qual nome cada um terá no arquivo visível e no cofre? Em qual camada (`group_vars/web/`, `host_vars/`, play) cada arquivo mora?

**Sua resposta:**

<!-- escreva abaixo desta linha -->

## 4. Estrutura

> Quais plays, tasks ou roles, e em que ordem?
> - Que arquivos você vai criar, com que comando, e que tasks entram em `site.yml`? Como o `site.yml` vai obter o valor do segredo sem que ele apareça no projeto?

**Sua resposta:**

<!-- escreva abaixo desta linha -->

## 5. Risco

> O que pode falhar? Como validar antes de aplicar? Como voltar atrás?
> - Por onde o segredo pode vazar (arquivo, `-v`, `debug`, histórico do shell, Git)? O que acontece com a idempotência da task que define a senha? Como você valida antes de aplicar?

**Sua resposta:**

<!-- escreva abaixo desta linha -->
