# Desafio 02 — Primeiro playbook idempotente

| | |
|---|---|
| **Dia do curso** | Dia 1 — Fundamentos (23/11) |
| **Missão essencial** | ~15 minutos |
| **Conceitos** | play, task, módulo, FQCN, `state`, `become`, idempotência, saída `ok`/`changed` |
| **Pasta de trabalho** | `/lab/02-primeiro-playbook` (no nó de controle) |

---

## Teoria

### Playbook, play e task

Um **playbook** é um arquivo YAML com uma lista de **plays**. Um play responde: *em quais hosts* (`hosts:`), *com quais privilégios* (`become:`) e *executando quais tasks*. Uma **task** é a chamada de **um módulo** com seus argumentos, sempre acompanhada de um `name` que descreva a **intenção** ("Garantir o diretório de backup"), não o comando.

### Módulos descrevem estado

Um módulo do Ansible é **declarativo**: você diz como o alvo deve **ficar**, não quais comandos digitar. O parâmetro `state` expressa esse estado, e **cada módulo define os valores que aceita** (por exemplo, `directory` e `absent` no módulo `file`). Descobrir quais são é o trabalho do `ansible-doc`.

Use sempre o nome completo do módulo, o **FQCN** (*Fully Qualified Collection Name*): `ansible.builtin.file`, não `file`. Isso evita ambiguidade quando collections diferentes têm módulos com o mesmo nome, e é o padrão deste curso.

### Privilégios com `become`

Instalar pacotes, mexer em serviços e escrever em `/etc` exigem administrador. O Ansible entra como um usuário comum e, onde você declara `become: true`, eleva os privilégios (aqui, por `sudo`). Pode ser no play inteiro ou em uma task.

### Idempotência

Uma automação é **idempotente** quando executá-la uma vez ou dez vezes leva ao **mesmo** resultado, sem efeitos colaterais na repetição. É isso que permite rodar o mesmo playbook toda noite, em 400 servidores, sem medo. O recap do Ansible mostra a prova:

```text
PLAY RECAP *********************************************
bd1 : ok=2  changed=1  unreachable=0  failed=0     <- 1ª execução: algo mudou
bd1 : ok=2  changed=0  unreachable=0  failed=0     <- 2ª execução: nada a fazer
```

Exemplo, em um caso **diferente** do desta missão — garantir uma área de backup:

```yaml
---
- name: Preparar a área de backup
  hosts: bd
  become: true
  tasks:
    - name: Garantir o diretório de backup da aplicação
      ansible.builtin.file:
        path: /var/backups/aplicacao
        state: directory
        owner: root
        mode: "0750"
```

Compare com a versão frágil, que descreve um **comando** em vez de um estado:

```yaml
    - name: Criar o diretório de backup (jeito frágil)
      ansible.builtin.command: mkdir /var/backups/aplicacao
```

Na primeira execução, funciona. Na segunda, **falha** (o diretório já existe). Se você a "consertar" para não falhar, ela passa a reportar `changed` **sempre**, e o recap deixa de dizer a verdade.

### O que acontece por baixo

O módulo `file` roda no alvo e **primeiro olha o estado atual**: o diretório existe? Dono e modo estão certos? Se já está como pedido, devolve `changed: false` e não mexe em nada. Só se algo diverge ele age e devolve `changed: true`. A lógica de "já está assim?" vive **dentro do módulo** — com `command` e `shell` ela não existe, e é você quem teria de escrevê-la.

Para ver o que um playbook faria sem alterar nada: `ansible-playbook site.yml --check --diff`.

---

## Cenário

Os dois servidores web do ambiente de homologação do **Órgão Exemplo** (`web1` e `web2`) precisam de uma base mínima de administração antes de receber a aplicação: um **agendador de tarefas** ativo (a rotina de limpeza noturna depende dele) e algumas ferramentas de apoio ao suporte. O banco (`db1`) e o balanceador (`lb1`) **não** fazem parte desta mudança.

O inventário já está pronto na pasta `inventario/`: aqui o assunto é o playbook.

## Missão essencial

Escreva o playbook **`site.yml`** (nesta pasta) de modo que, ao final, nos nós do grupo `web`:

- os pacotes **`cronie`**, **`rsync`**, **`tree`** e **`lsof`** estejam instalados;
- o serviço **`crond`** esteja **ativo** agora e **habilitado** para iniciar no boot;
- os nós **fora** do grupo `web` (`db1` e `lb1`) permaneçam intocados;
- a **segunda execução** do playbook termine com `changed=0`.

O playbook deve seguir o padrão do curso: toda task com `name`, todo módulo com FQCN.

## Critérios de aceite

- [ ] `site.yml` existe.
- [ ] `site.yml` passa na checagem de sintaxe.
- [ ] Todas as tasks têm `name`.
- [ ] Todos os módulos usam o nome completo (FQCN).
- [ ] Nenhuma task usa `command`/`shell` para instalar pacote ou controlar serviço.
- [ ] O playbook executa sem erros **a partir dos nós limpos** (o verificador desinstala os pacotes e para o serviço antes de rodá-lo).
- [ ] A segunda rodada termina com `changed=0`.
- [ ] Os quatro pacotes estão instalados em `web1` e `web2`.
- [ ] O serviço `crond` está ativo em `web1` e `web2`.
- [ ] O serviço `crond` está habilitado na inicialização em `web1` e `web2`.
- [ ] `db1` e `lb1` não foram alterados.

## Antes de começar

1. No terminal do seu computador: `lab start 02`.
2. Preencha o **`DESENHO.md`** desta pasta **antes** de escrever qualquer YAML.
3. No nó de controle (`lab shell`): `cd /lab/02-primeiro-playbook`.

## Como verificar

```bash
lab verify 02
```

Para a sua própria conferência, antes de pedir a verificação:

```bash
ansible-playbook site.yml --syntax-check
ansible-playbook site.yml --check --diff
ansible-playbook site.yml
ansible-playbook site.yml        # de novo: o que o recap mostra?
```

## Dicas

<details>
<summary>Dica 1 — conceitual</summary>

Há **dois assuntos** na missão: *o que deve estar instalado* e *o que deve estar rodando*. Cada um é cuidado por um módulo diferente. E "ativo" e "habilitado" **não são a mesma coisa**: um é sobre agora, o outro é sobre o próximo boot.

Como você descobre qual módulo gerencia pacotes na família Red Hat? E como descobre quais valores de `state` ele aceita?

</details>

<details>
<summary>Dica 2 — mais direta</summary>

Pacotes: módulo do gerenciador de pacotes do Rocky. Serviços: módulo que conversa com o systemd. Ambos precisam de privilégio de administrador: onde isso se declara?

Se a segunda rodada mostrar `changed`, olhe qual task foi marcada e pergunte: ela descreve um **estado** ou executa um **comando**? Rode com `--check --diff` para ver o que o Ansible acha que mudaria.

</details>

<details>
<summary>Dica 3 — o módulo e o parâmetro</summary>

- Pacotes: `ansible.builtin.dnf`, com `name` (aceita uma **lista**) e `state: present`.
- Serviço: `ansible.builtin.service`, com `name`, `state: started` e `enabled: true`.
- Privilégio: `become: true`, no play.
- `ansible-doc ansible.builtin.dnf` e `ansible-doc ansible.builtin.service` mostram todos os parâmetros e valores de `state`.

</details>

## Perguntas de reflexão

1. Se amanhã o `db1` (Debian) entrasse neste play, **o que precisaria mudar**? O que no seu playbook é específico de uma família de sistemas?
2. Um colega escreveu `command: dnf install -y cronie` "porque funciona". Que problemas isso causa quando o playbook roda toda noite em 400 servidores?
3. Como você provaria o que o playbook vai fazer **sem executá-lo**? E como provaria, depois, que ele fez?

## Extensão opcional

**Agendamento com cron.** Com o `crond` ativo, estenda o `site.yml` para que `web1` e `web2` tenham, no `crontab` do usuário `root`, uma entrada chamada **`limpeza-tmp`**, executada **todo dia às 02:30**, com o comando:

```text
find /var/tmp -type f -mtime +7 -delete
```

Ela precisa ser idempotente: a segunda rodada continua com `changed=0`. Ao rodar `lab verify 02`, uma seção extra confere a entrada (ela não conta para o resultado da missão).

## Para saber mais

```bash
ansible-doc ansible.builtin.dnf
ansible-doc ansible.builtin.service
ansible-doc ansible.builtin.cron
ansible-doc -t keyword -l | head       # palavras-chave de play e task (become, hosts...)
```

- [Introdução aos playbooks](https://docs.ansible.com/ansible/latest/playbook_guide/playbooks_intro.html)
- [Elevação de privilégios (become)](https://docs.ansible.com/ansible/latest/playbook_guide/playbooks_privilege_escalation.html)
- [Módulos e collections: o que é um FQCN](https://docs.ansible.com/ansible/latest/collections_guide/index.html)
