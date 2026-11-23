# Desafio 08 — Segredos com Ansible Vault

| | |
|---|---|
| **Dia do curso** | Dia 3 — Reuso, segredos e orquestração (25/11) |
| **Missão essencial** | ~30 minutos |
| **Conceitos** | `ansible-vault` (create, edit, view, encrypt_string), padrão `vars` × `vault`, `no_log`, filtro `password_hash`, vazamento por `-v` |
| **Pasta de trabalho** | `/lab/08-segredos-vault` (no nó de controle) |

---

## Teoria

### O problema

Senhas, tokens e chaves precisam chegar aos servidores, e o playbook é o caminho. Só que o playbook vive em um repositório Git que muita gente lê. Segredo em texto claro ali é segredo publicado: fica no histórico para sempre, mesmo depois de apagado.

### O Ansible Vault

O **Vault** cifra (AES256) arquivos inteiros ou valores isolados, e o Ansible os decifra **na hora de usar**, desde que receba a senha do Vault. Os comandos do dia a dia:

```bash
ansible-vault create group_vars/bancos/vault.yml   # abre o editor; ao salvar, o arquivo é cifrado
ansible-vault view   group_vars/bancos/vault.yml   # lê sem gravar em claro
ansible-vault edit   group_vars/bancos/vault.yml   # decifra, edita, cifra de novo
ansible-vault encrypt_string 'valor' --name 'api_chave'   # cifra um valor para colar em um YAML
```

A **senha do Vault** não pode morar no projeto. Em geral ela vem de um arquivo fora da pasta (`vault_password_file` no `ansible.cfg`), de uma pergunta (`--ask-vault-pass`) ou de um cofre corporativo. Neste laboratório o `ansible.cfg` já aponta para um arquivo no nó de controle, e o arquivo cifrado fica no Git sem risco.

### O padrão `vars` × `vault`

Um arquivo cifrado tem um custo: ninguém sabe o que há dentro sem abri-lo, e um `grep` não encontra nada. O padrão consagrado separa os dois papéis, em um exemplo de outro cenário:

```yaml
# group_vars/bancos/vars.yml   (em claro, nomes à vista)
banco_senha: "{{ vault_banco_senha }}"
# group_vars/bancos/vault.yml  (cifrado; só variáveis com prefixo vault_)
vault_banco_senha: "..."
```

O resto do projeto usa `banco_senha`, e o cofre guarda só os valores.

### Segredo vaza por outros caminhos

- **Saída do Ansible:** com `-v`, o resultado de cada task é impresso, e isso pode incluir o valor. `no_log: true` na task esconde o resultado (inclusive no `--diff`). Quem depura com `debug` imprime o segredo no terminal e no log do CI.
- **Histórico do shell:** `ansible-vault encrypt_string 'valor'` grava o valor no histórico. Prefira criar o arquivo pelo editor.
- **Hash que muda:** para definir a senha de um usuário Linux o módulo `ansible.builtin.user` espera um **hash**, e o filtro `password_hash` o calcula. Por padrão ele escolhe um *salt* aleatório, e então o hash muda a cada execução. O que isso faz com a idempotência? Veja `ansible-doc -t filter ansible.builtin.password_hash`.

---

## Cenário

A equipe de **portais** do **Órgão Exemplo** vai instalar o **Portal de Avisos**, que roda sob uma conta de serviço chamada **`appportal`** nos servidores web. A senha dessa conta é entregue pelo cofre de senhas da equipe de segurança, que neste laboratório é o arquivo **`/etc/lab/segredos/appportal-senha.txt`** (no nó de controle, **fora** da pasta do projeto). A equipe quer a conta criada por automação **sem** que a senha apareça no repositório, na tela ou no log.

## Missão essencial

Escreva o playbook **`site.yml`** (nesta pasta) de modo que:

1. Nos servidores do grupo `web`, exista a conta **`appportal`**, com a senha igual à do cofre de segredos, gravada como **hash sha512**.
2. A senha esteja no projeto **somente cifrada** pelo Vault, em um arquivo cifrado cujas variáveis tenham o prefixo **`vault_`**, e um arquivo em claro **aponte** para elas (padrão `vars` × `vault`).
3. **Nenhum arquivo do projeto** contenha a senha em claro, nem a senha do Vault.
4. A task que define a senha use **`no_log: true`**, e a saída do `ansible-playbook` com `-v` e com `-vvv` **não mostre** a senha.
5. O playbook seja **idempotente**: segunda execução com `changed=0`.
6. `db1` e `lb1` **não** recebam a conta.
7. Toda task com `name` e todo módulo com FQCN.

A senha do Vault já está configurada no `ansible.cfg` desta pasta; você não precisa mexer nele. O inventário também já está pronto.

## Critérios de aceite

- [ ] `site.yml` existe.
- [ ] `site.yml` passa na checagem de sintaxe.
- [ ] Todas as tasks têm `name`.
- [ ] Todos os módulos usam o nome completo (FQCN).
- [ ] Existe pelo menos um arquivo cifrado com o Vault no projeto.
- [ ] O arquivo cifrado abre com a senha do laboratório e só define variáveis com prefixo `vault_`.
- [ ] Um arquivo em claro expõe os nomes, com variáveis que apontam para as `vault_*` do cofre.
- [ ] Nenhum arquivo do projeto contém a senha em claro.
- [ ] A task que define a senha do usuário usa `no_log: true`.
- [ ] O playbook executa sem erros em `web1` e `web2` a partir dos nós sem a conta (o verificador remove a conta antes).
- [ ] Segunda rodada com `changed=0`.
- [ ] A saída com `-v` não mostra a senha.
- [ ] A saída com `-vvv` não mostra a senha.
- [ ] A conta `appportal` existe em `web1` e `web2`, com hash sha512 (`$6$`).
- [ ] O hash gravado corresponde à senha do cofre de segredos.
- [ ] `db1` e `lb1` não receberam a conta.

## Antes de começar

1. No terminal do seu computador: `lab start 08` (ele remove a conta `appportal` dos nós web).
2. Preencha o **`DESENHO.md`** desta pasta **antes** de mexer em qualquer arquivo.
3. No nó de controle (`lab shell`): `cd /lab/08-segredos-vault`.

## Como verificar

```bash
lab verify 08
```

Antes, para a sua conferência: `ansible-playbook site.yml --syntax-check`, `ansible-vault view` no seu cofre, `ansible-playbook site.yml` duas vezes (a segunda com `changed=0`), `ansible-playbook site.yml -vvv` olhando a saída com desconfiança, e `grep -r` procurando a senha pela pasta.

## Dicas

<details>
<summary>Dica 1 — conceitual</summary>

Separe o que é **nome** do que é **valor**. O valor secreto precisa estar cifrado; o nome pode (e deve) estar à vista. Qual arquivo guarda cada um, e como um aponta para o outro?

Depois, faça o caminho do segredo: de onde ele sai (o cofre de segredos da equipe), por onde passa até chegar ao nó, e em **cada** parada pergunte: "alguém consegue ler aqui?". Arquivo, tela, histórico do shell, log.

</details>

<details>
<summary>Dica 2 — mais direta</summary>

- Variáveis de grupo ficam em uma pasta com o nome do grupo (`group_vars/<grupo>/`), e **todos os arquivos** dessa pasta são lidos. Isso permite ter um arquivo em claro e um cifrado lado a lado.
- Para criar o cofre sem deixar a senha no histórico do shell, use o comando que abre o editor (`ansible-vault create`) e digite ou cole o valor lá dentro. Leia o arquivo do cofre de segredos com `cat` para copiar o valor.
- O módulo `ansible.builtin.user` **não** recebe a senha em texto: recebe o **hash**. Existe um filtro Jinja que calcula o hash a partir do texto.
- Rode o playbook duas vezes. Se a segunda disser `changed`, olhe o parâmetro do filtro que controla o *salt*.
- Rode com `-vvv` e leia a saída. O que aparece de cada task que mexe com a senha?

</details>

<details>
<summary>Dica 3 — o módulo e o parâmetro</summary>

- `ansible-vault create <arquivo>` (ou `encrypt` em um arquivo que já existe). Dentro, só variáveis `vault_...:` em YAML.
- `ansible.builtin.user`, parâmetro `password` (um **hash**, não o texto). O hash vem do filtro `password_hash('sha512', <salt>)`; o segundo argumento fixa o *salt* (até 16 caracteres entre letras, números, `.` e `/`).
- Palavra-chave `no_log: true` na task.
- `ansible-doc ansible.builtin.user`, `ansible-doc -t filter ansible.builtin.password_hash`, `ansible-doc -t keyword no_log`.

</details>

## Perguntas de reflexão

1. A senha do Vault está em um arquivo **fora** do projeto. Se o repositório for clonado em outra máquina, o que a pessoa precisa para rodar o playbook? Quem deve ter essa senha?
2. Por que o segredo em claro continua sendo um problema **mesmo** se você apagá-lo do arquivo no commit seguinte?
3. O que o `no_log: true` impede? Que outra situação ainda poderia expor a senha (um erro, o `-vvvv`, um `debug`)?

## Extensão opcional

**Token cifrado inline.** A aplicação precisa de um token, entregue em **`/etc/lab/segredos/portal-token.txt`**. Faça o playbook gravar nos nós web o arquivo **`/etc/appportal.env`** (dono `root`, modo `0600`) com a linha `PORTAL_TOKEN=<token>`, guardando o token no projeto como **valor cifrado inline** (`ansible-vault encrypt_string`, que produz um `!vault |` dentro de um YAML), sem que ele apareça em claro no projeto nem na saída com `-vvv`. A seção extra do `lab verify 08` roda se o seu `site.yml` mencionar `appportal.env` (ela não conta para o resultado da missão).

## Para saber mais

```bash
ansible-vault --help
ansible-doc -t filter ansible.builtin.password_hash
ansible-doc -t keyword no_log
```

- [Ansible Vault](https://docs.ansible.com/ansible/latest/vault_guide/index.html)
- [Protegendo a saída com no_log](https://docs.ansible.com/ansible/latest/playbook_guide/playbooks_error_handling.html#playbooks-keep-secret-data)
- [Precedência de variáveis](https://docs.ansible.com/ansible/latest/playbook_guide/playbooks_variables.html#understanding-variable-precedence)
