# Desafio 01 — Inventário e primeiro contato

| | |
|---|---|
| **Dia do curso** | Dia 1 — Fundamentos (23/11) |
| **Missão essencial** | ~15 minutos |
| **Conceitos** | inventário, grupos, grupos de grupos, padrões de hosts, comandos ad-hoc, `ansible-inventory`, `ansible-doc` |
| **Pasta de trabalho** | `/lab/01-inventario` (no nó de controle) |

---

## Teoria

### O que é um inventário

O Ansible só age sobre as máquinas que conhece. O **inventário** é a lista dos alvos (*hosts*) e de como eles estão agrupados. Ele pode ser estático (um arquivo INI ou YAML) ou dinâmico (gerado por um plugin que consulta a nuvem, um CMDB, etc.). Aqui usamos YAML estático.

Um **grupo** é um rótulo que reúne hosts. Um host pode ter vários rótulos. Um **grupo de grupos** (chave `children`) não tem hosts próprios: ele aponta para outros grupos e herda os hosts deles. Todo host pertence ao grupo especial `all`; quem não tem grupo algum cai em `ungrouped`.

Exemplo, em um cenário **diferente** do desta missão — as estações de um laboratório didático:

```yaml
all:
  children:
    sala101:
      hosts:
        pc01:
        pc02:
    sala102:
      hosts:
        pc03:
          ansible_host: 192.0.2.13   # o nome é pc03, mas a conexão vai a este endereço
    andar1:
      children:          # grupo de grupos: reúne sala101 e sala102
        sala101:
        sala102:
```

`ansible_host` é uma **variável de inventário**: ela muda como o Ansible alcança aquele host, sem mudar o nome pelo qual você o chama.

### Padrões de hosts

Na linha de comando você escolhe os alvos com um *padrão*:

| Padrão | Seleciona |
|---|---|
| `pc01` | um host |
| `sala101:sala102` | união de dois grupos |
| `andar1:!sala102` | o grupo `andar1`, exceto quem está em `sala102` |
| `andar1:&sala101` | interseção: quem está nos dois |
| `pc*` | curinga no nome |
| `sala101[0]` | o primeiro host do grupo (índices e fatias) |

### Comandos ad-hoc

Um comando **ad-hoc** executa um único módulo, sem escrever playbook:

```bash
ansible sala101 -m ansible.builtin.ping
ansible andar1:!sala102 -m ansible.builtin.setup -a "filter=ansible_kernel"
```

`-m` escolhe o módulo e `-a` passa os argumentos. O módulo `setup` coleta **fatos** (*facts*): informações do sistema do alvo, como kernel, distribuição, memória e rede. Para saber o que um módulo faz e quais parâmetros aceita, use `ansible-doc`.

### O que acontece por baixo

Quando você roda um ad-hoc, o Ansible: (1) lê o inventário e resolve o padrão em uma lista de hosts; (2) abre uma conexão SSH com cada um, usando o usuário e a chave da configuração; (3) copia um pequeno programa Python — o módulo — para um diretório temporário no alvo; (4) executa esse programa com o Python **do alvo**; (5) lê o resultado, em JSON, de volta; (6) apaga o temporário. Por isso o alvo só precisa de **SSH e Python**: não há agente instalado. E por isso o `ping` do Ansible não é um ping ICMP: ele prova que a conexão, a autenticação e o Python do alvo funcionam.

### Ferramentas de inspeção

- `ansible-inventory -i inventario --graph` mostra a árvore de grupos como o Ansible a enxerga.
- `ansible-inventory -i inventario --list` mostra tudo, em JSON. `--host NOME` mostra as variáveis de um host.
- `ansible PADRÃO --list-hosts` mostra quem um padrão seleciona, sem conectar em ninguém.

---

## Cenário

A Secretaria de TI do **Órgão Exemplo** recebeu quatro servidores de um novo ambiente de homologação do sistema fictício *Protocolo Digital*: dois servidores web, um banco de dados e um balanceador. Antes de qualquer automação, a equipe precisa de duas coisas: um **inventário** que represente esse ambiente com fidelidade e um **levantamento** do que cada servidor realmente é. O levantamento será anexado ao chamado de recebimento.

Os servidores se chamam `web1`, `web2`, `db1` e `lb1`, e o nó de controle os alcança pelo nome.

## Missão essencial

Ao final, precisa ser verdade que:

1. Existe um inventário na pasta `inventario/` em que:
   - o grupo `web` contém exatamente `web1` e `web2`;
   - o grupo `db` contém exatamente `db1`;
   - o grupo `lb` contém exatamente `lb1`;
   - existe um **grupo de grupos que representa o ambiente** (você escolhe o nome) e que reúne `web`, `db` e `lb`;
   - nenhum host ficou fora de grupo.
2. O Ansible alcança todos os nós **pelo grupo correto**.
3. O arquivo `respostas.txt`, na pasta do desafio, é o **levantamento** dos servidores. Nada é alocado nem dividido aqui: você apenas **descobre e anota** o que cada nó já tem. Para cada um dos 4 nós, registre:
   - a **distribuição** do sistema operacional (por exemplo, `Rocky` ou `Debian`);
   - a **memória RAM total** que o nó reporta, em **MB**, no valor inteiro que o próprio Ansible informa (sem converter, somar nem dividir entre os servidores).

   Os dois valores devem ser descobertos **com comandos ad-hoc** do Ansible. Formato: uma linha por nó, campos separados por `;`:

   ```text
   host;distribuicao;memoria_mb
   ```

   Exemplo do formato, com um host do cenário da teoria (não é nenhum dos seus): `pc01;Ubuntu;7843`

   O `respostas.txt` já vem com linhas de partida (`Ubuntu;2048`) apenas para mostrar o formato: **são valores de exemplo, não as respostas**. Substitua cada linha pelo que você descobriu.

## Critérios de aceite

O verificador confere, nesta ordem:

- [ ] O inventário em `inventario/` é lido sem erro pelo `ansible-inventory`.
- [ ] Grupo `web` com exatamente `web1` e `web2`.
- [ ] Grupo `db` com exatamente `db1`.
- [ ] Grupo `lb` com exatamente `lb1`.
- [ ] Existe um grupo de grupos que reúne `web`, `db` e `lb`.
- [ ] Nenhum host está fora dos grupos.
- [ ] O grupo `web` responde ao ping.
- [ ] O grupo `db` responde ao ping.
- [ ] O grupo `lb` responde ao ping.
- [ ] `respostas.txt` tem uma linha para cada um dos 4 nós, no formato esperado.
- [ ] A distribuição registrada confere em todos os nós.
- [ ] A memória total registrada (MB) confere com a que cada nó reporta, em todos os nós.

## Antes de começar

1. No seu terminal do computador, na pasta do repositório: `lab start 01`.
2. Abra o arquivo **`DESENHO.md`** desta pasta e responda as cinco perguntas **antes** de escrever qualquer YAML.
3. Abra o terminal do nó de controle (`lab shell`) e entre na pasta do desafio: `cd /lab/01-inventario`.

## Como levantar os dados do `respostas.txt` no `lab shell`

Tudo isto acontece **dentro do nó de controle** (`lab shell`), na pasta do desafio, **depois** de o inventário estar funcionando (`ansible-inventory -i inventario --graph` mostrando a árvore certa):

1. **Pergunte aos nós, não ao seu computador.** Os valores que valem são os que **cada servidor reporta**. Use um comando **ad-hoc** (`ansible <alvo> -m <módulo> -a '<argumentos>'`, como na teoria), escolhendo como alvo o grupo do ambiente (ou `all`) para ter os 4 nós de uma vez. O módulo que coleta informações do sistema é o `ansible.builtin.setup`; o parâmetro `filter` restringe a saída ao fato que você quer. Os nomes dos dois fatos estão na Dica 3, e você pode rodar sem filtro em um só host para vê-los todos.
2. **Leia a saída.** O Ansible mostra um bloco por host, com o nome do host no topo e o valor do fato dentro de `ansible_facts`. Cada nó pode ter um valor diferente: anote o de **cada um**, ao lado do nome do host, como ele aparece no inventário.
3. **Anote no arquivo.** Edite o `respostas.txt` com `nano respostas.txt` (ou `vim`) e deixe **uma linha por nó**, no formato `host;distribuicao;memoria_mb`. Salve com `Ctrl+O`, `Enter`, e saia com `Ctrl+X` no `nano`. O arquivo está na mesma pasta do inventário, e por isso aparece também no seu computador, em `desafios/01-inventario/`.
4. **Confira.** Rode `lab verify 01` no seu computador. Se a distribuição ou a memória de algum nó não bater, o verificador diz **qual nó** está errado (e, no caso da memória, quanto o nó reporta).

## Como verificar

```bash
lab verify 01
```

Cada linha começa com ✔ (atendido) ou ✘ (não atendido). Quando algo está errado, o verificador diz **o que encontrou e o que esperava** — descobrir o porquê e como resolver é a sua parte.

## Dicas

Use uma de cada vez. Tente por uns minutos antes de abrir a próxima.

<details>
<summary>Dica 1 — conceitual</summary>

Pense no inventário em duas camadas: **quem são os hosts** e **quais rótulos cada um carrega**. O grupo do ambiente não tem hosts próprios: ele só aponta para outros grupos. Olhe o exemplo da teoria: que chave do YAML expressa "este grupo contém estes grupos"?

Para os fatos, pergunte-se: qual comando coleta informações de um sistema, e como descobrir o nome do fato que traz a distribuição e o que traz a memória?

</details>

<details>
<summary>Dica 2 — mais direta</summary>

Rode `ansible-inventory -i inventario --graph`: se a árvore não bate com o seu desenho, o problema está no inventário, não na conexão. Corrija a árvore antes de testar o ping.

Para os fatos, rode **uma vez** o módulo que coleta fatos, sem filtro, em um só host, e leia a saída. Procure por "distribution" e por "memtotal". Depois, restrinja a coleta ao que interessa e rode no grupo todo (`all`, ou o grupo do ambiente).

</details>

<details>
<summary>Dica 3 — o módulo e o parâmetro</summary>

- Inventário em YAML: `children:` dentro de um grupo lista os grupos filhos.
- Ad-hoc: `ansible <alvo> -m ansible.builtin.setup -a 'filter=<fato>'`.
- Fatos úteis: `ansible_distribution` e `ansible_memtotal_mb`.
- `ansible-doc ansible.builtin.setup` explica o parâmetro `filter`.

</details>

## Perguntas de reflexão

1. **E se fossem 400 servidores?** Você escreveria os 400 nomes à mão? Que recursos do inventário (faixas de nomes, plugins, inventário dinâmico) ajudariam?
2. **Onde deveria morar a informação "este servidor é de homologação"?** No nome do host, em um grupo, em uma variável? O que muda quando existirem homologação *e* produção?
3. Um host pode pertencer a dois grupos. Se os dois grupos definirem valores diferentes para a mesma variável, quem deveria vencer? (Vamos responder isso no Dia 2.)

## Extensão opcional

**Padrões de hosts.** Crie o arquivo `padroes.txt` nesta pasta, com quatro linhas no formato `N: padrão`. Cada linha deve conter o **padrão de hosts** (o que vai depois de `ansible`) que seleciona:

1. todos os hosts, **menos** os do grupo `web`;
2. somente o **último** host do grupo `web`;
3. os hosts de `web` e de `lb`, **exceto** `web1`;
4. todos os hosts cujo **nome termina em `1`**.

Exemplo do formato, em outro cenário: `1: sala101:sala102`

Você pode testar cada padrão sem conectar em ninguém: `ansible -i inventario '<padrão>' --list-hosts`. Ao rodar `lab verify 01`, uma seção extra confere cada linha (ela não conta para o resultado da missão).

## Para saber mais

```bash
ansible-doc -l | grep -i ping          # lista módulos cujo nome ou descrição contém "ping"
ansible-doc ansible.builtin.ping
ansible-doc ansible.builtin.setup
ansible-inventory --help
```

- [Como montar o seu inventário](https://docs.ansible.com/ansible/latest/inventory_guide/intro_inventory.html)
- [Padrões: escolhendo hosts e grupos](https://docs.ansible.com/ansible/latest/inventory_guide/intro_patterns.html)
- [Introdução aos comandos ad-hoc](https://docs.ansible.com/ansible/latest/command_guide/intro_adhoc.html)
