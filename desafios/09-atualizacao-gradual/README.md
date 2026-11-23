# Desafio 09 — Atualização gradual

| | |
|---|---|
| **Dia do curso** | Dia 3 — Reuso, segredos e orquestração (25/11) |
| **Missão essencial** | ~40 minutos |
| **Conceitos** | `serial`, `delegate_to`, `max_fail_percentage`, verificação de saúde, `run_once`, módulo `community.general.haproxy` |
| **Pasta de trabalho** | `/lab/09-atualizacao-gradual` (no nó de controle) |

---

## Teoria

### O padrão que o Ansible usa por omissão

Um play roda cada task em **todos os hosts** do `hosts:` antes de passar para a task seguinte. Para configurar 40 servidores isso é ótimo. Para **atualizar** os mesmos 40 atrás de um balanceador é um desastre: a task "reiniciar a aplicação" derruba todos ao mesmo tempo, e o serviço fica fora do ar.

### Atualização em lotes: `serial`

A palavra-chave `serial` (no play) divide os hosts em **lotes**, e o play inteiro (todas as suas tasks) roda em um lote antes de começar o próximo. Em outro cenário:

```yaml
- name: Atualizar o servidor de relatórios
  hosts: relatorios
  serial: 2          # também aceita porcentagem ("25%") ou uma lista ([1, 5, 10])
```

Com `serial: 2`, só dois servidores estão em manutenção a cada momento. Os demais continuam atendendo.

### Falhar cedo: `max_fail_percentage`

E se a nova versão estiver com defeito? Sem proteção, o Ansible continuaria lote após lote, e você teria quebrado todos os servidores um de cada vez. Quando **todos** os hosts de um lote falham, o play é **interrompido** para os lotes seguintes (com `serial: 1`, uma falha já é o lote inteiro). A palavra-chave `max_fail_percentage` ajusta o limite: se a porcentagem de falhas do lote passar dele, o play para, e com `0` qualquer falha basta. O que interessa é a ideia: **a atualização precisa parar assim que a evidência de problema aparece**, e a evidência vem de uma **verificação de saúde** feita antes de devolver o nó ao serviço.

### Mexer em outro host: `delegate_to`

Tirar um servidor do balanceador não é uma ação *no servidor*: é uma ação *no balanceador*. `delegate_to` executa a task em outro host, mantendo as variáveis do host original (`inventory_hostname` continua sendo o servidor em atualização). Também existe o `run_once`, que executa a task uma só vez para o play (ou lote), útil para ações que não são por servidor.

```yaml
- name: Avisar o monitoramento
  ansible.builtin.uri:
    url: "http://monitor/manutencao/{{ inventory_hostname }}"
  delegate_to: monitor      # roda em "monitor", mas fala do host da vez
```

### Tirar do balanceador sem derrubar ninguém

O HAProxy tem um **socket de administração** que permite habilitar, desabilitar ou colocar um servidor em modo *drain*, sem recarregar a configuração. Desabilitar um servidor faz o balanceador **parar de enviar requisições novas** para ele (as que já estão em andamento terminam). O módulo `community.general.haproxy` fala com esse socket; veja `ansible-doc community.general.haproxy`. A opção `wait` espera o balanceador confirmar o estado, em vez de seguir adiante "na esperança".

### A ordem dos passos importa

Para cada nó: **tirar da rotação, esperar, atualizar, validar, devolver, esperar**. Inverter ou pular um passo costuma funcionar nos dias bons e falhar no dia ruim.

---

## Cenário

O **Portal de Avisos** do **Órgão Exemplo** roda na versão **1** em dois servidores, `web1` e `web2`, atrás de um balanceador HAProxy em `lb1`. Chegou a versão **2**, e a regra da área é: **o usuário não pode perceber a atualização.**

A equipe recebeu pronta a role **`atualizar_app`** (em `roles/atualizar_app/`), que troca a versão **em um nó**. Ela **não conhece o balanceador** e, de propósito, **deixa o nó fora do ar por alguns segundos** durante a troca. Quem a chamar precisa cuidar do resto. Leia o `README.md` da role.

Dados do ambiente:

- O serviço está em `http://lb1/` (no seu computador: `http://localhost:8080`). Cada página mostra a versão e o nome do servidor que respondeu.
- No HAProxy, o *backend* se chama **`web`**, e os servidores se chamam **`web1`** e **`web2`**, como no inventário.
- O socket de administração do HAProxy está em **`/var/lib/haproxy/admin.sock`**, em `lb1`.

## Missão essencial

Escreva o playbook **`atualizar.yml`** (nesta pasta) que leve `web1` e `web2` à **versão 2** sem interromper o serviço:

1. Use a role **`atualizar_app`** fornecida para trocar a versão (ela publica a versão 2 por padrão).
2. Atualize **um nó de cada vez**, e para cada nó: tire-o do balanceador, atualize, devolva-o ao balanceador.
3. O balanceador deve confirmar cada mudança de estado antes de o playbook seguir.
4. O serviço deve **responder sem nenhuma falha durante toda a execução**: o verificador dispara requisições contínuas ao balanceador enquanto roda o seu playbook, e nenhuma pode falhar.
5. Ao final, os dois nós estão na versão 2 e **de volta à rotação**.
6. Toda task com `name` e todo módulo com FQCN.

Este desafio **não** mede idempotência: a role fornecida reinicia o nginx de propósito, e cada execução repete a troca.

## Critérios de aceite

- [ ] `atualizar.yml` existe.
- [ ] `atualizar.yml` passa na checagem de sintaxe.
- [ ] Todas as tasks têm `name`.
- [ ] Todos os módulos usam o nome completo (FQCN).
- [ ] O playbook usa a role `atualizar_app` fornecida.
- [ ] O play usa `serial`.
- [ ] Alguma task usa `delegate_to` (o balanceador é outro host).
- [ ] O playbook executa sem erros.
- [ ] O serviço responde 200 em todas as requisições durante a execução.
- [ ] `web1` e `web2` respondem a versão 2 diretamente.
- [ ] O balanceador entrega a versão 2 pelos dois servidores.
- [ ] Os dois servidores terminam em rotação (UP) no balanceador.

## Antes de começar

1. No terminal do seu computador: `lab start 09` (ele põe a versão 1 no ar atrás do balanceador).
2. Preencha o **`DESENHO.md`** desta pasta **antes** de mexer em qualquer arquivo.
3. No nó de controle (`lab shell`): `cd /lab/09-atualizacao-gradual`.
4. Para **ver** o efeito, deixe um segundo terminal rodando `watch -n 0.5 curl -s http://lb1/` durante as suas execuções (ou abra `http://localhost:8080` no navegador e atualize a página).

## Como verificar

```bash
lab verify 09
```

O verificador leva cerca de **1,5 minuto** (ele põe a versão 1 no ar, executa o seu playbook sob carga, e depois confere os nós). Para a sua conferência antes: `ansible-playbook atualizar.yml --syntax-check`, `ansible-playbook atualizar.yml --list-tasks` e uma execução com o `watch` aberto.

## Dicas

<details>
<summary>Dica 1 — conceitual</summary>

Pense no que acontece **em cada instante**: em qualquer momento da execução, quantos nós precisam estar atendendo para o usuário não perceber? E o balanceador: ele sabe, sozinho e na hora, que um nó vai parar? Se ele não for avisado, para quem ele continua mandando requisições?

Desenhe a linha do tempo de **um** nó (do primeiro ao último passo) no `DESENHO.md`. Depois responda: se o play rodar em **todos** os nós ao mesmo tempo, o que acontece com essa linha do tempo?

</details>

<details>
<summary>Dica 2 — mais direta</summary>

- O play precisa executar em **lotes** de nós, e não em todos de uma vez. Existe uma palavra-chave de play para isso.
- Avisar o balanceador é uma ação **no balanceador**, mas sobre o servidor da vez. O Ansible tem uma palavra-chave que muda o host onde a task é executada sem perder as variáveis do host original.
- A role fornecida pode ser chamada como role do play ou dentro de uma task. Pense em qual das duas formas permite colocar tasks **antes e depois** dela, para cada nó.
- Tirar o servidor do balanceador e devolvê-lo são **duas** tasks. A ordem entre elas e a role é a lógica do desafio.
- Se o balanceador ainda não confirmou a mudança, a task seguinte pode começar cedo demais. O módulo tem um parâmetro para esperar a confirmação.

</details>

<details>
<summary>Dica 3 — o módulo e o parâmetro</summary>

- `serial:` no play (`ansible-doc -t keyword serial`).
- `delegate_to:` na task (`ansible-doc -t keyword delegate_to`).
- `community.general.haproxy` (`ansible-doc community.general.haproxy`): parâmetros `socket`, `backend`, `host`, `state` (`disabled` para tirar, `enabled` para devolver) e `wait` (com `wait_interval` e `wait_retries` para ajustar o tempo de espera).
- A role: `roles:` no play, ou `ansible.builtin.include_role` / `ansible.builtin.import_role` dentro de `tasks:`.
- Em uma task delegada, `inventory_hostname` continua sendo o servidor da vez.

</details>

## Perguntas de reflexão

1. Com `serial: 1`, quanto tempo a atualização leva para 2 servidores? E para 200? Em que situação `serial` em **porcentagem** ou em **lista** (`[1, 5, 10]`) é uma escolha melhor?
2. A role fornecida **não** conhece o balanceador. Por que é bom que ela não conheça? O que mudaria se ela mesma tirasse e devolvesse o nó?
3. Se a versão 2 estivesse com defeito, o que o seu playbook faria hoje? Quantos nós já estariam quebrados quando você descobrisse?

## Extensão opcional

**Release com defeito.** Rode o seu playbook com `-e atualizar_app_versao=3 -e atualizar_app_saudavel=false`: a role publica uma versão cuja verificação de saúde (`http://<nó>/saude`) responde **503**. Faça o playbook **parar no primeiro nó** que ficar doente: o nó com defeito **não** volta ao balanceador, o outro nó **não é tocado** e segue atendendo na versão 2, e **mesmo assim** o serviço não é interrompido. A seção extra do `lab verify 09` roda esse teste (ela não conta para o resultado da missão) e depois devolve o ambiente à versão 1.

## Para saber mais

```bash
ansible-doc community.general.haproxy
ansible-doc -t keyword serial
ansible-doc -t keyword max_fail_percentage
ansible-doc -t keyword delegate_to
```

- [Controlando a execução com `serial`](https://docs.ansible.com/ansible/latest/playbook_guide/playbooks_strategies.html#setting-the-batch-size-with-serial)
- [Delegação (`delegate_to`) e `run_once`](https://docs.ansible.com/ansible/latest/playbook_guide/playbooks_delegation.html)
- [Tratamento de erros e `max_fail_percentage`](https://docs.ansible.com/ansible/latest/playbook_guide/playbooks_error_handling.html)
