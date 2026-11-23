# Desafio 07 — Da lista de tasks à role

| | |
|---|---|
| **Dia do curso** | Dia 3 — Reuso, segredos e orquestração (25/11) |
| **Missão essencial** | ~35 minutos |
| **Conceitos** | estrutura de role, `defaults` × `vars`, handlers e templates dentro da role, `ansible-galaxy role init` |
| **Pasta de trabalho** | `/lab/07-da-lista-a-role` (no nó de controle) |

---

## Teoria

### Por que roles

Um playbook que cresce vira um arquivo de 300 linhas em que ninguém acha nada, e a próxima automação que precisa "instalar e configurar o Postgres" começa copiando e colando. A **role** é a unidade de reuso do Ansible: uma pasta com uma estrutura fixa que empacota **tasks, handlers, templates, arquivos e variáveis** de uma responsabilidade (por exemplo, "servidor de banco"). O playbook passa a dizer **onde** aplicar e **quais roles**, e não **como**.

### A estrutura

`ansible-galaxy role init <nome>` cria o esqueleto. Um exemplo, em outro cenário:

```text
roles/servidor_banco/
├── defaults/main.yml    # valores padrão, os mais fáceis de sobrepor
├── vars/main.yml        # valores internos da role (difíceis de sobrepor)
├── tasks/main.yml       # a lista de tasks
├── handlers/main.yml    # handlers (notify aponta para eles)
├── templates/           # arquivos .j2 usados pela role
├── files/               # arquivos estáticos para o copy
├── meta/main.yml        # autoria, plataformas, dependências
└── README.md            # como usar: variáveis, exemplo
```

E o playbook que a usa fica assim:

```yaml
- name: Banco de dados do sistema
  hosts: bancos
  become: true
  roles:
    - role: servidor_banco
      servidor_banco_porta: 5433
```

### `defaults` ou `vars`?

- **`defaults/main.yml`**: a **interface pública** da role. São os valores que o usuário da role **pode** (e deve) ajustar. Têm a **menor precedência** de todas: qualquer `group_vars`, `host_vars` ou `-e` os sobrepõe.
- **`vars/main.yml`**: constantes **internas**, que o usuário não deveria mexer. Têm precedência **alta**: `group_vars` e `host_vars` não conseguem sobrepô-las.

Regra prática: se o usuário da role precisa poder mudar, é `defaults`.

### O prefixo no nome das variáveis

Variáveis de role compartilham o mesmo "espaço" das do play e do inventário. Se duas roles usam `porta`, uma sobrescreve a outra. Por convenção, **toda variável da role leva o nome da role como prefixo**: `servidor_banco_porta`, não `porta`. É a defesa contra colisões e deixa claro, em qualquer lugar do projeto, a quem a variável pertence.

### Onde o Ansible procura arquivos de uma role

Dentro de uma role, o `template` com `src: arquivo.j2` procura primeiro em `roles/<nome>/templates/`. O mesmo vale para `copy` e `files/`. Por isso a role é **autocontida**: dá para copiá-la para outro projeto sem levar mais nada.

### O que acontece por baixo

Quando o playbook lista uma role, o Ansible a expande em uma sequência: dependências (`meta`), `defaults` e `vars` carregadas, `tasks/main.yml` executada e `handlers/main.yml` disponibilizados, como se tudo estivesse escrito ali. Os handlers continuam rodando no **fim do play**, e o `notify` funciona igual.

---

## Cenário

O playbook do servidor web do **Órgão Exemplo** funcionou bem, mas agora a equipe do **ambiente de treinamento** quer o mesmo servidor também, e o time de **portais** quer outra variação. Ninguém quer copiar o arquivo: a decisão é transformar a automação em uma **role reutilizável** e reduzir o playbook a poucas linhas.

O ponto de partida é um playbook **monolítico**, que já funciona. Ao rodar `lab start 07`, ele aparece na sua pasta como **`monolitico.yml`**, com os seus templates em `templates/`. **O seu trabalho é a refatoração**: o resultado final nos servidores deve ser **o mesmo**.

## Missão essencial

Crie a role **`servidor_web`** em `roles/servidor_web/` e o playbook **`site.yml`** (nesta pasta, `hosts: web`) de modo que:

1. O playbook `site.yml` use **apenas a role**: tem `roles:` e **nenhuma** task, `pre_tasks`, `post_tasks` ou `handlers` soltos.
2. A role tenha a estrutura de uma role de verdade: `tasks/main.yml`, `handlers/main.yml`, `defaults/main.yml`, `templates/*.j2` (dentro da role) e `README.md`. Use `ansible-galaxy role init` para começar.
3. As variáveis que o usuário da role pode ajustar vivam em **`defaults/main.yml`**, todas com o **prefixo `servidor_web_`**. Duas são obrigatórias:
   - **`servidor_web_porta`**, padrão `8081`;
   - **`servidor_web_ambiente`**, padrão `homologacao`.
4. O **`README.md` da role** descreva **cada variável** de `defaults/main.yml` (nome, para que serve, valor padrão).
5. O resultado nos servidores seja o **mesmo do monolítico**: nginx instalado, ativo e habilitado; configuração válida (`nginx -t`); página em `http://<servidor>:<porta>/` com o **nome do host** e o **ambiente**; recarga por handler **somente quando algo muda**.
6. O playbook seja **idempotente** (segunda execução com `changed=0`, sem handler).
7. Toda task com `name` e todo módulo com FQCN.

## Critérios de aceite

- [ ] `site.yml` existe.
- [ ] `site.yml` passa na checagem de sintaxe.
- [ ] `site.yml` usa só a role (sem `tasks`, `pre_tasks`, `post_tasks` ou `handlers` soltos).
- [ ] A role `servidor_web` tem `tasks/main.yml`, `handlers/main.yml`, `defaults/main.yml`, `README.md` e ao menos um `.j2` em `templates/`.
- [ ] As variáveis de `defaults/main.yml` têm o prefixo `servidor_web_` e incluem `servidor_web_porta` e `servidor_web_ambiente`.
- [ ] O `README.md` da role cita todas as variáveis de `defaults/main.yml`.
- [ ] As tasks e handlers da role têm `name` e usam FQCN.
- [ ] A porta e o ambiente **não** estão em `vars/main.yml` da role (onde ninguém conseguiria sobrepô-los pelo inventário).
- [ ] O playbook executa sem erros em `web1` e `web2` a partir dos nós sem nginx (o verificador remove o nginx antes).
- [ ] Segunda rodada com `changed=0`.
- [ ] Na segunda rodada, nenhum handler é executado.
- [ ] Executado com `-e servidor_web_porta=8082 -e servidor_web_ambiente=producao`, o playbook termina sem erros.
- [ ] Nessa execução, o handler roda em `web1` e `web2`.
- [ ] O nginx está ativo e habilitado, e `nginx -t` aprova a configuração, em `web1` e `web2`.
- [ ] A página responde na porta padrão (8081) e mostra o nome do host e `homologacao`.
- [ ] Com os valores sobrepostos, a página passa a responder na porta 8082 e mostra `producao`.
- [ ] A porta 8081 deixa de responder.

## Antes de começar

1. No terminal do seu computador: `lab start 07` (ele também coloca o `monolitico.yml` e os `templates/` na sua pasta).
2. Preencha o **`DESENHO.md`** desta pasta **antes** de mexer em qualquer arquivo.
3. No nó de controle (`lab shell`): `cd /lab/07-da-lista-a-role`.

## Como verificar

```bash
lab verify 07
```

Antes, para a sua conferência: `ansible-playbook site.yml` duas vezes (a segunda com `changed=0`), `ansible-playbook site.yml --list-tasks` (confira se as tasks da role aparecem com o nome da role como prefixo) e `ansible-lint`.

## Dicas

<details>
<summary>Dica 1 — conceitual</summary>

Antes de mover qualquer coisa, faça duas listas no `DESENHO.md`: (1) o que no `monolitico.yml` é **lógica** (tasks, handler, templates) e (2) o que é **dado ajustável** (variáveis). A lógica vai para dentro da role. Dos dados, quais o usuário da role precisa poder mudar? Esses são a **interface** da role.

Depois, pergunte-se: ao sair do playbook, **quem passa a ser responsável por cada coisa**? Se sobrar alguma task "solta" no `site.yml`, ela pertence a alguma role?

</details>

<details>
<summary>Dica 2 — mais direta</summary>

- O comando `ansible-galaxy role init --init-path roles servidor_web` cria o esqueleto na pasta certa. Apague o que não for usar.
- Cada seção do monolítico tem um lugar na role: `tasks:` → `tasks/main.yml` (sem o `tasks:`: o arquivo é **uma lista de tasks**), `handlers:` → `handlers/main.yml`, `vars:` ajustáveis → `defaults/main.yml`, templates → `templates/` **da role**.
- **Renomeie as variáveis** com o prefixo da role, **também dentro dos templates**. Um nome esquecido gera `undefined variable`.
- A variável do diretório do site, `raiz_site`, é algo que o usuário da role precisa mudar? Se não, onde deveria morar?
- O `README.md` gerado pelo `init` é só um modelo: edite-o, listando as variáveis.
- Para o `site.yml` ficar pequeno, o que fica dentro de `roles:`?

</details>

<details>
<summary>Dica 3 — o módulo e o parâmetro</summary>

- `ansible-galaxy role init --init-path roles servidor_web`.
- `defaults/main.yml`: um dicionário YAML simples: `servidor_web_porta: 8081`.
- `tasks/main.yml` e `handlers/main.yml`: **listas** de tasks (começam com `- name: ...`).
- Playbook: `roles: [ servidor_web ]`, dentro do play.
- Constante interna da role (não ajustável): `vars/main.yml`. Valor ajustável: `defaults/main.yml`.
- Para ver como o Ansible enxerga as tasks: `ansible-playbook site.yml --list-tasks`.
- `ansible-doc -t keyword roles`.

</details>

## Perguntas de reflexão

1. Outro time quer usar a role `servidor_web` com uma página diferente. Quais variáveis (ou arquivos) você precisaria **expor** para que isso aconteça **sem editar a role**?
2. Duas roles do mesmo projeto usam `porta` sem prefixo. O que acontece? Como você descobriria o que aconteceu?
3. Quando **não** vale a pena criar uma role? Quantas vezes uma automação precisa se repetir para compensar o custo?

## Extensão opcional

**Role publicável.** Faça a role passar no `ansible-lint` (perfil `production`, já configurado na pasta) **sem nenhum apontamento**, o que inclui preencher o `meta/main.yml` (autor, descrição, licença, plataformas) e remover do esqueleto o que não é usado. Ao rodar `lab verify 07`, uma seção extra roda `ansible-lint` sobre `site.yml` e `roles/servidor_web` (ela não conta para o resultado da missão).

## Para saber mais

```bash
ansible-galaxy role init --help
ansible-doc -t keyword roles
ansible-playbook site.yml --list-tasks
ansible-lint
```

- [Roles](https://docs.ansible.com/ansible/latest/playbook_guide/playbooks_reuse_roles.html)
- [Precedência de variáveis](https://docs.ansible.com/ansible/latest/playbook_guide/playbooks_variables.html#understanding-variable-precedence)
- [Boas práticas: organização do conteúdo](https://docs.ansible.com/ansible/latest/tips_tricks/ansible_tips_tricks.html)
