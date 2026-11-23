# Desafio 04 — Variáveis, facts e precedência

| | |
|---|---|
| **Dia do curso** | Dia 2 — Playbooks em profundidade (24/11) |
| **Missão essencial** | ~25 minutos |
| **Conceitos** | `group_vars`, `host_vars`, facts, `os_family`, precedência de variáveis, `-e` |
| **Pasta de trabalho** | `/lab/04-variaveis-facts` (no nó de controle) |

---

## Teoria

### Um playbook, vários sistemas

No desafio anterior o mesmo playbook valia para Rocky e Debian porque os módulos usados (`file`, `user`, `copy`) escondem as diferenças. Mas nem tudo é igual: o pacote que instala o servidor web é `httpd` na família Red Hat e `apache2` na Debian; o serviço do SSH é `sshd` em uma e `ssh` na outra. A tentação é escrever duas tasks, cada uma com um `when` por distribuição. Funciona, mas dobra o que há para manter.

A alternativa é separar **regra** de **dado**: a task é uma só, e o **nome** vem de uma variável.

### Facts: o que o Ansible descobre sozinho

Antes das tasks, o Ansible roda o módulo `ansible.builtin.setup` e guarda o resultado em **facts**: distribuição, versão, memória, interfaces de rede... Eles ficam em `ansible_facts`. O fact `os_family` agrupa as distribuições (`RedHat` para Rocky, Alma ou RHEL; `Debian` para Debian ou Ubuntu). Veja todos com `ansible <host> -m ansible.builtin.setup`, e filtre com `-a 'filter=ansible_os_family'`.

### Onde moram os valores

Variáveis podem viver em muitos lugares. As três camadas que você mais usa vivem ao lado do inventário:

```text
inventario/
├── hosts.yml
├── group_vars/
│   ├── all.yml        # vale para todos
│   └── bd.yml         # vale para o grupo "bd"
└── host_vars/
    └── bd02.yml       # vale só para o host bd02
```

Um exemplo em outro cenário: o serviço do SSH tem nome diferente por família, e a task consulta um dicionário usando o fact como chave.

```yaml
# group_vars/all.yml
servico_ssh:
  RedHat: sshd
  Debian: ssh

# na task
- name: Garantir o SSH ativo
  ansible.builtin.service:
    name: "{{ servico_ssh[ansible_facts['os_family']] }}"
    state: started
```

Outra forma é um arquivo de variáveis por família, carregado com `vars_files` ou `include_vars`, usando o fact no nome do arquivo. Qual escolher é decisão de desenho.

### Precedência: quem vence quando há conflito

Se a mesma variável aparece em mais de um lugar, **um valor vence**. Há uma ordem fixa (são 22 níveis na documentação), mas quatro regras resolvem a maioria dos casos:

1. `group_vars/all` perde para um grupo específico, que perde para `host_vars`: **quanto mais específico, mais forte**.
2. Se um host está em **dois grupos do mesmo nível** com valores diferentes, os grupos são mesclados em **ordem alfabética** e o **último** vence. Sim, é arbitrário, e é por isso que se evita depender disso (ou se usa `ansible_group_priority`).
3. Variáveis do play (`vars:`) vencem as do inventário.
4. `-e` (extra vars) **vence tudo**.

Para ver o valor final de uma variável, sem rodar nenhuma task:

```bash
ansible-inventory -i inventario --host bd02          # variáveis do inventário daquele host
ansible -i inventario bd02 -m ansible.builtin.debug -a 'var=nome_da_variavel'
```

O hábito mais valioso: **prever antes de provar**. Quem confere o resultado sem ter previsto não aprende nada com um acerto, e aprende pouco com um erro.

---

## Cenário

A auditoria do **Órgão Exemplo** quer uma **ficha** em cada servidor do ambiente de homologação: um arquivo curto que diz quem é o servidor, em que ambiente está e por quanto tempo seus registros são mantidos. Aproveitando a visita, a equipe quer que todos os servidores tenham as **ferramentas de diagnóstico de DNS** (`dig` e companhia) instaladas.

Os quatro nós (`web1`, `web2`, `db1`, `lb1`) são dois sistemas diferentes, mas o órgão exige **um único playbook**. O inventário já está pronto em `inventario/`. Os valores (ambiente, retenção, nomes de pacote) **mudam com o tempo** e quem os altera não é quem mantém o playbook.

## Missão essencial

### Parte A: o playbook `site.yml`

Escreva o playbook **`site.yml`** (nesta pasta) de modo que, em **todos os nós**, ao final:

1. As ferramentas de diagnóstico de DNS estejam instaladas e o comando `dig` funcione. O pacote se chama **`bind-utils`** na família Red Hat e **`dnsutils`** na família Debian.
2. Exista o arquivo `/etc/ficha-servidor` (dono `root:root`, modo `0644`) com **estas cinco linhas** (a ordem não importa):

   ```text
   host=<nome do host, como no inventário>
   familia=<família do sistema, como o Ansible a conhece>
   ambiente=homologacao
   retencao_dias=30
   pacote_dns=<nome do pacote que foi instalado naquele nó>
   ```

3. Exceção por host: em **`db1`**, a retenção é **90** dias (`retencao_dias=90`); nos demais, 30.
4. A organização atenda à regra do órgão: os **valores** (ambiente, retenção, nomes de pacote por família) ficam em **`group_vars/`** e **`host_vars/`**, **não** escritos dentro do `site.yml`. Existe **uma só** sequência de tasks para as duas famílias, **sem `when`** por distribuição ou família.
5. O playbook é **idempotente**: a segunda execução termina com `changed=0`.

### Parte B: preveja, depois prove

Na pasta `conflitos/` há um **mini-inventário só para este exercício**, com variáveis em várias camadas. Leia os arquivos dele e **responda as três questões abaixo ANTES de rodar qualquer comando**. Depois prove cada uma com o Ansible de verdade.

1. No host **`web1`**, qual é o valor de `retencao_dias`?
2. No host **`web1`**, qual é o valor de `nivel_log`? (Repare nos grupos a que `web1` pertence.)
3. No host **`db1`**, qual é o valor de `ambiente` quando o Ansible é executado com **`-e ambiente=teste`**?

Registre no arquivo **`previsoes.txt`** (já existe, com o modelo) uma linha por questão, no formato `questão;previsão;observado`. A **previsão** é o que você achava antes; o **observado** é o que o Ansible mostrou. Errar a previsão não reprova: **o que o verificador confere é se o valor observado é o verdadeiro**.

## Critérios de aceite

- [ ] `site.yml` existe.
- [ ] `site.yml` passa na checagem de sintaxe.
- [ ] Todas as tasks têm `name`.
- [ ] Todos os módulos usam o nome completo (FQCN).
- [ ] Nenhuma task usa `when` para separar distribuição ou família.
- [ ] Os nomes dos pacotes não estão escritos no `site.yml`.
- [ ] Existe ao menos um arquivo em `group_vars/` (ao lado do inventário ou do playbook).
- [ ] Existe ao menos um arquivo em `host_vars/` de um host do inventário (a exceção por host).
- [ ] O playbook executa sem erros nos 4 nós a partir do estado inicial (o verificador desinstala os pacotes e apaga a ficha antes de rodá-lo).
- [ ] A segunda rodada termina com `changed=0`.
- [ ] O pacote certo de cada família está instalado e o `dig` funciona, nos 4 nós.
- [ ] `/etc/ficha-servidor`: dono, modo, e as linhas `host`, `familia`, `ambiente` e `pacote_dns`, nos 4 nós.
- [ ] `retencao_dias` vale 30 em `web1`, `web2` e `lb1`, e 90 em `db1`.
- [ ] `previsoes.txt` tem as três questões com previsão e observado preenchidos.
- [ ] Os três valores observados conferem com o que o Ansible realmente usa.

## Antes de começar

1. No terminal do seu computador: `lab start 04`.
2. Preencha o **`DESENHO.md`** desta pasta **antes** de escrever qualquer YAML.
3. No nó de controle (`lab shell`): `cd /lab/04-variaveis-facts`.

## Como verificar

```bash
lab verify 04
```

Para a sua própria conferência: `ansible-playbook site.yml --check --diff`, e uma segunda execução que deve mostrar `changed=0`. Para inspecionar variáveis sem tocar nos nós, use `ansible-inventory --host <host>` e o módulo `ansible.builtin.debug`.

## Dicas

<details>
<summary>Dica 1 — conceitual</summary>

Separe **o que muda** de **o que é regra**. A regra é "instalar o pacote de DNS e gravar a ficha". O que muda é o **nome** do pacote (depende da família), o ambiente e a retenção (dependem de quem manda). Para cada valor, pergunte: "se isso mudar amanhã, em quantos arquivos eu mexo?"

E como o Ansible descobre a família de cada nó sem você dizer? Rode o módulo que coleta fatos em um nó Rocky e em `db1` e compare.

</details>

<details>
<summary>Dica 2 — mais direta</summary>

- Um fact da família do sistema resolve o nome do pacote. Ele pode ser usado como **chave de um dicionário** ou como **parte do nome de um arquivo** de variáveis. Os dois caminhos são válidos.
- Valores que valem para todos moram em `group_vars/all` (ou no grupo do ambiente). A exceção de `db1` mora onde só `db1` enxerga.
- Antes de gravar a ficha, rode `ansible-inventory -i inventario --host db1`: o valor que você vê ali é o que o play enxerga.
- Para a Parte B: `ansible -i conflitos/inventario <host> -m ansible.builtin.debug -a 'var=<variável>'`. E o `-e` entra como em qualquer comando do Ansible.

</details>

<details>
<summary>Dica 3 — o módulo e o parâmetro</summary>

- Pacotes: `ansible.builtin.package` aceita o mesmo `name` em qualquer família (ele delega ao `dnf` ou ao `apt`). Alternativa: um módulo por família, com a variável escolhendo o nome.
- Fact: `ansible_facts['os_family']` (valores `RedHat` e `Debian`).
- Arquivo: `ansible.builtin.copy` com `content`, `dest`, `owner`, `group` e `mode`. Uma linha por variável, escrita com Jinja: `chave={{ variavel }}`.
- Nome do host como o inventário o conhece: `inventory_hostname`.
- Arquivo de variáveis escolhido por fact: `vars_files` ou `ansible.builtin.include_vars`.
- `ansible-doc ansible.builtin.package` e `ansible-doc ansible.builtin.include_vars`.

</details>

## Perguntas de reflexão

1. O `db1` ganhou uma exceção em `host_vars`. Daqui a seis meses, alguém acha estranho que só ele guarde 90 dias. **Onde essa justificativa deveria estar registrada**, para não se perder?
2. Dois grupos do mesmo nível com valores diferentes para a mesma variável: o vencedor é decidido pela **ordem alfabética dos nomes**. O que você faria no desenho do inventário para **não depender** disso?
3. Quando vale a pena usar `-e` em produção, sabendo que ele vence todas as outras camadas? Que risco isso traz?

## Extensão opcional

**Fato local.** Faça cada nó guardar um *fact personalizado*: um arquivo `/etc/ansible/facts.d/ficha.fact`, em formato INI, com a seção `[dados]` e a chave `responsavel=infra`. Depois, acrescente à ficha a linha `responsavel=infra`, **lida do fato** (não digitada de novo). Ao rodar `lab verify 04`, uma seção extra confere o arquivo `.fact` e a linha na ficha (não conta para o resultado da missão).

## Para saber mais

```bash
ansible-doc ansible.builtin.setup
ansible-doc ansible.builtin.package
ansible-doc ansible.builtin.include_vars
ansible-doc -t keyword -l | grep -i vars
```

- [Usando variáveis](https://docs.ansible.com/ansible/latest/playbook_guide/playbooks_variables.html)
- [Precedência de variáveis: o que vence?](https://docs.ansible.com/ansible/latest/playbook_guide/playbooks_variables.html#understanding-variable-precedence)
- [Descobrindo variáveis: facts e fatos locais](https://docs.ansible.com/ansible/latest/playbook_guide/playbooks_vars_facts.html)
