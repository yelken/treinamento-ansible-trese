# DESENHO — Desafio 04: Variáveis, facts e precedência

> **Preencha este arquivo ANTES de escrever qualquer YAML.** Ninguém corrige as suas respostas (o `lab verify` só avisa se ele continuar em branco):
> serve para você pensar. Pode rascunhar no papel e resumir aqui. Respostas curtas e objetivas bastam.
> O método completo, com um exemplo resolvido, está em `docs/metodo.md`.

## 1. Estado desejado

> O que precisa ser verdade ao final? Como você vai provar que está verdade?
> - O que deve existir em cada nó (pacote, arquivo) e com que conteúdo? Como você provaria, em `web1` e em `db1`, sem olhar o playbook?
> - O que a segunda execução deve mostrar no recap?

**Sua resposta:**

Em cada nó: o pacote de DNS instalado (`dig -v` responde) e `/etc/ficha-servidor` com as 5 linhas (+ `responsavel` na extensão). Prova: `ssh` no nó e `cat`. Segunda execução: `changed=0`.

## 2. Inventário

> Quem são os alvos e como estão agrupados?
> - Os quatro nós são do mesmo tipo? O que o Ansible sabe sobre cada um antes de rodar a primeira task?

**Sua resposta:**

Todos os 4 nós (grupo `homologacao`), `hosts: all`. Duas famílias: RedHat (web1, web2, lb1) e Debian (db1), descobertas pelo fact `os_family`.

## 3. Variáveis

> O que muda entre hosts ou ambientes? Em qual camada cada valor mora?
> - Liste cada valor que muda (nome do pacote, ambiente, retenção). Para cada um: vale para quem? Em qual arquivo ele deveria morar? Qual é a exceção e onde ela mora?
> - Para a Parte B: escreva aqui, em palavras, como você chegou às três previsões.

**Sua resposta:**

Mudam: nome do pacote (por família), ambiente (todos), retenção (30; 90 em db1). `group_vars/all` guarda retenção e o dicionário de pacotes; `group_vars/homologacao` guarda o ambiente; `host_vars/db1` guarda a exceção de 90.

## 4. Estrutura

> Quais plays, tasks ou roles, e em que ordem?
> - Quantas tasks? Existe `when`? Como o nome do pacote chega até a task?

**Sua resposta:**

Um play, `hosts: all`, `become: true`: instalar o pacote (nome via variável), criar o fato local, reler os fatos, gravar a ficha. O fato precisa existir antes de ser lido.

## 5. Risco

> O que pode falhar? Como validar antes de aplicar? Como voltar atrás?
> - Que erro surge se o fact não estiver disponível ou se a chave do dicionário não existir? Que comando mostra o valor final de uma variável sem rodar o playbook?

**Sua resposta:**

Pode falhar: chave de família ausente no dicionário (Ubuntu, por exemplo). Valido com `--check --diff` e `ansible-inventory --host db1`. Voltar atrás: remover o pacote e a ficha.
