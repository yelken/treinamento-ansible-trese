# DESENHO — Desafio 07: Da lista de tasks à role

> **Preencha este arquivo ANTES de escrever qualquer YAML.** Ninguém corrige as suas respostas (o `lab verify` só avisa se ele continuar em branco):
> serve para você pensar. Pode rascunhar no papel e resumir aqui. Respostas curtas e objetivas bastam.
> O método completo, com um exemplo resolvido, está em `docs/metodo.md`.

## 1. Estado desejado

> O que precisa ser verdade ao final? Como você vai provar que está verdade?
> - O que precisa continuar verdade nos servidores depois da refatoração? Como você prova que o resultado é o mesmo do monolítico (página, serviço, `nginx -t`, handler, `changed=0`)?
> - O que precisa ser verdade na pasta do projeto (estrutura da role, `site.yml` enxuto, README da role)?

**Sua resposta:**

Igual ao desafio 05: nginx ativo e habilitado, `nginx -t` aprovado, página na porta 8081 com host e ambiente, handler só quando muda. Além disso: `site.yml` com apenas `roles:` e README da role descrevendo as variáveis.

## 2. Inventário

> Quem são os alvos e como estão agrupados?
> - Em quais hosts a role se aplica? Ela deveria saber em quais hosts ela vai rodar?

**Sua resposta:**

Mesmo alvo do monolítico: o grupo `web` (web1, web2).

## 3. Variáveis

> O que muda entre hosts ou ambientes? Em qual camada cada valor mora?
> - Liste cada variável do `monolitico.yml`. Quais o usuário da role deve poder ajustar (`defaults`)? Qual é constante interna (`vars`)? Qual será o nome de cada uma com o prefixo da role?

**Sua resposta:**

Ajustáveis (interface): `servidor_web_porta` e `servidor_web_ambiente`, em `defaults/main.yml`. Interna: `servidor_web_raiz`, em `vars/main.yml`. Todas com o prefixo do nome da role.

## 4. Estrutura

> Quais plays, tasks ou roles, e em que ordem?
> - O que do monolítico vai para `tasks/`, `handlers/`, `templates/`, `defaults/`? O que sobra no `site.yml`? Em que ordem você vai mover as peças para poder testar a cada passo?

**Sua resposta:**

Role `servidor_web` (tasks, handlers, defaults, vars, templates, meta, README). O playbook `site.yml` fica com um play: `hosts: web`, `become: true`, `roles: [servidor_web]`.

## 5. Risco

> O que pode falhar? Como validar antes de aplicar? Como voltar atrás?
> - O que pode quebrar na refatoração (nome de variável esquecido, caminho do template)? Como validar antes de aplicar (`--syntax-check`, `--list-tasks`, `--check --diff`)? Como voltar atrás se algo der errado?

**Sua resposta:**

Risco: esquecer de renomear uma variável dentro de um template (`undefined variable`). Valido com `--list-tasks`, `--check --diff`, segunda execução com `changed=0` e `ansible-lint`. Voltar atrás: o `monolitico.yml` continua intacto.
