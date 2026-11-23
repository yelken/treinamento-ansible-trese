# DESENHO — Desafio 06: Condicionais, loops e erros

> **Preencha este arquivo ANTES de escrever qualquer YAML.** Ninguém corrige as suas respostas (o `lab verify` só avisa se ele continuar em branco):
> serve para você pensar. Pode rascunhar no papel e resumir aqui. Respostas curtas e objetivas bastam.
> O método completo, com um exemplo resolvido, está em `docs/metodo.md`.

## 1. Estado desejado

> O que precisa ser verdade ao final? Como você vai provar que está verdade?
> - Parte A: para cada área ativa, o que deve existir? Para cada inativa? Como você prova, em um nó, sem olhar o playbook?
> - Parte B: o que é uma 'versão no ar'? Como você prova qual versão está no ar? Que arquivo precisa dizer o resultado da última publicação?

**Sua resposta:**

Áreas: cada ativa tem `/var/www/portal/areas/<nome>/index.html` com o nome; cada inativa não tem pasta. Publicação: `readlink /var/www/portal/atual` diz a versão no ar e `curl localhost:8081` mostra `PORTAL-OK`; `ultima-publicacao.txt` diz versão e resultado.

## 2. Inventário

> Quem são os alvos e como estão agrupados?
> - Em quais hosts os dois playbooks agem? Esperar o nginx responder é uma decisão do nó ou do nó de controle? De onde parte a verificação de saúde?

**Sua resposta:**

Os dois playbooks agem no grupo `web`. A verificação de saúde parte do próprio nó (`localhost:8081`), porque é o nginx daquele nó que está sendo testado.

## 3. Variáveis

> O que muda entre hosts ou ambientes? Em qual camada cada valor mora?
> - De onde vêm a lista de áreas e o nome da versão? Qual é o padrão de `dir_releases` e como ele pode ser sobreposto? Que valor o registro grava quando dá certo e quando dá errado?

**Sua resposta:**

A lista `areas` vem de `dados/areas.yml` (dado). `versao` é sempre informada com `-e`; `dir_releases` tem padrão `{{ playbook_dir }}/releases` e `-e` sobrepõe. O registro grava ok ou falha conforme o caminho.

## 4. Estrutura

> Quais plays, tasks ou roles, e em que ordem?
> - Parte A: quantas tasks, e qual `when` em cada? Parte B: escreva o fluxo em linhas (antes de mudar, mudar, verificar, desfazer, registrar) e marque quais ficam em `block`, `rescue` e `always`.

**Sua resposta:**

Áreas: três tasks com `loop`: criar pasta e página (`when: item.ativa`) e remover (`when: not item.ativa`). Publicação: `stat` do link (register), depois `block` (copiar, trocar link, verificar com `until`, anotar sucesso, podar), `rescue` (voltar link, anotar falha, `fail`), `always` (gravar o registro).

## 5. Risco

> O que pode falhar? Como validar antes de aplicar? Como voltar atrás?
> - O que pode falhar na publicação? Se o `rescue` terminar bem, o play falha ou não? Se o link anterior não existir (primeira publicação), o que acontece? Como testar o plano de retorno sem esperar uma versão defeituosa de verdade?

**Sua resposta:**

Se o `rescue` terminar bem o play seguiria como sucesso: por isso termina em `fail` com o nome da versão. Na primeira publicação sem link anterior, o `when` evita voltar para um link inexistente. Testo o plano de retorno com a versão `exemplo-defeito`.
