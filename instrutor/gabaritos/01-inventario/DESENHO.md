# DESENHO — Desafio 01: Inventário e primeiro contato

> **Preencha este arquivo ANTES de escrever qualquer YAML.** Ninguém corrige as suas respostas (o `lab verify` só avisa se ele continuar em branco):
> serve para você pensar. Pode rascunhar no papel e resumir aqui. Respostas curtas e objetivas bastam.
> O método completo, com um exemplo resolvido, está em `docs/metodo.md`.

## 1. Estado desejado

> O que precisa ser verdade ao final? Como você vai provar que está verdade?
> - Que pergunta o verificador fará a cada nó? Que comando seu responde a mesma pergunta?
> - Como você vai conferir a árvore de grupos antes de testar a conexão?

**Sua resposta:**

<!-- escreva abaixo desta linha -->
Os 4 nós alcançáveis pelo grupo certo. Prova: ansible-inventory --graph mostra a árvore, ping por grupo responde e respostas.txt bate com o que o setup reporta.

## 2. Inventário

> Quem são os alvos e como estão agrupados?
> - Quais são os hosts? Quais rótulos (grupos) cada um carrega? O grupo do ambiente tem hosts próprios ou só aponta para outros grupos?

**Sua resposta:**

<!-- escreva abaixo desta linha -->
web = web1, web2; db = db1; lb = lb1; grupo homologacao aponta (children) para web, db e lb. Nenhum host solto.

## 3. Variáveis

> O que muda entre hosts ou ambientes? Em qual camada cada valor mora?
> - Nesta missão, algum valor muda de host para host? Ainda não é hora de usar variáveis: o que você anotaria para depois?

**Sua resposta:**

<!-- escreva abaixo desta linha -->
Nada varia por host nesta missão. Anotar para depois: o ambiente (homologacao) deveria virar variável de grupo.

## 4. Estrutura

> Quais plays, tasks ou roles, e em que ordem?
> - Em que ordem você vai trabalhar: inventário, ping, coleta de fatos, registro das respostas? Por quê?

**Sua resposta:**

<!-- escreva abaixo desta linha -->
Primeiro o inventário e a árvore (--graph), depois ping por grupo, depois setup com filter e registro das respostas.

## 5. Risco

> O que pode falhar? Como validar antes de aplicar? Como voltar atrás?
> - Qual o efeito de um nome de host digitado errado? Como você percebe isso antes de rodar qualquer comando em todos os nós?

**Sua resposta:**

<!-- escreva abaixo desta linha -->
Nome de host errado vira host fantasma e falha no ping. Valido com --graph e --list-hosts antes de rodar em todos; nada é alterado nos nós.

