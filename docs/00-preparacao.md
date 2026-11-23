# Preparação do ambiente

Este guia leva você de "computador sem Docker" até `lab up` funcionando. Faça **antes** do primeiro encontro:
a construção das imagens baixa algumas centenas de megabytes e leva alguns minutos.

**Resumo do que você precisa:** Docker com Compose v2, ~4 GB de memória para o Docker, ~5 GB de disco livre, internet na primeira vez (ou o arquivo de imagens do instrutor, veja [Sem internet](#sem-internet-lab-save-e-lab-load)).

---

## 1. Instalar o Docker

### Windows 10/11 (WSL2 + Docker Desktop)

1. **Habilite o WSL2.** Em um PowerShell **como administrador**:
   ```powershell
   wsl --install
   ```
   Reinicie quando solicitado. Confirme com `wsl --status` (a versão padrão deve ser 2).
2. **Instale o Docker Desktop** ([docs.docker.com/desktop/setup/install/windows-install](https://docs.docker.com/desktop/setup/install/windows-install/)) e, na instalação, mantenha marcada a opção **Use WSL 2 instead of Hyper-V**.
3. **Abra o Docker Desktop** e espere o ícone indicar que o motor está rodando.
4. **Dê memória suficiente ao WSL2.** Por padrão o WSL2 usa metade da RAM, o que costuma bastar. Se `lab doctor` reclamar de memória, crie o arquivo `C:\Users\<seu usuário>\.wslconfig`:
   ```ini
   [wsl2]
   memory=6GB
   ```
   e rode `wsl --shutdown` (depois reabra o Docker Desktop).
5. **Teste** em um PowerShell: `docker version` e `docker compose version`.

> **Licença:** o Docker Desktop exige assinatura paga em empresas grandes. A alternativa gratuita é instalar o **Docker Engine dentro do WSL2** (veja a seção Linux, executada dentro da distribuição Ubuntu do WSL) e usar o comando `./lab` pelo terminal do WSL. O laboratório funciona igual.

**Onde guardar o repositório:**

- Com **Docker Desktop**: pode ficar em qualquer pasta do Windows (`C:\Projetos\...`). Prefira um caminho **sem espaços e sem acentos**.
- Com **Docker Engine no WSL2**: guarde o repositório **dentro do WSL** (`~/ansible-lab-tre-se`), não em `/mnt/c/...` (mais rápido e com permissões corretas). Para editar com um editor do Windows, abra `\\wsl$\Ubuntu\home\<usuário>\ansible-lab-tre-se`.

**Scripts no Windows:**

- Use **`.\lab.ps1`** no PowerShell. Se aparecer *"a execução de scripts foi desabilitada"*:
  ```powershell
  powershell -ExecutionPolicy Bypass -File .\lab.ps1 doctor
  ```
  ou, só para a sessão atual: `Set-ExecutionPolicy -Scope Process Bypass`.
- Se você usa o **Git Bash**, o `./lab` funciona, mas `lab shell` só abre terminal interativo se o `winpty` estiver disponível (vem com o Git para Windows). Na dúvida, use o PowerShell.
- **Se você clonou o repositório com Git**, o fim de linha precisa ser LF. O repositório já traz um `.gitattributes` que cuida disso. Se `lab doctor` acusar CRLF, rode:
  ```powershell
  git config core.autocrlf false
  git rm --cached -r -q .
  git reset --hard
  ```

### Linux (Ubuntu, Debian, Fedora, Rocky...)

Instale o **Docker Engine** e o plugin **Compose v2** seguindo a documentação oficial da sua distribuição
([docs.docker.com/engine/install](https://docs.docker.com/engine/install/)). Depois:

```bash
sudo usermod -aG docker "$USER"   # permite usar docker sem sudo
newgrp docker                     # ou saia e entre na sessão de novo
docker compose version            # precisa ser v2.x
```

Observações:

- **cgroup v2** é necessário (padrão em Ubuntu 22.04+, Debian 11+, Fedora 31+, Rocky/RHEL 9). Confira com `stat -fc %T /sys/fs/cgroup` (deve mostrar `cgroup2fs`).
- **SELinux (Fedora, RHEL, Rocky):** a montagem de `desafios/` já usa o rótulo `:z`, que ajusta o contexto da pasta. Não é preciso fazer nada.
- **Permissões:** o usuário `aluno` do nó de controle ajusta o seu uid ao dono da pasta `desafios/`, então você consegue editar os arquivos tanto no editor do host quanto dentro do contêiner.
- Docker em modo **rootless** ou **Podman** não foram validados com este laboratório (os nós usam systemd e contêineres privilegiados).

### macOS (Intel e Apple Silicon)

1. Instale o **Docker Desktop** ([docs.docker.com/desktop/setup/install/mac-install](https://docs.docker.com/desktop/setup/install/mac-install/)) para o seu chip (Apple Silicon ou Intel).
2. Abra o Docker Desktop e espere o motor iniciar.
3. Em **Settings → Resources**, deixe pelo menos 4 GB de memória.
4. Teste: `docker version` e `docker compose version`.

As imagens do laboratório são construídas para `amd64` e `arm64`: no Apple Silicon elas rodam nativamente, sem emulação.

---

## 2. Primeiro uso

Na pasta do repositório:

```bash
./lab doctor     # Windows: .\lab.ps1 doctor
./lab up
./lab shell
```

Dentro do nó de controle:

```bash
ansible --version
ssh web1 hostname        # entra no nó web1 sem senha e mostra o nome
```

Para sair do nó de controle: `exit`. Para desligar tudo: `lab down` (suas chaves e seus arquivos são mantidos).

---

## 3. Rede corporativa

### Atrás de um proxy

O `lab build` repassa as variáveis de proxy do seu ambiente ao build. Defina-as **antes** de rodar `lab up` ou `lab build`:

```bash
# Linux / macOS / WSL2
export HTTP_PROXY=http://proxy.exemplo.local:3128
export HTTPS_PROXY=http://proxy.exemplo.local:3128
export NO_PROXY=localhost,127.0.0.1
./lab build
```

```powershell
# Windows (PowerShell)
$env:HTTP_PROXY  = 'http://proxy.exemplo.local:3128'
$env:HTTPS_PROXY = 'http://proxy.exemplo.local:3128'
$env:NO_PROXY    = 'localhost,127.0.0.1'
.\lab.ps1 build
```

O Docker **Desktop** também precisa conhecer o proxy para baixar as imagens-base: *Settings → Resources → Proxies*.

### Proxy com inspeção TLS (erro de certificado)

Se o build falhar com `SSL certificate problem` ou `self-signed certificate in certificate chain`, copie o certificado da CA corporativa (PEM, extensão `.crt`) para `docker/certs/` e rode `lab build` de novo. Veja `docker/certs/README.md`.

### Sem internet (`lab save` e `lab load`)

Depois de construídas, as imagens contêm tudo de que os desafios precisam: **o laboratório funciona sem internet**. Para distribuir sem que cada aluno precise construir:

```bash
# Na máquina do instrutor (que já fez lab up):
./lab save                     # gera ansible-lab-imagens.tar

# Na máquina do aluno, com o repositório e o arquivo .tar:
./lab load ansible-lab-imagens.tar
./lab up                       # não precisa de internet
```

---

## 4. Solução de problemas

Comece sempre por **`lab doctor`**: ele detecta a maioria dos problemas abaixo.

| Sintoma | Causa provável | O que fazer |
|---|---|---|
| `docker: command not found` / "Docker não encontrado" | Docker não instalado, ou no WSL sem integração | Instale conforme a seção 1. No Docker Desktop: *Settings → Resources → WSL integration* e marque a sua distribuição. |
| "O serviço do Docker não responde" | Docker Desktop fechado | Abra o Docker Desktop e espere o motor iniciar (ícone verde). |
| `lab up` trava ou falha no build com erro de rede | Sem internet ou proxy | Veja a seção 3. |
| `port is already allocated` / "porta 8080 em uso" | Outro programa usa a 8080 | Crie `docker/lab.local.env` com `LAB_LB_PORT=9090` e rode `lab up` de novo. |
| `lab doctor` acusa CRLF | Git converteu fim de linha no Windows | Comandos de correção na seção 1 (Windows). |
| Nó "não respondeu por SSH" após 2 minutos | Nós ainda iniciando, pouca memória, ou cgroup v1 | Rode `lab status`. Aumente a memória do Docker/WSL2. Depois `lab down` e `lab up`. |
| `Permission denied` ao salvar arquivo em `desafios/` (Linux) | Pasta pertence a outro usuário | O nó de controle ajusta o uid ao dono de `desafios/`. Rode `lab down` e `lab up` de novo; confira com `ls -ld desafios`. |
| Ansible avisa *"world writable directory, ignoring ansible.cfg"* | Você rodou o Ansible fora do `lab shell` ou com `ANSIBLE_CONFIG` alterada | Use `lab shell` (ele define `ANSIBLE_CONFIG` para o `ansible.cfg` do desafio em que você está). |
| `lab shell` no Git Bash: "the input device is not a TTY" | O mintty não é um TTY real para o docker.exe | Use o PowerShell (`.\lab.ps1 shell`) ou o terminal do WSL. |
| `WARNING: ... host key ... changed` ao usar `ssh` à mão | Os nós foram recriados | No nó de controle isso é desativado para `web1 web2 db1 lb1`. Não ocorre com `ssh web1`. |
| Quero começar do zero (inclusive chaves) | — | `lab down -v` e depois `lab up`. Seus arquivos em `desafios/` continuam intactos. |

---

## 5. Como o ambiente funciona (para diagnóstico)

Não é preciso saber isto para fazer os desafios, mas ajuda a entender o que está rodando.

- **`control`:** Debian 13 com Python 3.13, `ansible-core` 2.21, `ansible-lint`, `yamllint` e as collections `ansible.posix` e `community.general`, todos com versão fixada. Usuário `aluno`; pasta de trabalho `/lab` (é a pasta `desafios/` do repositório).
- **Nós gerenciados:** Rocky Linux 9 (`web1`, `web2`, `lb1`, Python 3.9) e Debian 12 (`db1`, Python 3.11), cada um com **systemd como PID 1** e `sshd`. Entrada apenas por chave SSH, com o usuário `ansible` (sudo sem senha). Nenhuma senha padrão existe.
- **Chaves SSH:** geradas no primeiro `lab up` e guardadas em volumes Docker (**nunca** no repositório). A chave privada fica em `~/.ssh` do usuário `aluno`, com modo 600, **fora** de `/lab` — por isso o SSH a aceita mesmo quando `/lab` aparece com permissão 777 no Windows.
- **`ANSIBLE_CONFIG`:** o Ansible ignora um `ansible.cfg` em pasta gravável por todos (é o caso de `/lab` no Windows). O contêiner define `ANSIBLE_CONFIG` explicitamente, e o prompt a atualiza para o `ansible.cfg` do desafio em que você está.
- **systemd em contêiner** (validado em cgroup v2, Docker Desktop/WSL2). Cada nó usa:
  - `privileged: true`, para o systemd poder gerenciar a própria árvore de cgroup;
  - `cgroup: host` e `/sys/fs/cgroup` montado com leitura e escrita;
  - `tmpfs` em `/run`, `/run/lock` e `/tmp`;
  - `stop_signal: SIGRTMIN+3`, o sinal com que o systemd desliga de forma limpa;
  - unidades inúteis em contêiner mascaradas (udev, getty, montagens do kernel, sysctl, timers do apt/dnf).
- **Por isso os desafios não usam** chrony/NTP (o contêiner privilegiado compartilha o relógio do host), firewalld, SELinux, sysctl nem módulos de kernel.
- **Segurança:** contêineres privilegiados dão ao conteúdo deles acesso amplo ao host. Isto é aceitável em um laboratório local e descartável; **não** reutilize esta configuração em produção.
