# Desafio 06 — Condicionais, loops e erros

| | |
|---|---|
| **Dia do curso** | Dia 2 — Playbooks em profundidade (24/11) |
| **Missão essencial** | ~35 minutos |
| **Conceitos** | `loop`, `when`, `register`, `until`, `block`/`rescue`/`always`, `failed_when`, `changed_when` |
| **Pasta de trabalho** | `/lab/06-condicionais-loops-erros` (no nó de controle) |

---

## Teoria

### Repetir: `loop`

Quando a mesma task precisa rodar para vários itens, não copie a task: dê a ela uma lista. O item corrente é a variável `item`.

```yaml
- name: Criar as contas de serviço
  ansible.builtin.user:
    name: "{{ item.nome }}"
    shell: "{{ item.shell | default('/sbin/nologin') }}"
  loop: "{{ contas_de_servico }}"
  loop_control:
    label: "{{ item.nome }}"      # a saída mostra só o nome, não o dicionário inteiro
```

A lista é **dado**: pode vir de um arquivo (`vars_files`, `include_vars`) e mudar sem tocar na task.

### Decidir: `when`

`when` recebe uma expressão Jinja2 (sem `{{ }}`) e decide se a task roda **naquele host**. Em um laço, a condição é avaliada **a cada item**.

```yaml
  loop: "{{ contas_de_servico }}"
  when: item.ativa | bool
```

Uma task pulada aparece como `skipping`; ela não é um erro e não conta como `changed`.

### Guardar resultados: `register`

`register: nome` guarda o retorno da task em uma variável. Ela traz `rc`, `stdout`, `status`, `content` e `changed`, dependendo do módulo. Muito útil para decidir a próxima task.

### Tentar de novo: `until`

Serviços levam tempo para subir. Em vez de um `sleep` fixo, repita a verificação até dar certo:

```yaml
- name: Esperar a API responder
  ansible.builtin.uri:
    url: http://localhost:9000/ping
  register: ping
  until: ping.status == 200
  retries: 10
  delay: 3
```

### Definir o que é falha: `failed_when` e `changed_when`

Por padrão, uma task de `command` é `changed` sempre e só falha com código de saída diferente de zero. Você pode **redefinir** isso: `failed_when: "'ERRO' in resultado.stdout"` e `changed_when: false` para comandos que só leem. Tasks de `command` e `shell` **sem** `changed_when` quebram a idempotência e são apontadas pelo `ansible-lint`.

### Plano de retorno: `block`, `rescue`, `always`

É o `try/catch/finally` do Ansible:

```yaml
- name: Migrar o esquema com plano de retorno
  block:
    - name: Copiar o dump de segurança
      ansible.builtin.command: pg_dump -f /srv/bkp/antes.sql appdb
      changed_when: true
    - name: Aplicar a migração
      ansible.builtin.command: /opt/app/migrar.sh
      changed_when: true
  rescue:
    - name: Restaurar o dump de segurança
      ansible.builtin.command: psql -f /srv/bkp/antes.sql appdb
      changed_when: true
    - name: Avisar que a migração foi desfeita
      ansible.builtin.fail:
        msg: "A migração falhou e o esquema voltou ao estado anterior."
  always:
    - name: Remover a trava
      ansible.builtin.file:
        path: /run/migracao.lock
        state: absent
```

- Se tudo no `block` passa, o `rescue` é ignorado.
- Se algo no `block` falha, o `rescue` roda. Se o `rescue` termina bem, o play **continua como se nada tivesse falhado** (o host é considerado recuperado). Para que a falha **apareça**, o próprio `rescue` precisa terminar com `ansible.builtin.fail`.
- O `always` roda **de qualquer jeito**.

---

## Cenário

O **Portal de Avisos** do **Órgão Exemplo** é servido pelo nginx de `web1` e `web2`, na porta **8081**. O ambiente de homologação já está no ar com uma versão inicial. A equipe de conteúdo pediu duas coisas:

1. **Áreas do portal.** Cada área ativa precisa ter a sua pasta e a sua página; áreas desativadas precisam sumir. A lista de áreas muda com frequência, então ela vive em um **arquivo de dados** (`dados/areas.yml`).
2. **Publicação de versões do site.** Publicar deve ser **seguro**: se a nova versão não passar na verificação de saúde, o portal **volta sozinho** para a versão anterior e o time é avisado de forma clara. Nunca pode ficar fora do ar.

## Missão essencial

### Parte A: as áreas (`areas.yml`)

Escreva o playbook **`areas.yml`** (hosts `web`). A lista vem da variável **`areas`** (já definida em `dados/areas.yml`; cada item tem `nome` e `ativa`). Ao final, em `web1` e `web2`:

- para cada área **ativa**: o diretório `/var/www/portal/areas/<nome>/` existe (dono `root:root`, modo `0755`) e contém `index.html` (modo `0644`) com o **nome da área** no texto;
- para cada área **inativa**: o diretório `/var/www/portal/areas/<nome>/` **não existe** (ele pode já existir, deixado por versões antigas do portal);
- o playbook usa **`loop`** e **`when`**, e é **idempotente**.

O verificador também troca a lista (`-e` com outra lista `areas`) para provar que o playbook **obedece aos dados**, e não aos nomes que você viu.

### Parte B: a publicação (`publicar.yml`)

Escreva o playbook **`publicar.yml`** (hosts `web`). Ele recebe duas variáveis:

- **`versao`**: o nome da versão a publicar (sem valor padrão: é sempre informada com `-e versao=...`);
- **`dir_releases`**: a pasta, **no nó de controle**, onde ficam as versões. **Padrão: a pasta `releases/` ao lado do playbook.** Cada versão é um diretório `<dir_releases>/<versao>/` com um `index.html`.

O comportamento esperado, em `web1` e `web2`:

1. A versão é copiada para `/var/www/portal/releases/<versao>/` e o link simbólico **`/var/www/portal/atual`** passa a apontar para ela (o nginx serve a pasta `atual`).
2. **Verificação de saúde:** `http://localhost:8081/` (acessado **a partir do próprio nó**) deve responder **200** e a página deve conter o texto **`PORTAL-OK`**. Dê ao servidor uma chance de se firmar: repita a verificação algumas vezes (`until`) antes de concluir que falhou.
3. **Se a verificação falhar**: o link `atual` **volta para a versão que estava no ar antes**, e o play termina **com falha**, com uma mensagem clara que **cita o nome da versão rejeitada**. O portal continua respondendo a versão anterior, sem interrupção.
4. **Em qualquer caso** (sucesso ou falha), o arquivo **`/var/log/portal/ultima-publicacao.txt`** é atualizado com duas linhas: `versao=<versao>` e `resultado=ok` (ou `resultado=falha`).
5. Publicar duas vezes seguidas a **mesma** versão válida termina com `changed=0` na segunda.

Na pasta `releases/` há duas versões de exemplo, para você testar: `exemplo-valida` (contém `PORTAL-OK`) e `exemplo-defeito` (não contém).

## Critérios de aceite

- [ ] `areas.yml` existe.
- [ ] `areas.yml` passa na checagem de sintaxe.
- [ ] `publicar.yml` existe.
- [ ] `publicar.yml` passa na checagem de sintaxe.
- [ ] Todas as tasks dos dois playbooks têm `name`.
- [ ] Todos os módulos dos dois playbooks usam o nome completo (FQCN).
- [ ] `areas.yml` usa `loop` e `when`.
- [ ] `publicar.yml` usa `block`, `rescue` e `always`.
- [ ] `publicar.yml` usa `until` com `retries`.
- [ ] `areas.yml` executa sem erros a partir do estado inicial.
- [ ] Segunda rodada de `areas.yml` com `changed=0`.
- [ ] Áreas ativas existem e áreas inativas não existem, em `web1` e `web2`.
- [ ] Com outra lista de áreas, o resultado nos nós acompanha a nova lista.
- [ ] Publicar uma versão válida termina sem erros.
- [ ] Publicar a mesma versão de novo termina com `changed=0`.
- [ ] Publicar uma segunda versão válida a coloca no ar, nos dois nós.
- [ ] O registro da publicação traz `versao=` e `resultado=ok`.
- [ ] Publicar uma versão defeituosa termina com falha e uma mensagem que cita a versão.
- [ ] Depois da falha, a versão anterior continua respondendo `PORTAL-OK` nos dois nós.
- [ ] O registro da falha traz `versao=` da versão rejeitada e `resultado=falha`.

## Antes de começar

1. No terminal do seu computador: `lab start 06`.
2. Preencha o **`DESENHO.md`** desta pasta **antes** de escrever qualquer YAML.
3. No nó de controle (`lab shell`): `cd /lab/06-condicionais-loops-erros`.

## Como verificar

```bash
lab verify 06
```

Antes, para a sua conferência: `ansible-playbook areas.yml` duas vezes (o recap da segunda diz algo?); `ansible-playbook publicar.yml -e versao=exemplo-valida` e depois `-e versao=exemplo-defeito`. Em um nó, `curl http://localhost:8081/` mostra o que o portal está servindo.

## Dicas

<details>
<summary>Dica 1 — conceitual</summary>

Parte A: para cada item da lista há **duas** situações (ativa, inativa), e cada uma pede um estado diferente. Quantas tasks isso dá? O `when` decide qual delas vale para cada item.

Parte B: desenhe o fluxo em linhas: *o que eu preciso saber antes de mudar o link?* (para onde ele apontava), *o que é mudar*, *como saber que deu certo*, *o que fazer se não deu*. Cada linha é uma ou mais tasks; quais delas pertencem ao "tentar" e quais ao "se falhar"?

</details>

<details>
<summary>Dica 2 — mais direta</summary>

- Parte A: a lista pode vir de `vars_files` no play. Em um laço com `when`, o item é `item`; um booleano em YAML já é um booleano.
- Parte B: o módulo que consulta o alvo de um link simbólico devolve esse caminho no resultado. Guarde-o com `register` **antes** de trocar o link.
- A verificação de saúde precisa de **três** coisas: o código HTTP, o conteúdo da página e a repetição. Cada módulo tem parâmetros para as duas primeiras; a terceira é uma palavra-chave da task.
- No `rescue`, desfazer não basta: se o `rescue` terminar bem, o play considera que **não houve falha**. Como fazer a falha ser reportada?
- Não se esqueça: o `always` precisa saber se deu certo ou não. De onde vem essa informação?
- O `copy` de um diretório inteiro tem uma regra sobre a barra final do `src`. Leia o `ansible-doc`.

</details>

<details>
<summary>Dica 3 — o módulo e o parâmetro</summary>

- `ansible.builtin.file`: `state: directory` / `state: absent` / `state: link` (com `src` e `dest`, ou `path`).
- `ansible.builtin.copy`: `content`, `dest`, `owner`, `mode`; para diretório, `src` terminado em `/`.
- `ansible.builtin.stat`: `path`; o resultado traz `stat.lnk_source` para links simbólicos.
- `ansible.builtin.uri`: `url`, `status_code`, `return_content: true`, mais `register`.
- Verificação: `until: resposta.status == 200 and 'PORTAL-OK' in resposta.content`, com `retries` e `delay`.
- Falha explícita: `ansible.builtin.fail` com `msg`.
- Para decidir o que escrever no registro, `ansible.builtin.set_fact` dentro do `block` e do `rescue`, ou variáveis do próprio Ansible.
- `ansible-doc ansible.builtin.uri`, `ansible-doc ansible.builtin.stat`, `ansible-doc -t keyword block`.

</details>

## Perguntas de reflexão

1. Se a versão defeituosa fosse publicada em **400** servidores ao mesmo tempo, o plano de retorno de cada nó basta? Que mecanismo do Ansible (você o verá no desafio 09) limitaria o estrago a poucos nós?
2. Por que o `rescue` termina com `fail`, em vez de simplesmente voltar o link e deixar o play seguir em frente? Quem precisa saber que a publicação foi rejeitada?
3. O `always` grava o resultado mesmo quando a publicação falha. Que decisão operacional **fora do Ansible** (um painel, um chamado, uma automação de CI) depende desse registro?

## Extensão opcional

**Histórico enxuto.** Depois de publicar, **mantenha apenas as três versões mais recentes** em `/var/www/portal/releases/`, **sem nunca apagar a versão que está no ar**. Ao rodar `lab verify 06`, uma seção extra publica versões em sequência e confere que sobraram no máximo 3 diretórios e que a ativa continua presente (ela não conta para o resultado da missão).

## Para saber mais

```bash
ansible-doc ansible.builtin.uri
ansible-doc ansible.builtin.stat
ansible-doc ansible.builtin.fail
ansible-doc -t keyword -l | grep -E "^(block|rescue|always|until|retries|loop)"
```

- [Condicionais](https://docs.ansible.com/ansible/latest/playbook_guide/playbooks_conditionals.html)
- [Laços (loops)](https://docs.ansible.com/ansible/latest/playbook_guide/playbooks_loops.html)
- [Blocos e tratamento de erros](https://docs.ansible.com/ansible/latest/playbook_guide/playbooks_blocks.html) e [definindo falha e mudança](https://docs.ansible.com/ansible/latest/playbook_guide/playbooks_error_handling.html)
