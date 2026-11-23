# Desafio 05 — Templates e handlers

| | |
|---|---|
| **Dia do curso** | Dia 2 — Playbooks em profundidade (24/11) |
| **Missão essencial** | ~30 minutos |
| **Conceitos** | `template`, Jinja2 (variáveis, `for`, filtros), handlers, `notify`, `validate` |
| **Pasta de trabalho** | `/lab/05-templates-handlers` (no nó de controle) |

---

## Teoria

### Template: um arquivo com lacunas

Com `ansible.builtin.copy` você leva um arquivo **idêntico** para todos os nós. Mas configuração raramente é idêntica: o endereço muda, a porta muda, o nome do servidor muda. O módulo `ansible.builtin.template` resolve isso: ele lê um arquivo **Jinja2** (por convenção, terminado em `.j2`, na pasta `templates/`), substitui as lacunas pelas variáveis **daquele host** e grava o resultado no nó. Cada nó recebe a sua versão.

Um exemplo em outro cenário, um fragmento de configuração do `rsyslog` para enviar logs a um servidor central:

```jinja
# {{ ansible_managed }}
*.* @@{{ servidor_logs }}:{{ porta_logs | default(514) }}
```

e a task correspondente:

```yaml
- name: Enviar os logs ao servidor central
  ansible.builtin.template:
    src: remoto.conf.j2
    dest: /etc/rsyslog.d/50-remoto.conf
    owner: root
    group: root
    mode: "0644"
  notify: Reiniciar o rsyslog
```

### Um pouco de Jinja2

- `{{ variavel }}` imprime um valor. Filtros se encadeiam com `|`: `{{ nome | upper }}`, `{{ porta | default(80) }}`.
- `{% for h in groups['app'] %} ... {% endfor %}` repete um trecho. Exemplo: gerar uma linha por servidor do grupo `app`:

  ```jinja
  {% for h in groups['app'] %}
  {{ h }} {{ hostvars[h]['ansible_host'] | default(h) }}
  {% endfor %}
  ```

- `{% if ... %}` decide se um trecho entra.
- O template é processado **no nó de controle**: o resultado vai pronto para o nó. O nó nem precisa saber o que é Jinja2.

### Handlers: reagir a mudanças

Se você recarrega o serviço em **toda** execução, derruba conexões à toa. Se **nunca** recarrega, a configuração nova não vale. O **handler** resolve: é uma task que só roda **quando outra task, que a notificou (`notify`), reportou `changed`**.

```yaml
tasks:
  - name: Enviar os logs ao servidor central
    ansible.builtin.template: { ... }
    notify: Reiniciar o rsyslog        # só dispara se esta task mudou o arquivo

handlers:
  - name: Reiniciar o rsyslog
    ansible.builtin.service:
      name: rsyslog
      state: restarted
```

Três regras que pegam todo mundo:

1. O nome do `notify` precisa ser **idêntico** ao nome do handler. Se divergir por uma letra, o Ansible só reclama (com erro) **no momento em que a task muda algo**; nas execuções em que nada muda, o defeito passa despercebido.
2. Handlers rodam **uma vez, no fim do play** (não no meio), por maior que seja o número de tasks que os notificaram. Se precisar antes, use `ansible.builtin.meta: flush_handlers`.
3. Se uma task falhar, handlers pendentes **não** rodam (a menos que `--force-handlers`).

### O que acontece por baixo

O `template` calcula o conteúdo final, compara com o arquivo do nó (por checksum) e só grava se for diferente. É por isso que ele é **idempotente**: na segunda rodada, nada difere, nada muda, ninguém notifica o handler. E o parâmetro `validate` roda um comando de checagem (por exemplo, `nginx -t`) no arquivo **temporário** antes de ele substituir o definitivo.

---

## Cenário

A página institucional de **homologação** do **Órgão Exemplo** vai ser servida por **nginx** em `web1` e `web2`. Cada servidor deve mostrar uma página que diga **qual servidor** a entregou e **em que ambiente** está, para que a equipe de suporte saiba, olhando o navegador, onde caiu a requisição. A porta de publicação vai variar entre ambientes, e a configuração do nginx não deve ser recarregada à toa.

O inventário já está pronto em `inventario/`.

## Missão essencial

Escreva o playbook **`site.yml`** (nesta pasta, `hosts: web`), com templates na pasta **`templates/`**, de modo que, em `web1` e `web2`:

1. O **nginx** esteja instalado, **ativo** e **habilitado** na inicialização.
2. A **configuração do nginx** seja gerada por **template** e escute na porta dada pela variável **`site_porta`**, cujo valor **padrão é `8081`**. A configuração passa na validação do próprio nginx (`nginx -t`).
3. Uma **página inicial** seja gerada por **template** e, ao ser acessada em `http://<servidor>:<site_porta>/`, mostre o **nome do host** e o **ambiente**, dado pela variável **`site_ambiente`**, cujo valor **padrão é `homologacao`**.
4. A **recarga** do nginx aconteça **por handler** (`state: reloaded`), notificado pelas tasks que alteram a configuração, e **somente quando algo mudou**:
   - numa segunda execução idêntica, o handler **não roda**;
   - se o playbook for executado com outro valor de porta, o handler **roda**.
5. O playbook é **idempotente**: a segunda execução termina com `changed=0`.
6. O playbook segue o padrão do curso: toda task com `name`, todo módulo com FQCN.

## Critérios de aceite

- [ ] `site.yml` existe.
- [ ] `site.yml` passa na checagem de sintaxe.
- [ ] Todas as tasks têm `name`.
- [ ] Todos os módulos usam o nome completo (FQCN).
- [ ] O playbook usa o módulo `template` em pelo menos duas tasks, e há arquivos `.j2` em `templates/`.
- [ ] Existe ao menos um handler que recarrega (`state: reloaded`) um serviço, e ao menos uma task o notifica.
- [ ] O playbook executa sem erros em `web1` e `web2` a partir dos nós sem nginx (o verificador remove o nginx antes de rodá-lo).
- [ ] Segunda rodada com `changed=0`.
- [ ] Na segunda rodada, nenhum handler é executado.
- [ ] Executado com `-e site_porta=8082 -e site_ambiente=producao`, o playbook termina sem erros.
- [ ] Nessa execução, o handler roda em `web1` e `web2`.
- [ ] O nginx está ativo e habilitado, e `nginx -t` aprova a configuração, em `web1` e `web2`.
- [ ] A página responde na porta padrão (8081) e mostra o nome do host e `homologacao`.
- [ ] Com `-e site_porta=8082 -e site_ambiente=producao`, a página passa a responder na porta 8082 e mostra `producao`.
- [ ] A porta 8081 deixa de responder.

## Antes de começar

1. No terminal do seu computador: `lab start 05`.
2. Preencha o **`DESENHO.md`** desta pasta **antes** de escrever qualquer YAML.
3. No nó de controle (`lab shell`): `cd /lab/05-templates-handlers`.

## Como verificar

```bash
lab verify 05
```

Para a sua própria conferência: rode o playbook duas vezes e leia o recap; depois rode com `-e site_porta=8082` e observe se a linha `RUNNING HANDLER` aparece. Em um nó, `curl http://localhost:8081/` mostra a página.

## Dicas

<details>
<summary>Dica 1 — conceitual</summary>

Quais são as **coisas que mudam** de nó para nó ou de ambiente para ambiente? Elas são as variáveis. O que **não** muda é a estrutura do arquivo: essa é o template.

Para o handler, pense em **qual evento** exige recarregar o nginx: instalar o pacote? Mudar o arquivo de configuração? Mudar a página? Só um deles muda o que o processo em memória precisa reler.

</details>

<details>
<summary>Dica 2 — mais direta</summary>

- Cada template vira uma task com `template`, e cada uma tem `src` (na pasta `templates/`), `dest`, dono e modo.
- A configuração do nginx para um servidor extra normalmente fica em um arquivo próprio dentro do diretório de configurações adicionais do pacote. Veja o `nginx.conf` instalado para saber onde ele os procura.
- Se `notify` e nome do handler divergirem por uma letra, o erro só aparece quando a task realmente muda algo. Teste também a execução que **altera** a configuração, não só a repetida.
- A página pode ser servida pelo diretório padrão do pacote ou por um diretório seu: se for o seu, quem o cria?
- A porta e o ambiente têm um valor **padrão**. Onde um valor padrão deve morar para que `-e` consiga sobrepô-lo sem erro?

</details>

<details>
<summary>Dica 3 — o módulo e o parâmetro</summary>

- `ansible.builtin.dnf`: `name: nginx`, `state: present`.
- `ansible.builtin.template`: `src`, `dest`, `owner`, `group`, `mode`, `validate`, `notify`.
- Validação do nginx: `validate: nginx -t -c %s` (para um arquivo de configuração completo).
- `ansible.builtin.service`: `name`, `state` (`started`, `reloaded`), `enabled`.
- Handlers: seção `handlers:` do play; o `name` do handler é o texto do `notify`.
- Variável do nome do host: `inventory_hostname`.
- `ansible-doc ansible.builtin.template` explica `validate` e `%s`.

</details>

## Perguntas de reflexão

1. Mudar o **texto da página** exige recarregar o nginx? E mudar a **porta**? Que tasks devem notificar o handler, e por quê?
2. O `validate` com `nginx -t` impede que uma configuração inválida chegue ao servidor. O que aconteceria, em 400 servidores, **sem** ele e com um handler de `reloaded`? E com um de `restarted`?
3. Um colega edita a configuração do nginx diretamente em `web1`. O que acontece na próxima execução do playbook? O handler roda? Isso é desejável?

## Extensão opcional

**Uma página que conhece o grupo.** Faça a página mostrar também a **lista de todos os servidores do grupo `web`** (use um laço `for` do Jinja2 sobre `groups['web']`), de modo que `web1` e `web2` listem os dois nomes. Ao rodar `lab verify 05`, uma seção extra confere se cada página cita os dois (ela não conta para o resultado da missão).

## Para saber mais

```bash
ansible-doc ansible.builtin.template
ansible-doc ansible.builtin.service
ansible-doc -t keyword -l | grep -i notify
```

- [Templating (Jinja2)](https://docs.ansible.com/ansible/latest/playbook_guide/playbooks_templating.html)
- [Handlers: executando operações em mudança](https://docs.ansible.com/ansible/latest/playbook_guide/playbooks_handlers.html)
- [Filtros do Jinja2 no Ansible](https://docs.ansible.com/ansible/latest/playbook_guide/playbooks_filters.html)
