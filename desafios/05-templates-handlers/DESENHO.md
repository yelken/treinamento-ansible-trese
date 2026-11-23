# DESENHO — Desafio 05: Templates e handlers

> **Preencha este arquivo ANTES de escrever qualquer YAML.** Ninguém corrige as suas respostas (o `lab verify` só avisa se ele continuar em branco):
> serve para você pensar. Pode rascunhar no papel e resumir aqui. Respostas curtas e objetivas bastam.
> O método completo, com um exemplo resolvido, está em `docs/metodo.md`.

## 1. Estado desejado

> O que precisa ser verdade ao final? Como você vai provar que está verdade?
> - Que três coisas devem ser verdade em cada servidor web (pacote, serviço, página)? Como você prova cada uma sem olhar o playbook (`curl`, `nginx -t`, `systemctl`)?
> - O que a segunda execução deve mostrar no recap? E o que NÃO deve aparecer nela?

**Sua resposta:**

<!-- escreva abaixo desta linha -->

## 2. Inventário

> Quem são os alvos e como estão agrupados?
> - Em quais hosts o play age? Quais hosts não podem ser tocados?

**Sua resposta:**

<!-- escreva abaixo desta linha -->

## 3. Variáveis

> O que muda entre hosts ou ambientes? Em qual camada cada valor mora?
> - O que muda entre os servidores (nome do host)? O que muda entre ambientes (porta, nome do ambiente)? Onde cada valor padrão vai morar, de modo que `-e` consiga sobrepô-lo?

**Sua resposta:**

<!-- escreva abaixo desta linha -->

## 4. Estrutura

> Quais plays, tasks ou roles, e em que ordem?
> - Quais tasks, em que ordem? Quais geram arquivo por template? Quais delas notificam o handler, e por quê só elas? O que o handler faz?

**Sua resposta:**

<!-- escreva abaixo desta linha -->

## 5. Risco

> O que pode falhar? Como validar antes de aplicar? Como voltar atrás?
> - O que acontece se o nome no `notify` não bater com o do handler? E se a configuração gerada for inválida: como evitar que ela chegue ao serviço em execução? Como voltar atrás?

**Sua resposta:**

<!-- escreva abaixo desta linha -->
