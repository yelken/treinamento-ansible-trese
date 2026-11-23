# Método: as cinco perguntas

Quem digita YAML antes de pensar costuma acabar com um playbook que "funciona na minha máquina" e que ninguém consegue explicar. O método deste curso é simples: **antes de escrever qualquer tarefa, responda cinco perguntas**. Cada desafio traz um arquivo `DESENHO.md` com elas; preencha-o antes de abrir o editor de playbook.

Ninguém corrige as suas respostas. O `lab verify` apenas avisa se o arquivo continuar em branco. O valor está em **pensar**, e em ter algo escrito para comparar com o resultado no fim.

> **Por que isso importa com IA por perto?** Para julgar uma solução que outra pessoa (ou uma IA) escreveu, você precisa saber **o que ela deveria fazer** e **como o resultado seria provado**. Essas respostas são o seu critério de revisão. Veja a seção "Como usar IA neste laboratório" no `README.md`.

## As cinco perguntas

| # | Pergunta | O que você escreve |
|---|---|---|
| 1 | **Estado desejado** | O que precisa ser **verdade** ao final, e **como você prova** isso (sem confiar no próprio playbook). |
| 2 | **Inventário** | Quem são os alvos, como estão agrupados, e quem **não** pode ser tocado. |
| 3 | **Variáveis** | O que muda entre hosts ou ambientes, e em qual camada cada valor mora. |
| 4 | **Estrutura** | Quais plays, tasks ou roles, em que ordem, e o que depende do quê. |
| 5 | **Risco** | O que pode dar errado, como validar **antes** de aplicar e como voltar atrás. |

### 1. Estado desejado

Descreva o **resultado**, não os passos. "Instalar o pacote e reiniciar" é um roteiro; "o pacote está instalado e o serviço está ativo" é um estado. Estados podem ser **verificados**; roteiros só podem ser seguidos.

Boas respostas têm **evidência**: o comando que mostra, em cada nó, que o estado é verdadeiro (`systemctl is-active`, `stat`, `ls -l`, `grep`). E dizem o que a **segunda execução** deve mostrar: `changed=0`.

### 2. Inventário

Em quais hosts o play age? Existe um grupo que já os representa, ou será preciso criá-lo? Quais hosts **não** fazem parte da mudança? Se um nó fora do alvo for alterado por engano, o desenho falhou, mesmo que o playbook "passe".

### 3. Variáveis

Separe o que é **regra** do que é **dado**. Se um valor muda entre ambientes (homologação e produção), entre grupos ou entre hosts, ele é dado e não deve ficar escrito dentro da task. Pergunte-se: "se este valor mudar amanhã, quantos arquivos eu preciso editar?" E: em qual camada ele mora (`defaults` do role, `group_vars`, `host_vars`, linha de comando) e por quê?

### 4. Estrutura

Quantos plays? Em que ordem as tasks precisam rodar, e **por quê** (qual depende de qual)? Algo precisa reagir a uma mudança (um handler)? O trecho vai se repetir em outros projetos (um role)? Desenhar a estrutura antes evita a task de 200 linhas que ninguém quer abrir.

### 5. Risco

- **Privilégio:** que acesso o play exige, e onde ele é declarado?
- **Alcance:** o que acontece se o `hosts:` estiver errado? Existe como limitar (`--limit`)?
- **Validação prévia:** `--syntax-check`, `--check --diff`, `ansible-lint`, `--list-hosts`.
- **Arquivos críticos:** existe um jeito de validar o conteúdo antes de gravar (`validate`)?
- **Reversão:** como voltar ao estado anterior? Existe backup? A mudança é reversível?

## Exemplo resolvido (fora dos desafios)

Cenário fictício: o **Órgão Exemplo** mantém o sistema *Fichário Digital* em três servidores de aplicação (`app01`, `app02`, `app03`) e um servidor de banco (`bd01`). Os logs da aplicação ficam em `/var/log/fichario/` e estão enchendo o disco. A equipe quer uma **política de rotação de logs** nos servidores de aplicação, e só neles.

> Este exemplo mostra o **raciocínio**, não um playbook. Um arquivo de rotação de logs e as tasks que o instalariam ficam como exercício para o dia em que você precisar disso: o método vale para qualquer problema.

### 1. Estado desejado

- Existe o arquivo `/etc/logrotate.d/fichario` nos três `app`, com dono `root:root` e modo `0644`, contendo a política: rotação diária, 14 arquivos mantidos, compressão ligada.
- A política **é válida** para o `logrotate` (ele não reclama ao ler o arquivo).
- **Como provo:** `ls -l /etc/logrotate.d/fichario` em cada nó; `logrotate -d /etc/logrotate.d/fichario` (modo de simulação) sem erros; `grep` pelas diretivas.
- Na **segunda execução**: `changed=0`.

### 2. Inventário

- Alvo: o grupo `app` (`app01`, `app02`, `app03`).
- **Não pode ser tocado:** `bd01` (grupo `bd`). Ele tem outro perfil de logs e outra equipe responsável.
- Se o grupo `app` ainda não existir no inventário, crio antes e confiro com `ansible-inventory --graph`.

### 3. Variáveis

- A quantidade de arquivos mantidos (14) e a frequência (diária) são **dados**: amanhã a auditoria pode pedir 30 dias. Não devem estar escritos no meio de uma task.
- Em produção talvez a retenção seja maior que em homologação: o valor deve morar numa camada que dependa do ambiente (por exemplo, `group_vars`), com um padrão sensato como ponto de partida.
- O caminho `/var/log/fichario/` é característica do sistema, não do ambiente: pode ser fixo.

### 4. Estrutura

- **Um play** com `hosts: app` e `become: true`, porque `/etc` exige administrador.
- Tarefas: (1) garantir que a ferramenta de rotação esteja presente, **se** ela não vier na imagem base; (2) gravar a política. A ordem importa: sem a ferramenta, o arquivo de política não tem quem o leia.
- Nada precisa reagir a mudança (o `logrotate` lê os arquivos quando roda), então **não preciso de handler**.
- Não vou virar role: é pequeno e específico. Se o padrão se repetir em outros sistemas, aí sim.

### 5. Risco

- Uma política de rotação errada pode **apagar logs que a auditoria exige**: isso não se desfaz. Antes de aplicar, confirmo com o responsável o prazo mínimo de retenção.
- Antes de rodar em todos os nós, rodo `--check --diff` e depois aplico com `--limit app01` (um nó) para observar.
- Se o conteúdo do arquivo tiver erro de sintaxe, o `logrotate` falha **silenciosamente na madrugada**. Por isso a validação com `logrotate -d` faz parte da prova do estado desejado.
- Reversão: guardo o arquivo anterior (se existir) antes da primeira aplicação.

Perceba o que aconteceu: ao terminar o desenho você ainda **não escreveu nenhuma linha de YAML** e já sabe **o que o playbook precisa provar**, **onde ele pode errar** e **o que ele não pode tocar**. Escrever as tasks passa a ser a parte fácil.

## Dicas para preencher o `DESENHO.md`

- **Respostas curtas e objetivas bastam.** Uma ou duas frases por pergunta. O arquivo é seu.
- Se travar na pergunta 1, tente completar a frase: "Terminei quando eu conseguir rodar ___ no nó e ver ___".
- Se travar na 3, pergunte: "se isso for diferente em produção, o que eu mudo?".
- Volte ao `DESENHO.md` quando o `lab verify` apontar um critério que falhou: muitas vezes a resposta já estava na pergunta 1.
- **Atualize o desenho se mudar de ideia.** Isso é normal e saudável; só não pule a etapa.
