# DESENHO — Desafio 08: Segredos com Ansible Vault

> **Preencha este arquivo ANTES de escrever qualquer YAML.** Ninguém corrige as suas respostas (o `lab verify` só avisa se ele continuar em branco):
> serve para você pensar. Pode rascunhar no papel e resumir aqui. Respostas curtas e objetivas bastam.
> O método completo, com um exemplo resolvido, está em `docs/metodo.md`.

## 1. Estado desejado

> O que precisa ser verdade ao final? Como você vai provar que está verdade?
> - O que precisa ser verdade nos nós web ao final? E o que precisa ser verdade (e falso!) na pasta do projeto e na saída do Ansible?

**Sua resposta:**

Nos nós web: a conta `appportal` existe, com a senha do cofre de segredos gravada como hash sha512, e a segunda rodada dá `changed=0`. No projeto: nenhum arquivo contém a senha em claro, o cofre está cifrado e a saída com `-v`/`-vvv` não a mostra.

## 2. Inventário

> Quem são os alvos e como estão agrupados?
> - Em quais hosts a conta deve existir? E em quais ela não pode aparecer?

**Sua resposta:**

A conta pertence só ao grupo `web` (web1, web2); `db1` e `lb1` não recebem nada.

## 3. Variáveis

> O que muda entre hosts ou ambientes? Em qual camada cada valor mora?
> - Quais valores são secretos e quais não são? Qual nome cada um terá no arquivo visível e no cofre? Em qual camada (`group_vars/web/`, `host_vars/`, play) cada arquivo mora?

**Sua resposta:**

Secreta: a senha da conta. Não secreta: o nome da conta. No cofre (`group_vars/web/vault.yml`, cifrado): `vault_appportal_senha`. No arquivo visível (`group_vars/web/vars.yml`): `appportal_senha: "{{ vault_appportal_senha }}"`. Assim `grep appportal_senha` acha o nome sem abrir o cofre. Extensão: `portal_token` cifrado inline com `encrypt_string`.

## 4. Estrutura

> Quais plays, tasks ou roles, e em que ordem?
> - Que arquivos você vai criar, com que comando, e que tasks entram em `site.yml`? Como o `site.yml` vai obter o valor do segredo sem que ele apareça no projeto?

**Sua resposta:**

Criar o cofre com `ansible-vault create` (ou `encrypt`), o `vars.yml` em claro, e um play em `web` com `become` e uma task `ansible.builtin.user` com `password` vinda de `password_hash('sha512', <salt fixo>)` e `no_log: true`. A senha chega ao cofre digitada no editor do `ansible-vault create`, lida do arquivo fora do projeto.

## 5. Risco

> O que pode falhar? Como validar antes de aplicar? Como voltar atrás?
> - Por onde o segredo pode vazar (arquivo, `-v`, `debug`, histórico do shell, Git)? O que acontece com a idempotência da task que define a senha? Como você valida antes de aplicar?

**Sua resposta:**

Vazamentos: arquivo em claro, `debug`, `-v` mostrando o resultado, histórico do shell (por isso `ansible-vault create` abre um editor em vez de receber o valor na linha de comando) e Git. `password_hash` sem salt fixo gera um hash novo a cada execução, e a task passa a dar `changed` sempre; por isso o salt fixo. Valido com `--syntax-check`, `ansible-vault view` e `--check --diff` (com `no_log`, a diferença não aparece).
