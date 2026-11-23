# Desafio 03 — Arquivos, usuários e permissões

| | |
|---|---|
| **Dia do curso** | Dia 1 — Fundamentos (23/11) |
| **Missão essencial** | ~15 minutos |
| **Conceitos** | `copy`, `file`, `user`, `group`, `lineinfile`, modos e donos, `state: absent`, `validate` |
| **Pasta de trabalho** | `/lab/03-arquivos-usuarios` (no nó de controle) |

---

## Teoria

### Os módulos do dia a dia

Quase toda padronização de servidor é feita de cinco peças:

- **`ansible.builtin.file`** garante que um caminho **exista como diretório** (`state: directory`), **não exista** (`state: absent`), ou tenha certo dono e modo.
- **`ansible.builtin.copy`** publica um arquivo no alvo, a partir de um arquivo seu (`src`) ou de um texto (`content`).
- **`ansible.builtin.lineinfile`** garante que **uma linha** exista (ou não) dentro de um arquivo que você não controla por inteiro: ele procura a linha pelo `regexp` e a substitui; se não achar, acrescenta.
- **`ansible.builtin.group`** e **`ansible.builtin.user`** cuidam de grupos e contas. Com `user`, `groups` + `append: true` **acrescenta** o usuário a grupos sem tirá-lo dos que já tem.

### Donos e modos

`owner`, `group` e `mode` aparecem em quase todos esses módulos. Um cuidado clássico: o **modo é um texto**. Escreva-o **entre aspas** e com quatro dígitos (`"0640"`), para o YAML não o interpretar como número. O primeiro dígito carrega bits especiais: em `"2770"`, o `2` é o **setgid** — arquivos criados no diretório herdam o grupo dele. O modo também aceita a forma simbólica (`u=rwx,g=rx,o=`).

### Ordem importa

O Ansible executa as tasks **de cima para baixo**. Se um diretório deve pertencer a um grupo, o grupo precisa existir **antes** da task que o usa; se um usuário entra em um grupo, o grupo também vem antes. Pense nas dependências ao desenhar.

### Remover também é declarar estado

`state: absent` diz "isto não deve existir" — e é idempotente: se já não existe, nada muda. No módulo `user`, remover a conta **não** apaga o diretório pessoal, a menos que você peça (`remove: true`). Cada módulo tem seus próprios detalhes: leia o `ansible-doc`.

### Validar antes de valer

Alguns arquivos são perigosos de errar: um erro de sintaxe em uma configuração de serviço pode derrubá-lo; um erro no `sudoers` pode **trancar o acesso administrativo**. Os módulos `copy`, `template` e `lineinfile` aceitam `validate`: um comando que recebe o arquivo **temporário** (no lugar do `%s`) e só deixa o Ansible instalá-lo no destino se terminar com sucesso.

Exemplo, em um caso **diferente** do desta missão — um serviço de relatórios fictício:

```yaml
- name: Garantir o grupo e a conta de serviço
  ansible.builtin.group:
    name: relatorios
    state: present

- name: Garantir o usuário de serviço
  ansible.builtin.user:
    name: svc_relatorio
    groups: relatorios
    append: true
    shell: /sbin/nologin
    create_home: false

- name: Publicar a configuração, validando o JSON antes
  ansible.builtin.copy:
    content: '{"retencao_dias": 30}'
    dest: /etc/relatorio/config.json
    owner: root
    group: relatorios
    mode: "0640"
    validate: /usr/bin/python3 -m json.tool %s

- name: Ajustar uma opção em um arquivo que já existe
  ansible.builtin.lineinfile:
    path: /etc/default/relatorio
    regexp: '^RETENCAO='
    line: RETENCAO=30
    create: true
    mode: "0644"
```

### O que acontece por baixo

O `copy` envia o conteúdo para um arquivo temporário no alvo, **compara o checksum** com o destino e, se forem iguais, devolve `ok` sem tocar em nada; se forem diferentes, roda o `validate` sobre o temporário e só então move para o lugar. O `lineinfile` lê o arquivo, procura a linha pelo `regexp` e só reescreve se o conteúdo for diferente. O `user` consulta a conta atual (como `getent passwd`) e só chama `useradd`, `usermod` ou `userdel` quando precisa. É por isso que tudo isso é idempotente.

---

## Cenário

Uma auditoria interna do **Órgão Exemplo** apontou que os servidores do ambiente de homologação não seguem o padrão de acesso do órgão: faltam o aviso legal de acesso, a estrutura de diretórios de operação, o grupo de administradores com permissão de `sudo` controlada e a política de validade de senhas. Além disso, um analista que foi desligado, **`marcos`**, ainda tem conta ativa nos servidores.

A padronização vale para **os quatro nós** (`web1`, `web2`, `db1`, `lb1`) — dois sistemas diferentes, um só playbook. O inventário já está pronto em `inventario/`.

## Missão essencial

Escreva o playbook **`site.yml`** (nesta pasta) de modo que, em **todos os nós**, ao final:

1. **Banner:** o arquivo `/etc/motd` contém a linha `ACESSO RESTRITO - USO EXCLUSIVO DE PESSOAL AUTORIZADO`; dono `root:root`, modo `0644`.
2. **Diretórios** (devem existir, com este dono/grupo e modo):

   | Caminho | Dono:grupo | Modo |
   |---|---|---|
   | `/opt/infra` | `root:root` | `0755` |
   | `/opt/infra/scripts` | `root:adm-infra` | `0750` |
   | `/opt/infra/relatorios` | `root:adm-infra` | `2770` |

3. **Administradores:** o grupo `adm-infra` existe, e os usuários `ana`, `bruno` e `carla` existem, com shell `/bin/bash`, diretório pessoal e **membros** de `adm-infra`.
4. **Sudo:** membros de `adm-infra` podem executar qualquer comando via `sudo`, **sem senha**, por uma regra no arquivo `/etc/sudoers.d/adm-infra` (dono `root:root`, modo `0440`), **gravada com `validate`**.
5. **Senhas:** o arquivo `/etc/login.defs` tem **uma única** linha `PASS_MAX_DAYS`, com o valor `90`.
6. **Desligamento:** o usuário `marcos` **e o diretório pessoal dele** não existem mais.
7. O playbook é **idempotente**: a segunda execução termina com `changed=0`.

## Critérios de aceite

- [ ] `site.yml` existe.
- [ ] `site.yml` passa na checagem de sintaxe.
- [ ] A regra de sudo é gravada com `validate` (visudo).
- [ ] O playbook executa sem erros nos 4 nós (o verificador recria o usuário `marcos` antes de rodá-lo).
- [ ] A segunda rodada termina com `changed=0`.
- [ ] Banner em `/etc/motd`: texto, dono e modo, nos 4 nós.
- [ ] Diretório `/opt/infra`: dono, grupo e modo, nos 4 nós.
- [ ] Diretório `/opt/infra/scripts`: dono, grupo e modo, nos 4 nós.
- [ ] Diretório `/opt/infra/relatorios`: dono, grupo e modo, nos 4 nós.
- [ ] O grupo `adm-infra` existe nos 4 nós.
- [ ] `ana`, `bruno` e `carla` existem, com shell `/bin/bash`, home e membros de `adm-infra`, nos 4 nós.
- [ ] Regra de sudo: arquivo, dono, modo, sintaxe válida e efeito real, nos 4 nós.
- [ ] `PASS_MAX_DAYS` vale 90 em `/etc/login.defs`, em uma única linha, nos 4 nós.
- [ ] O usuário `marcos` e o diretório dele não existem mais, nos 4 nós.

## Antes de começar

1. No terminal do seu computador: `lab start 03` (ele cria o usuário `marcos` nos nós).
2. Preencha o **`DESENHO.md`** desta pasta **antes** de escrever qualquer YAML.
3. No nó de controle (`lab shell`): `cd /lab/03-arquivos-usuarios`.

## Como verificar

```bash
lab verify 03
```

Antes, para a sua conferência: `ansible-playbook site.yml --check --diff` mostra o que mudaria, e a segunda execução do playbook deve mostrar `changed=0`.

## Dicas

<details>
<summary>Dica 1 — conceitual</summary>

Antes de escrever, faça a lista de dependências: **o que precisa existir antes do quê?** Um diretório com grupo `adm-infra` precisa do grupo; o usuário também. E pergunte-se: o que significa, para cada item, "já está como eu quero"? É isso que o módulo compara.

Sobre o `marcos`: remover a conta e remover o que ela deixou para trás são **dois** comportamentos. Qual deles a missão pede?

</details>

<details>
<summary>Dica 2 — mais direta</summary>

- **Modos** são texto: cuidado com como o YAML interpreta números que começam com zero.
- **Sudoers:** qual comando valida um arquivo `sudoers` antes de ele valer? Procure no `ansible-doc ansible.builtin.copy` o parâmetro que executa uma validação sobre o arquivo temporário.
- **`login.defs`:** o arquivo já tem a linha com outro valor; você quer *trocar a linha*, não duplicá-la. Que módulo faz isso, e qual parâmetro identifica a linha a ser trocada?
- O mesmo playbook vale para Rocky e Debian: algum caminho usado aqui muda entre as famílias?

</details>

<details>
<summary>Dica 3 — o módulo e o parâmetro</summary>

- `ansible.builtin.copy`: `content`, `dest`, `owner`, `group`, `mode`, `validate`.
- `ansible.builtin.file`: `path`, `state: directory`, `owner`, `group`, `mode`.
- `ansible.builtin.group`: `name`, `state: present`.
- `ansible.builtin.user`: `name`, `shell`, `groups`, `append`, `state: absent`, `remove`.
- `ansible.builtin.lineinfile`: `path`, `regexp`, `line`.
- Validação do sudoers: `validate: /usr/sbin/visudo -cf %s`. Regra: `%grupo ALL=(ALL) NOPASSWD: ALL`.

</details>

## Perguntas de reflexão

1. A lista de administradores tem 3 nomes aqui. E se fossem **30**, mudando todo mês? Onde essa lista deveria morar: dentro das tasks ou em outro lugar? Como a task a consumiria?
2. Por que o `validate` no `sudoers` é tão importante? O que aconteceria sem ele, em 400 servidores, se houvesse um erro de digitação?
3. Alguém edita `/etc/motd` à mão em um nó. O que acontece na próxima execução do playbook? Isso é bom ou ruim?

## Extensão opcional

**Chave SSH autorizada.** O arquivo `dados/ana.pub` traz a chave pública (fictícia) da analista `ana`. Estenda o `site.yml` para que, em todos os nós, essa chave esteja **autorizada** para `ana` (`~ana/.ssh/authorized_keys`, com o diretório `.ssh` em `0700` e o arquivo em `0600`, ambos de `ana`). O módulo que faz isso **não está** no `ansible.builtin`: descubra em qual collection ele vive (o nó de controle já tem `ansible.posix` e `community.general`). Ao rodar `lab verify 03`, uma seção extra confere o resultado (ela não conta para a missão).

## Para saber mais

```bash
ansible-doc ansible.builtin.copy
ansible-doc ansible.builtin.file
ansible-doc ansible.builtin.user
ansible-doc ansible.builtin.group
ansible-doc ansible.builtin.lineinfile
ansible-galaxy collection list         # collections instaladas no nó de controle
```

- [Módulo copy](https://docs.ansible.com/ansible/latest/collections/ansible/builtin/copy_module.html)
- [Módulo user](https://docs.ansible.com/ansible/latest/collections/ansible/builtin/user_module.html)
- [Sobre o `sudoers.d` e o `visudo`](https://www.sudo.ws/docs/man/sudoers.man/)
