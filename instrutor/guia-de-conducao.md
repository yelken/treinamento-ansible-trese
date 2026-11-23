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
- Alguns verificadores **preparam o terreno** antes de rodar o playbook do aluno (e avisam isso na saída): o 02 devolve os nós `web` ao estado limpo; o 03 recria o usuário `marcos`; o 05 e o 07 removem o nginx; o 08 remove a conta `appportal`; o 09 põe a versão 1 no ar atrás do balanceador. Assim o resultado não depende de o aluno ter rodado o playbook antes.

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

## Desafio 04 — Variáveis, facts e precedência

| | |
|---|---|
| **Dia / tempo** | Dia 2 · missão ~25 min |
| **Objetivo** | Separar **dado** de **lógica**: valores em `group_vars`/`host_vars`, um único conjunto de tasks para duas famílias de SO (via fato `os_family` e um dicionário de dados), e exercitar a **precedência** de variáveis prevendo antes de rodar. |

### O que observar

- O aluno resolve a diferença `bind-utils` × `dnsutils` com `when` (o critério proíbe) ou com **dado** (um dicionário por família, consultado pelo fato)?
- Ele faz a **previsão antes** de rodar os comandos da Parte B? (O verificador só confere o valor *observado*; a previsão é para ele.)
- Ele diferencia "valor do host" (`ansible-inventory --host`) de "valor visto pelo play"?

### Erros comuns e como guiar

| O que acontece | Pergunta que guia |
|---|---|
| Usa `when: ansible_os_family == ...` com duas tasks de pacote. | "Daqui a seis meses entra o Ubuntu. Quantas tasks mudam? E se a diferença fosse só um **valor**, onde ele moraria?" |
| Erra a grafia da chave do dicionário (`RedHat` × `redhat`, `Debian`). | "Rode `ansible db1 -m setup -a filter=ansible_os_family`. Compare, caractere por caractere, com a chave que você escreveu. A caixa importa." |
| `apt` em `db1` falha por cache vazio. | No laboratório as listas do apt já vêm carregadas na imagem, então não deve ocorrer. Se ocorrer, é rede: veja `lab status`. Em produção a pergunta é "quando o cache deve ser atualizado?" (`update_cache` e `cache_valid_time`). |
| Coloca a retenção de 90 dias do `db1` no `site.yml` com `when: inventory_hostname == 'db1'`. | "Se o `db1` mudar de nome, quantos arquivos você edita? Qual camada o Ansible oferece para valor **de um host**?" |
| Previsão 2 (`nivel_log`): erra por achar que o grupo "de cima" vence. | "Os dois grupos estão no mesmo nível. Que regra desempata? Rode `ansible-inventory -i conflitos/inventario --host web1`." (Mesmo nível: ordem **alfabética** do nome do grupo; o último vence.) |
| Previsão 3: esquece que `-e` vence tudo. | "Que camada está acima de `host_vars`? Rode o comando e leia a saída." |
| Segunda rodada com `changed`: o arquivo `ficha` usa `lineinfile` ou `command: echo`. | "Descreva o estado final do arquivo inteiro. Um `template`/`copy` com `content` o descreve melhor que um `echo`?" |

### Notas do instrutor

- O verificador confere `previsoes.txt` apenas no campo **observado**: errar a previsão não reprova, de propósito. Peça à turma que leia as previsões em voz alta *antes* de mostrar as respostas: é aí que a precedência fica na memória.
- O gabarito usa um dicionário por família (`pacote_dns_por_familia`) e uma variável `pacote_dns` calculada com `os_family`. O aluno pode chegar ao mesmo resultado de outro jeito; aceite desde que **não** haja `when` por distribuição.

### Reflexão: respostas esperadas

1. **Onde registrar a justificativa:** junto ao dado, em **comentário no próprio `host_vars/db1.yml`** (com a data, o chamado e quem decidiu) e na mensagem do commit. Comentário perdido no playbook, ou "na cabeça de alguém", se perde.
2. **Não depender da ordem alfabética:** não definir a mesma variável em dois grupos do mesmo nível; ou usar `ansible_group_priority`; ou levar o valor a uma camada que não concorre (`host_vars`, ou um grupo-pai bem definido). O ideal é **desenhar** o inventário para que cada variável tenha uma única fonte.
3. **`-e` em produção:** para valores pontuais e conscientes (a versão a publicar, uma janela de manutenção), que vencem tudo por desenho. O risco é a **sobrescrita silenciosa**: um `-e` esquecido em um script de CI passa por cima do inventário sem deixar rastro no repositório.

### Extensão opcional (fato local)

`ansible.builtin.file` (diretório `/etc/ansible/facts.d`), `ansible.builtin.copy` do `.fact` (INI com `[dados]`), `ansible.builtin.setup` com `filter=ansible_local` para **recarregar** os fatos na mesma execução, e a linha da ficha lida de `ansible_local.ficha.dados.responsavel`. Armadilha comum: usar o fato antes do `setup`; na primeira rodada ele ainda não existe.

---

## Desafio 05 — Templates e handlers

| | |
|---|---|
| **Dia / tempo** | Dia 2 · missão ~30 min |
| **Objetivo** | Gerar configuração e página com `template` (Jinja2), recarregar o nginx **só quando algo muda** (handler com `notify`) e **validar** a configuração antes de ela entrar no ar. |

> Este desafio **instala o nginx de verdade** nos nós `web`: é preciso acesso à internet (ou a um *mirror*) na hora de rodar.

### O que observar

- O aluno entende que o handler roda **no fim do play**, e não no instante do `notify`?
- Ele testa a segunda rodada **lendo o recap** e os nomes das tasks que rodaram, não só o `changed=0`?
- Ele separa o que dispara recarga (configuração) do que não dispara (página)?

### Erros comuns e como guiar

| O que acontece | Pergunta que guia |
|---|---|
| `service: state: restarted` em uma task comum, no lugar do handler. | "Rode duas vezes. O recap mostra `changed` na segunda? O que isso diz sobre o que você descreveu?" |
| Handler com nome diferente do `notify`. | **Atenção:** no Ansible 2.21 isso é **erro**, mas só aparece quando a task que notifica **muda**. Na segunda rodada nada acontece e o aluno acha que está certo. "O que você espera ver se alterar a porta? Teste isso." Boa deixa para o desafio 11 (defeito plantado). |
| `notify` na task da página. | "Mudar o texto da página exige recarregar o nginx? O que o nginx lê na recarga?" |
| `validate: nginx -t` (sem `-c %s`) ou `validate` em um *fragmento* de configuração. | O `validate` testa o **arquivo temporário**, e o `nginx -t` só aprova uma configuração **completa**. "O que o `nginx -t` precisa receber para validar esse arquivo? O arquivo que você gera é uma configuração inteira?" |
| A página não mostra o host: usa uma variável que difere do nome do inventário. | "O critério fala do nome *como no inventário*. Qual variável mágica traz isso?" |
| Porta fixa dentro do template. | "O verificador roda com outra porta. Onde essa porta deveria viver para ser trocada sem editar o template?" |
| Reiniciar em vez de recarregar. | "O que acontece com as conexões abertas em cada caso? E se a configuração estiver inválida?" |

### Reflexão: respostas esperadas

1. **Texto da página × porta:** o texto **não** exige recarga (o nginx lê o arquivo a cada requisição). A **porta** exige (é configuração lida na partida/recarga). Só as tasks que alteram **a configuração** notificam o handler.
2. **Sem `validate`:** uma configuração inválida chega aos 400 servidores. Com `reloaded`, o nginx **recusa** a configuração nova e continua com a antiga (o serviço segue no ar, mas "desatualizado", com erro no log). Com `restarted`, ele **tenta subir com a configuração inválida e fica fora do ar** em todos os servidores.
3. **Edição manual:** na próxima execução o `template` detecta a diferença, **restaura** o arquivo e notifica o handler (que roda e recarrega). É desejável (a configuração converge, *drift* corrigido) e perigoso se a mudança manual era uma correção de emergência não registrada.

### Extensão opcional (página que conhece o grupo)

`groups['web']` com `{% for h in groups['web'] %}`. Mostra que o template tem acesso a **todo o inventário**, não só ao host da vez.

---

## Desafio 06 — Condicionais, loops e erros

| | |
|---|---|
| **Dia / tempo** | Dia 2 · missão ~35 min |
| **Objetivo** | Dois playbooks: um orientado a **dados** (`loop` + `when` + remoção do que sobrou) e uma **publicação segura** (`register`, `until`, `block`/`rescue`/`always`, retorno automático e registro do resultado). |

> O verificador do 06 é o mais demorado do Dia 2 (**cerca de 2 minutos**): ele publica várias versões e executa as áreas duas vezes. Avise a turma para não interromper.

### O que observar

- O aluno trata a lista como **dado** (e a obedece quando o verificador a troca) ou escreve os nomes?
- Na publicação: ele guarda o destino do link anterior **antes** de trocá-lo (`stat` + `register`)? É a decisão central.
- O `rescue` termina com `fail`? Sem isso, o play continua **verde**, mesmo com a versão rejeitada.
- Ele testa o caminho de falha com `exemplo-defeito`, e não só o do sucesso?

### Erros comuns e como guiar

| O que acontece | Pergunta que guia |
|---|---|
| Áreas inativas só **não são criadas**; diretórios antigos continuam lá. | "O critério diz que a pasta não pode existir. Que estado você descreve para uma área inativa: 'não faço nada' ou 'ausente'?" |
| `rescue` volta o link e **não** termina com `fail`. O play fica verde. | "Quem precisa saber que a publicação foi rejeitada? O que o recap mostra? Que módulo encerra um play com mensagem?" (`ansible.builtin.fail`.) |
| Link anterior lido depois da troca. | "Em que momento você sabe qual era a versão no ar? Esse valor ainda existe depois da troca?" |
| Verificação de saúde sem `until`: falha na primeira tentativa porque o nginx ainda está se firmando. | "O que acontece nos primeiros segundos depois da troca? Como pedir ao Ansible para tentar de novo?" |
| `ignore_errors: true` em vez de `block`/`rescue`. | "O que você quer que aconteça **depois** da falha? O `ignore_errors` ajuda a fazer isso ou só silencia?" |
| Mensagem de falha genérica ("falhou"). | "Releia o critério: a mensagem precisa citar o quê? Qual variável tem esse valor?" |
| O `always` não grava o resultado quando falha (a task está no `block`). | "Em qual seção ficam as tasks que rodam **sempre**?" |
| `changed` em toda publicação da mesma versão (copia sempre, link recriado, `command: ln -s`). | "O que descreve o estado de um link: o módulo `file` com `state: link`? E o de uma pasta copiada?" |

### Reflexão: respostas esperadas

1. **400 servidores ao mesmo tempo:** o retorno **por nó** protege cada nó, mas todos tentam a mesma versão defeituosa **ao mesmo tempo**: se o defeito só aparece sob carga, todos já estarão na versão ruim quando alguém perceber. A resposta é `serial` + `max_fail_percentage`, que o desafio 09 vê.
2. **`fail` no fim do `rescue`:** o `rescue` **absorve** o erro: sem `fail`, o play termina com sucesso e o pipeline/CI acha que publicou. O erro precisa **subir** a quem opera.
3. **O `always`:** um painel de implantações, uma regra de CI que bloqueia a próxima publicação, um chamado automático, uma auditoria. O registro é o que torna possível a decisão **fora** do Ansible.

### Extensão opcional (histórico enxuto)

Módulo `ansible.builtin.find` (diretórios, ordenados por idade), e remoção das mais antigas por `loop`, **excluindo** a que `atual` aponta. A armadilha é apagar a versão no ar quando ela é antiga (retorno recente): a exclusão deve olhar para onde o link aponta, e não só para a idade.

---

## Desafio 07 — Da lista de tasks à role

| | |
|---|---|
| **Dia / tempo** | Dia 3 · missão ~35 min |
| **Objetivo** | Refatorar um playbook monolítico em uma **role** autocontida: estrutura, `defaults` × `vars`, prefixo de variáveis, README da role, mesmo resultado nos nós. |

> `lab start 07` **gera** o `monolitico.yml` e os `templates/` na pasta do aluno (vêm da imagem; estão no `.gitignore`). O verificador remove o nginx antes de rodar, então também precisa de internet (ou de um *mirror*).

### O que observar

- O aluno usa `ansible-galaxy role init` ou monta as pastas à mão?
- Ele **renomeia as variáveis também dentro dos templates**? É o erro mais comum (`undefined variable`).
- Ele decide **conscientemente** o que vai em `defaults` e o que vai em `vars`? (Pergunta 3 do `DESENHO.md`.)
- Ele roda `--list-tasks` para ver o prefixo da role nas tasks?

### Erros comuns e como guiar

| O que acontece | Pergunta que guia |
|---|---|
| `undefined variable` (nome novo ou antigo) em um template. | "Em que arquivo a variável é *usada*? Você renomeou lá também? `grep -rn raiz_site roles/`." |
| Porta e ambiente em `vars/main.yml`. | "Qual camada vence: `vars` da role ou `group_vars`? Se o usuário da role precisa mudar, vai em qual pasta?" (O `-e` do verificador ainda vence `vars`, então só o critério estático pega o princípio.) |
| `tasks/main.yml` copiado com o cabeçalho `tasks:` (ou com `hosts:`). | "A role espera uma **lista** de tasks. Compare com o início do `tasks/main.yml` de uma role gerada pelo `init`." |
| `site.yml` ainda com tasks soltas "porque funciona". | "Quem é dono dessa task: a role ou o play? Daqui a seis meses outro time usa a role: a task solta vai junto?" |
| `src: templates/nginx.conf.j2` (caminho completo). Funciona, mas é o hábito errado. | "Dentro de uma role, onde o `template` procura `src` por padrão? O que acontece se alguém renomear a pasta?" |
| README da role gerado e não editado (cita variáveis que não existem). | "O README descreve a interface pública: quais variáveis estão em `defaults`?" |
| Handler da role não roda porque o nome no `notify` ficou diferente do `handlers/main.yml`. | "Em que arquivo a role procura os handlers? O nome é o mesmo?" (No resultado, handlers de role aparecem como `role : nome`.) |

### Reflexão: respostas esperadas

1. **Expor:** o texto/arquivo da página (variável ou `template` substituível), o ambiente, a porta, talvez o caminho da raiz do site. O ponto: tudo que muda entre usuários vai para `defaults`; a role fica **fechada para edição e aberta para configuração**.
2. **Colisão de `porta`:** a **última** definida vence (as duas roles compartilham o mesmo espaço de nomes), e uma role passa a usar o valor da outra, **sem erro**. Descobre-se com `ansible-inventory --host`, `-v`, `--list-tasks` e lendo a precedência. A defesa é o prefixo (e o `ansible-lint` aponta `var-naming[no-role-prefix]`).
3. **Quando não vale:** automação usada **uma vez**, ou muito simples (duas tasks). Regra de bolso: a segunda vez que você copia o playbook, é hora de pensar em role. Custo de uma role: estrutura, README, versão, testes.

### Extensão opcional (role publicável)

`meta/main.yml` com autor, descrição, licença e plataformas; remoção do que não é usado; `ansible-lint` sem apontamentos no perfil `production`. O verificador roda `ansible-lint` sobre `site.yml` e a role.

---

## Desafio 08 — Segredos com Ansible Vault

| | |
|---|---|
| **Dia / tempo** | Dia 3 · missão ~30 min |
| **Objetivo** | Proteger um segredo de ponta a ponta: **cofre cifrado** + arquivo visível com os nomes (padrão `vars` × `vault`), `no_log`, saída limpa com `-v`/`-vvv`, e a senha de um usuário com `password_hash` mantendo a **idempotência**. |

> O segredo é **fictício** (`/etc/lab/segredos/`, na imagem do nó de controle, fora do `/lab`). A senha do Vault também (`/etc/lab/vault-pass`, sem bit de execução, como pede o projeto). O `ansible.cfg` do desafio já aponta para ela; o aluno **não** precisa de `--ask-vault-pass`.

### O que observar

- Como o aluno **leva o valor** do cofre de segredos para o `ansible-vault create`? Quem usa `encrypt_string 'valor'` na linha de comando deixa o segredo no **histórico do shell**: use isso como conversa (o README já alerta).
- Ele abre o cofre com `ansible-vault view` para conferir, ou confia?
- Ele roda com `-vvv` e **lê** a saída?

### Erros comuns e como guiar

| O que acontece | Pergunta que guia |
|---|---|
| **Segunda rodada com `changed`** na task `user`. É a pegadinha central: `password_hash('sha512')` usa um *salt* **aleatório**, então o hash muda a cada execução. | "O que mudou entre as duas execuções? Para o Ansible, a senha mudou? Leia `ansible-doc -t filter ansible.builtin.password_hash` e procure o que fixa o valor que muda sozinho." (Salt fixo, até 16 caracteres.) |
| Passa o **texto** em `password:` (sem hash). O módulo grava o texto como se fosse o hash e o login não funciona. | "O que o parâmetro `password` do módulo `user` espera? Olhe o `/etc/shadow` do nó." |
| Variáveis do cofre **sem** o prefixo `vault_`, ou nenhum arquivo visível apontando para elas. | "Se alguém fizer `grep` pela variável no projeto, o que encontra? E sem abrir o cofre?" |
| Cofre em `group_vars/web.yml` cifrado e nada em claro (o padrão pede dois arquivos). | "Para saber **quais** variáveis o projeto usa, o que é preciso fazer hoje? Quanto custa isso em uma revisão de código?" |
| `no_log: true` esquecido. O módulo `user` já mascara o parâmetro `password`, então a saída pode não vazar *neste* caso, mas um `debug` ou um `copy` com `content` mostraria. O verificador cobra `no_log` **estaticamente** e confere a saída **de fato**. | "Mesmo que hoje nada vaze, o que protege a próxima pessoa que acrescentar uma task?" |
| `debug: var=...` "para conferir". | "A tela e o log do CI são seguros? Como conferir sem imprimir (`ansible-vault view`, `getent shadow` no nó)?" |
| Senha do Vault copiada para dentro do projeto (`.vault_pass`). | "O que adianta cifrar o cofre se a chave está ao lado? Para onde o `ansible.cfg` já aponta?" |
| `ansible-vault create` abre um editor que o aluno não conhece. | Problema de ambiente, não do exercício: `export EDITOR=nano` (o laboratório traz `nano` e `vim`). |

### Reflexão: respostas esperadas

1. **Clone em outra máquina:** além do repositório, precisa da **senha do Vault** (ou do acesso ao cofre corporativo que a guarda). Só quem opera a automação deve ter essa senha, e ela circula por canal seguro, não por e-mail ou chat.
2. **Apagar no commit seguinte:** o segredo **fica no histórico** do Git (e em clones, forks, caches de CI). A resposta é **rotacionar** o segredo, e não só apagá-lo.
3. **`no_log`:** impede que o **resultado** da task seja impresso (saída, `-v`, `--diff`, log do CI). Não impede: um `debug` que imprime a variável em outra task, um erro que cita o valor, ou o valor no histórico do shell.

### Extensão opcional (token inline)

`ansible-vault encrypt_string --name portal_token '...'` produz o `!vault |` para colar em um arquivo de variáveis; o `ansible.builtin.copy` com `content`, `mode: "0600"` e `no_log: true` grava o arquivo. Lembre que passar o valor na linha de comando o deixa no histórico do shell (alternativa: `--stdin-name`).

---

## Desafio 09 — Atualização gradual

| | |
|---|---|
| **Dia / tempo** | Dia 3 · missão ~40 min |
| **Objetivo** | Atualizar dois servidores atrás de um balanceador **sem o usuário perceber**: `serial`, `delegate_to` (tirar/devolver o nó no HAProxy), espera pela confirmação do balanceador e, na extensão, verificação de saúde com parada antecipada. |

> O verificador leva **cerca de 1,5 minuto**: ele põe a versão 1 no ar, dispara ~30 requisições por segundo ao `lb1` enquanto roda o playbook do aluno, e **nenhuma** pode falhar. **Este desafio não mede idempotência de propósito:** a role fornecida reinicia o nginx a cada execução.
>
> O HAProxy do laboratório usa `retries 0` (sem nova tentativa em outro servidor) **de propósito**: em produção, `retries` e `redispatch` esconderiam parte das falhas, e o aluno não "veria" o problema de atualizar sem tirar o nó. Se a turma perguntar, é uma boa conversa.

### O que observar

- Sem `serial`, o aluno vê o portal cair? Peça que rode `watch -n 0.5 curl -s http://lb1/` (ou o navegador em `localhost:8080`) em outro terminal **enquanto** executa. A experiência vale mais que a explicação.
- Ele pensa em **quanto tempo** o nó fica fora (8 s, por desenho da role) e em **quem avisa o balanceador**?
- Na extensão, ele percebe que o nó doente **não pode voltar** ao balanceador?

### Erros comuns e como guiar

| O que acontece | Pergunta que guia |
|---|---|
| Playbook só com a role e `serial: 1`: o portal responde 503 durante cada atualização. | "Enquanto o `web1` está sem nginx, para onde o balanceador continua mandando requisições? Quem o avisou?" |
| Tira o servidor do balanceador **sem** `delegate_to`: o módulo roda em `web1` e não acha o socket. | "O socket de administração está em qual host? Em que host a task roda por padrão? Que palavra-chave troca o host sem perder o `inventory_hostname`?" |
| `state: disabled` sem `wait`: a task seguinte começa antes de o HAProxy confirmar. Às vezes passa, às vezes não. | "O que significa uma task 'concluída' para o Ansible: o comando foi enviado ou o estado foi atingido? Há parâmetro no módulo para esperar?" |
| Devolve o nó sem `wait`: o play termina quando o HAProxy ainda nem fez as verificações de saúde (`rise 2`); o verificador pode ver o servidor fora de `UP` no fim. | "No fim, o servidor está *UP* ou apenas 'habilitado'? O que o HAProxy exige antes de mandar tráfego?" |
| `shell` com `echo "disable server ..."` e `socat`. | Só funciona com `socat`, que não está instalado. "Há módulo para isso? `ansible-doc -l community.general`, e procure `haproxy`." |
| Só `throttle: 1` na task do balanceador, sem `serial`. | "O `throttle` limita a *task*. As tasks seguintes (a role) rodam nos dois nós juntos?" |
| Role em `roles:` do play, com as tasks do balanceador em `pre_tasks`/`post_tasks`. | Funciona. Confira se o aluno entende a ordem `pre_tasks` → `roles` → `tasks` → `post_tasks`. |
| (Extensão) O playbook não falha com a release doente, ou devolve o nó ao balanceador. | "Quem decide que o nó está bom? Qual URL o nginx expõe? O que o play faz se essa checagem falha?" |

### Notas do instrutor

- **Tempos do HAProxy:** `inter 1s fall 2 rise 2`. Tirar o nó **antes** de parar o nginx é o que evita os 503; a janela entre "nginx parou" e "HAProxy percebeu" (~2 s) é a que quebra o playbook ingênuo.
- **`max_fail_percentage`:** com `serial: 1`, uma falha já é o lote inteiro, e o play para. O gabarito acrescenta `max_fail_percentage: 0` só para tornar a intenção explícita; se o aluno omitir, o resultado é o mesmo.
- O verificador **devolve o laboratório à versão 1** quando executa a extensão. Se a turma interromper o `lab verify 09` no meio, rode `lab start 09`.

### Reflexão: respostas esperadas

1. **`serial: 1` e o tempo:** linear: ~12 s por nó, então 2 nós levam cerca de meio minuto e 200 nós, perto de 40 min. Para frotas grandes: **porcentagem** (`"10%"`) ou **lista** (`[1, 5, "25%"]`: um nó *canário* primeiro, depois lotes maiores). O compromisso é tempo × risco × capacidade restante (quantos nós podem sair sem sobrecarregar os demais).
2. **Role que não conhece o balanceador:** é reutilizável (serve onde não há balanceador, ou há outro), simples de testar e tem **uma só responsabilidade**. Quem **orquestra** (o playbook) sabe a ordem e o contexto. Se a role tirasse e devolvesse o nó, ficaria presa a um balanceador específico.
3. **Release com defeito hoje:** sem verificação de saúde, o playbook devolve o nó doente ao balanceador e segue para o próximo: ao final, **todos** estão doentes, um de cada vez. A extensão corta isso: valida a saúde antes de devolver, e a falha para o play.

### Extensão opcional (release com defeito)

Verificação de saúde com `ansible.builtin.uri` (`until` + `retries` + `delay`) antes de devolver o nó; a falha interrompe o play (com `serial: 1`, o primeiro nó doente já encerra a atualização). O nó doente fica fora (`MAINT`); o outro continua em rotação na versão antiga. O verificador roda a versão 3 doente e confere exatamente isso, sem falhas de requisição.

---

*Os desafios 10 a 12 serão acrescentados na próxima fase.*
