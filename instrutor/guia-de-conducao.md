# Guia de condução — instrutor

> **Material do instrutor. Não distribuir aos alunos** (`empacotar-aluno.sh` exclui esta pasta).

Este guia acompanha os desafios, um por um. Para cada um você encontra: objetivo, tempo, o que observar, erros comuns (com a forma de **guiar sem entregar a resposta**), respostas esperadas das perguntas de reflexão e notas sobre o verificador.

## Princípios de condução

- **Faça a pergunta antes de dar a resposta.** "O que você esperava que acontecesse?" resolve metade dos bloqueios.
- **Mande o aluno de volta ao `DESENHO.md`.** Quase todo erro de execução tem origem em uma resposta em branco ou vaga na pergunta 1 (estado desejado) ou 5 (risco).
- **Use o `lab verify` como espelho.** A mensagem diz o que foi encontrado e o que era esperado; peça ao aluno que a leia em voz alta e diga o que ela revela.
- **Dicas em ordem.** `lab hint NN` libera uma dica por vez (conceitual, direta, módulo e parâmetro). Incentive tentar alguns minutos entre uma e outra.
- **Sobre a IA:** os alunos têm o `AGENTS.md` e o `tutor.mdc`. Se um aluno disser que a IA "se recusou", elogie a regra e retome a pergunta orientadora. Se alguém chegar com uma solução que não consegue explicar, peça que explique cada task e faça a **previsão** do recap antes de rodar.
- **Tempo da missão essencial** é uma referência para a turma média. A extensão opcional é para quem terminar antes: nunca a cobre de todos.

### Como funciona o verificador (para você saber o que esperar)

- Roda no nó de controle, com as mesmas permissões do aluno, e executa o playbook dele de verdade. Idempotência é medida pelo recap real (`changed=0` na segunda rodada).
- Cada linha é um critério (✔/✘). O total aparece como "N de M critérios atendidos". Seções de **extensão opcional** são mostradas à parte e não entram na conta.
- Quando o `DESENHO.md` está em branco (menos de 4 palavras em alguma das cinco respostas), aparece um **lembrete**, mas ele **não reprova**. É uma decisão de projeto: o desenho não é auditável de forma automática, e reprovar por isso incentivaria o texto vazio. A conversa sobre o desenho é sua, no atendimento individual.
- Alguns verificadores **preparam o terreno** antes de rodar o playbook do aluno (e avisam isso na saída): o 02 devolve os nós `web` ao estado limpo; o 03 recria o usuário `marcos`. Assim o resultado não depende de o aluno ter rodado o playbook antes.

### Operação no dia a dia

- `lab start NN` coloca os nós no estado inicial do desafio (pode ser repetido).
- `lab reset` recria tudo do zero (~10 s). Use quando o aluno "quebrou o laboratório".
- `instrutor/gabarito.sh aplicar NN` copia o gabarito para `desafios/NN-...` (guardando o estado anterior); `restaurar NN` desfaz. Use para demonstrações, **nunca com a tela projetada para a turma sem avisar**.

---

## Desafio 01 — Inventário e primeiro contato

| | |
|---|---|
| **Dia / tempo** | Dia 1 · missão ~15 min |
| **Objetivo** | O aluno modela o ambiente em um inventário (grupos e grupo de grupos), prova que o Ansible alcança cada grupo e usa **ad-hoc** para descobrir fatos, aprendendo a consultar `ansible-doc` e `ansible-inventory`. |

### O que observar

- O aluno preenche o `DESENHO.md` ou vai direto ao editor?
- Ele testa o inventário com `ansible-inventory --graph` **antes** de testar conexão?
- Ele descobre o nome dos fatos lendo a saída do `setup` ou chuta?
- Ele registra os fatos copiando da saída ou digitando de memória?

### Erros comuns e como guiar

| O que acontece | Pergunta que guia (sem dar a resposta) |
|---|---|
| Usa `hosts:` no grupo do ambiente e lista `web`, `db`, `lb` como se fossem hosts. O `--graph` mostra três "hosts" novos. | "Rode `ansible-inventory --graph`. Quantos hosts existem de verdade? Que palavra do YAML diz 'este grupo contém *grupos*'? Procure no exemplo da teoria." |
| Deixa `lb1` (ou outro) fora de grupo; aparece em `ungrouped`. | "O que o `--graph` mostra além dos três grupos? Qual critério do README fala disso?" |
| Cria `inventario/hosts` em INI sem entender que o verificador lê a pasta. | Nada a corrigir: a pasta aceita INI e YAML. Só confirme se o `--graph` bate. |
| Usa `ansible all -m ping` e conclui que "está tudo certo", sem ver os grupos. | "O ping de `all` prova que *os hosts* respondem. Prova que *cada grupo* tem os hosts certos?" |
| Rodar `setup` sem filtro e colar a saída inteira. | "Você precisa de dois valores por nó. Como pedir só o que interessa? `ansible-doc ansible.builtin.setup`, parâmetro `filter`." |
| Anota a memória com `free -m` (valor diferente do fato). | O verificador tolera diferença de poucos MB; só pergunte "de onde veio esse número?". Todos os nós reportam a memória total da VM do Docker (valores iguais) — isso é normal e vira ótimo ponto de conversa (ver abaixo). |
| Digita "Rocky Linux 9" em vez de `Rocky`. | Aceito: o verificador procura o nome da distribuição dentro do texto. Não corrija. |

### Reflexão: respostas esperadas

1. **400 servidores:** não se escreve à mão. Faixas de nomes (`web[01:50]`), vários arquivos de inventário em uma pasta, plugins de inventário e **inventário dinâmico** (nuvem, CMDB, vCenter). O ponto principal: o inventário pode ser *gerado*.
2. **Onde mora "homologação":** em um **grupo** (`homologacao`, com `web`, `db`, `lb` como filhos) e, para valores, em `group_vars/<grupo>`. No nome do host é frágil (renomear quebra tudo); em variável por host é repetitivo. Com produção ao lado, cada ambiente é um grupo de grupos, e um host pode estar em mais de um grupo (ambiente **e** função).
3. **Variável diferente em dois grupos:** o Ansible tem regras de precedência (e, para grupos de mesmo nível, ordem alfabética, ou `ansible_group_priority`). A resposta completa vem no Dia 2 (desafio 04); aqui basta o aluno perceber que **existe uma regra** e que não se deve depender de "sorte".

**Pergunta-ponte:** "Por que todas as memórias saíram iguais, se os nós têm perfis diferentes?" → os containers compartilham a memória da VM do Docker. Em servidores reais os fatos seriam diferentes; isso reforça por que se **coleta** e não se **supõe**.

### Extensão opcional (padrões de hosts)

Respostas: `all:!web`; `web[-1]` (índice negativo: o último do grupo, aqui `web2`); `web:lb:!web1`; `*1`. Recomende que testem com `--list-hosts` (não conecta em ninguém).

---

## Desafio 02 — Primeiro playbook idempotente

| | |
|---|---|
| **Dia / tempo** | Dia 1 · missão ~15 min |
| **Objetivo** | Escrever o primeiro playbook: instalar pacotes e garantir um serviço ativo e habilitado, com `become`, FQCN e `name`; entender idempotência pelo recap (`changed=0`). |

### O que observar

- O aluno roda `--syntax-check` e `--check --diff` antes de aplicar?
- Ele **lê o recap** da segunda execução e sabe dizer o que significa `changed`?
- Ele esquece o `become` e o erro de permissão o confunde?

### Erros comuns e como guiar

| O que acontece | Pergunta que guia |
|---|---|
| `command: dnf install -y ...` ou `shell: systemctl start crond`. | "Rode duas vezes e compare o recap. O que mudou na segunda? Essa task descreve um *estado* ou executa um *comando*?" |
| Esquece `become: true`: erro de permissão ao instalar. | "Que usuário o Ansible usa para entrar? Esse usuário pode instalar pacotes? Onde se declara a elevação de privilégio, e em qual nível (play ou task)?" |
| Usa `state: started` mas não `enabled`; o verificador pede os dois. | "Leia o critério: 'ativo' e 'habilitado' são o mesmo? Um se refere a quando?" Observação do instrutor: no Rocky, instalar o `cronie` já habilita o `crond` pelo *preset* do pacote; por isso o critério "habilitado" pode passar por sorte em alguns playbooks. Se for o caso, pergunte "e se o pacote já estivesse instalado e o serviço desabilitado?". |
| `hosts: all` em vez de `web`; `db1` (Debian) falha por causa do `dnf`. | "Quais hosts a missão diz que **não** podem ser tocados? Em que linha você declarou os alvos?" |
| Uma task por pacote (4 tasks `dnf`). | Não é erro. Pergunte depois: "o `name:` aceita só um valor? Quantas vezes o `dnf` rodaria?" |
| Sem `name`, ou módulo curto (`dnf:`). | Mostre o critério "FQCN" e `ansible-doc -l | grep dnf`. |
| `state: latest`. | Funciona e é idempotente, mas muda o comportamento ao longo do tempo. Pergunte: "A missão pede *instalado* ou *atualizado*?" |

### Reflexão: respostas esperadas

1. **E o Debian?** O módulo de pacotes (`dnf`) é de família Red Hat; no Debian seria `apt`, ou o módulo genérico `ansible.builtin.package`. Os **nomes** dos pacotes e do serviço também mudam (`cron` em vez de `crond`, e `cronie` não existe). Específico de família: o módulo, os nomes de pacote e de serviço.
2. **`command: dnf install`:** não é idempotente (reporta `changed` sempre), não diz o que quer (pacote, versão), não faz `--check`, depende de saída de texto, e esconde mudanças reais em meio ao ruído. Em 400 servidores toda noite, `changed` constante torna impossível distinguir uma mudança real de uma rotina.
3. **Provar sem executar / depois de executar:** `--check --diff` (e `--syntax-check`) antes; depois, segunda execução com `changed=0` e conferência independente no nó (`rpm -q`, `systemctl is-active`, `is-enabled`).

### Extensão opcional (cron)

Módulo `ansible.builtin.cron`, com `name: limpeza-tmp` (o nome vira o comentário `#Ansible: limpeza-tmp`), `minute: "30"`, `hour: "2"` e `job`. O `name` é o que garante a idempotência: sem ele, cada execução duplica a entrada.

---

## Desafio 03 — Arquivos, usuários e permissões

| | |
|---|---|
| **Dia / tempo** | Dia 1 · missão ~15 min |
| **Objetivo** | Um playbook, dois sistemas operacionais: banner, diretórios com dono/grupo/modo (inclusive `setgid`), grupo e usuários, regra de `sudo` **validada**, ajuste de linha em arquivo de configuração e remoção completa de uma conta. |

### O que observar

- Aparecem **dependências** (grupo antes do diretório e do usuário)? O aluno as percebeu no desenho?
- Os modos estão entre aspas?
- Ele valida o `sudoers` ou grava direto?
- Ele roda no Debian (`db1`) e confere a saída lá?

### Erros comuns e como guiar

| O que acontece | Pergunta que guia |
|---|---|
| Modo sem aspas (`mode: 2770`): fica um modo estranho (o YAML lê número). O `0755` "funciona" por acaso, o `2770` não. | "Qual é o modo que aparece no `ls -ld` do nó? Como o YAML interpreta um número começando com zero? Na dúvida, como se escreve um modo para que ele seja *texto*?" |
| Diretório com grupo `adm-infra` criado **antes** do grupo: erro "group ... does not exist". | "Leia o erro: que grupo ele não achou? Em que ordem as tasks rodam?" |
| `user` sem `shell`: na `db1` (Debian) o shell padrão é `/bin/sh`, no Rocky é `/bin/bash`. Falha só no `db1`. | "O critério falha em todos os nós ou só em um? O que muda entre os dois sistemas? O que você declarou explicitamente e o que deixou ao padrão?" |
| `groups: adm-infra` sem pensar em `append`. | "Se o usuário já tivesse outros grupos, o que aconteceria com eles? Procure `append` no `ansible-doc ansible.builtin.user`." |
| Sudoers gravado sem `validate`. | Critério estático falha. "O que acontece em 400 servidores se a regra tiver um erro de digitação?" (Ver reflexão 2.) |
| `lineinfile` sem `regexp`: a linha nova é **adicionada** e `PASS_MAX_DAYS` fica duplicado. | "Conte as linhas `PASS_MAX_DAYS` no arquivo do nó. Como o módulo sabe qual linha **trocar**?" |
| `user: state: absent` sem `remove`: o diretório `/home/marcos` fica. | "Remover a *conta* e remover o *que ela deixou* são o mesmo comportamento? Procure em `ansible-doc ansible.builtin.user`." |
| `command: useradd`, `shell: echo >> /etc/login.defs`. | Idempotência: peça a segunda rodada e leia o recap. |
| Texto do banner com espaço ou acento diferente. | O verificador procura o texto exato: "compare, caractere a caractere, com o README". |

### Notas do instrutor

- O gabarito usa `loop` (conceito formal do desafio 06) para diretórios e usuários, por economia. **O aluno pode usar três tasks separadas, e está tudo bem**: o verificador não exige `loop`. Se alguém repetir muito, aproveite para plantar a pergunta "e se fossem 30 usuários?" (reflexão 1), que é a ponte para o Dia 2.
- O verificador **recria `marcos`** antes de rodar o playbook (avisa na saída), então o aluno não precisa ter rodado `lab start 03` na hora, e pode repetir a verificação à vontade.
- Se o aluno derrubar o próprio acesso (muito improvável, pois o `ansible` entra por chave), `lab reset` resolve.

### Reflexão: respostas esperadas

1. **30 administradores, mudando todo mês:** a lista deve ser **dado** (variável, em `group_vars` ou em um arquivo de variáveis), não texto espalhado nas tasks; a task a consome com `loop`. Quem muda a lista não precisa mexer na lógica (princípio do desenho, pergunta 3). Aproveite para antecipar o Dia 2.
2. **`validate` no sudoers:** um erro de sintaxe no `sudoers` pode **invalidar o sudo inteiro**: ninguém mais consegue elevar privilégio, nem o próprio Ansible (que usa `become`). Em 400 servidores, o acesso administrativo cai em todos, ao mesmo tempo, e a correção exige acesso físico ou console. O `validate` testa o arquivo temporário **antes** de ele substituir o definitivo.
3. **Edição manual do `/etc/motd`:** na próxima execução, o playbook **restaura** o conteúdo desejado (`changed` naquele nó). É bom (a configuração converge para o desenhado: *drift* corrigido, sem mão humana) e pode ser ruim (apaga um ajuste legítimo de emergência, se ninguém registrou no repositório). Mensagem: o repositório é a fonte da verdade; mudança manual é dívida.

### Extensão opcional (chave SSH autorizada)

Módulo `ansible.posix.authorized_key`, com `user: ana` e `key` lida de `dados/ana.pub` (`lookup('ansible.builtin.file', ...)`). Os modos `0700`/`0600` do `.ssh` e do `authorized_keys` são tratados pelo próprio módulo. Se o aluno procurar em `ansible.builtin` e não achar, é exatamente o objetivo: `ansible-galaxy collection list` e `ansible-doc -l ansible.posix`.

---

*Os desafios 04 a 12 serão acrescentados nas próximas fases.*
