# lab.ps1 - comando do Laboratório Ansible TRE-SE para Windows (PowerShell 5.1 ou 7+).
# Camada fina sobré `docker compose`; a lógica de verificação roda DENTRO do contêiner `control`.
# Uso: .\lab.ps1 <comando>      (rode .\lab.ps1 help para ver a lista)
#
# Este arquivo é UTF-8 com BOM (necessário para acentos no PowerShell 5.1).

$ErrorActionPreference = 'Continue'
$ProgressPreference = 'SilentlyContinue'
try {
    [Console]::OutputEncoding = [System.Text.Encoding]::UTF8
    $OutputEncoding = [System.Text.Encoding]::UTF8
} catch { }

$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $Root

# ---------------------------------------------------------------- configuracao
# docker/lab.env traz os padrões; docker/lab.local.env (opcional) sobrescreve;
# uma variável já definida no ambiente vence os dois.
$script:EnvFiles = @('--env-file', 'docker/lab.env')
function Import-LabEnv([string]$Path) {
    foreach ($line in Get-Content -LiteralPath $Path -Encoding UTF8) {
        $l = $line.Trim()
        if ($l -eq '' -or $l.StartsWith('#')) { continue }
        $i = $l.IndexOf('=')
        if ($i -lt 1) { continue }
        $k = $l.Substring(0, $i); $v = $l.Substring($i + 1)
        if (-not [Environment]::GetEnvironmentVariable($k)) { [Environment]::SetEnvironmentVariable($k, $v) }
    }
}
if (Test-Path docker/lab.local.env) {
    $script:EnvFiles += @('--env-file', 'docker/lab.local.env')
    Import-LabEnv docker/lab.local.env
}
Import-LabEnv docker/lab.env

$Tag = $env:LAB_TAG
$LbPort = $env:LAB_LB_PORT
$Images = @("ansible-lab/control:$Tag", "ansible-lab/rocky9:$Tag", "ansible-lab/debian12:$Tag")
$Nodes = @('web1', 'web2', 'db1', 'lb1')

# Cores do verificador dentro do contêiner: só quando o terminal entende ANSI.
$UseColor = if (($PSVersionTable.PSVersion.Major -ge 7) -or $env:WT_SESSION) { '1' } else { '0' }
if ($env:NO_COLOR) { $UseColor = '0' }

# ---------------------------------------------------------------- saída
function Write-Ok([string]$m)   { Write-Host '  ' -NoNewline; Write-Host ([string][char]0x2714) -ForegroundColor Green -NoNewline; Write-Host " $m" }
function Write-Bad([string]$m)  { Write-Host '  ' -NoNewline; Write-Host ([string][char]0x2718) -ForegroundColor Red -NoNewline; Write-Host " $m" }
function Write-Warn2([string]$m){ Write-Host '  ' -NoNewline; Write-Host '!' -ForegroundColor Yellow -NoNewline; Write-Host " $m" }
function Write-Info([string]$m) { Write-Host "==> $m" -ForegroundColor Cyan }
function Stop-Lab([string]$m)   { Write-Host ("$([char]0x2718) $m") -ForegroundColor Red; exit 1 }

# ---------------------------------------------------------------- docker compose
function Invoke-Dc {
    & docker compose @script:EnvFiles -f docker/compose.yml @args
}

function Test-DockerReady {
    if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
        Stop-Lab 'Docker não encontrado. Veja docs/00-preparacao.md (rode: .\lab.ps1 doctor).'
    }
    & docker info *> $null
    if ($LASTEXITCODE -ne 0) { Stop-Lab 'O Docker está instalado, mas o serviço não responde. Abra o Docker Desktop e tente de novo.' }
    & docker compose version *> $null
    if ($LASTEXITCODE -ne 0) { Stop-Lab "Docker Compose v2 não encontrado (comando 'docker compose'). Veja docs/00-preparacao.md." }
}

function Test-ImagesPresent {
    & docker image inspect @Images *> $null
    return ($LASTEXITCODE -eq 0)
}

function Test-ControlRunning {
    $id = Invoke-Dc ps --status running -q control 2>$null
    return [bool]$id
}
function Assert-Running {
    if (-not (Test-ControlRunning)) { Stop-Lab 'O laboratório não está no ar. Rode primeiro: .\lab.ps1 up' }
}

# Executa um comando no nó de controle como aluno, sem TTY (verificadores, scripts).
function Invoke-InControl {
    Invoke-Dc exec -T -u aluno -w /lab -e "FORCE_COLOR=$UseColor" control @args
}

function Assert-Nn($value, [string]$cmd) {
    if ($value -notmatch '^[0-9]{2}$') { Stop-Lab "Informe o número do desafio com dois dígitos. Exemplo: .\lab.ps1 $cmd 01" }
}

# ---------------------------------------------------------------- comandos
function Invoke-Build {
    Test-DockerReady
    Write-Info 'Construindo as imagens (a primeira vez leva alguns minutos)...'
    if ($env:HTTP_PROXY -or $env:HTTPS_PROXY) {
        $p = if ($env:HTTPS_PROXY) { $env:HTTPS_PROXY } else { $env:HTTP_PROXY }
        Write-Warn2 "Proxy detectado e repassado ao build: $p"
    }
    Invoke-Dc build @args
    if ($LASTEXITCODE -ne 0) { Stop-Lab 'Falha no build. Se a rede usa proxy ou inspeção TLS, veja docs/00-preparacao.md.' }
    Write-Ok 'Imagens prontas.'
}

function Wait-Nodes {
    Invoke-InControl /opt/lab/bin/lab-wait 120
    if ($LASTEXITCODE -ne 0) { Stop-Lab 'Algum nó não respondeu por SSH. Veja: .\lab.ps1 status' }
}

function Invoke-Up {
    Test-DockerReady
    if (-not (Test-ImagesPresent)) { Invoke-Build }
    Write-Info 'Subindo os 5 contêineres...'
    Invoke-Dc up -d
    if ($LASTEXITCODE -ne 0) { Stop-Lab 'Falha ao subir o laboratório. Rode .\lab.ps1 doctor para diagnosticar.' }
    Write-Info 'Preparando a chave SSH do laboratório...'
    Invoke-Dc exec -T -u root control /opt/lab/bin/lab-keygen
    if ($LASTEXITCODE -ne 0) { Stop-Lab 'Falha ao preparar a chave SSH.' }
    Write-Info 'Esperando os nós gerenciados responderem por SSH...'
    Wait-Nodes
    Write-Host ''
    Write-Ok 'Laboratório no ar.'
    Write-Host '   Entrar no nó de controle:  .\lab.ps1 shell'
    Write-Host "   Balanceador (desafio 09):  http://localhost:$LbPort"
}

function Invoke-Shell {
    Test-DockerReady; Assert-Running
    if ([Console]::IsInputRedirected -or [Console]::IsOutputRedirected) {
        Invoke-Dc exec -T -u aluno -w /lab control bash
    } else {
        Invoke-Dc exec -u aluno -w /lab control bash
    }
}

function Invoke-Verify($nn) {
    Assert-Nn $nn 'verify'
    Test-DockerReady; Assert-Running
    Invoke-InControl /opt/lab/bin/lab-verify $nn
    exit $LASTEXITCODE
}

function Invoke-RecreateNodes {
    Invoke-Dc up -d --force-recreate --no-deps @Nodes *> $null
    if ($LASTEXITCODE -ne 0) { Stop-Lab 'Falha ao recriar os nós gerenciados.' }
    # Conexões SSH persistentes (ControlPersist) apontariam para os nós antigos.
    Invoke-InControl bash -c 'ssh -O exit web1 web2 db1 lb1 >/dev/null 2>&1; rm -rf ~/.ansible/cp; true' *> $null
    Wait-Nodes
}

function Invoke-Reset {
    Test-DockerReady; Assert-Running
    Write-Info 'Recriando os nós gerenciados no estado inicial (seus arquivos em desafios/ não são tocados)...'
    Invoke-RecreateNodes
    Write-Ok 'Nós no estado inicial.'
}

function Invoke-Start($nn) {
    Assert-Nn $nn 'start'
    Test-DockerReady; Assert-Running
    Write-Info "Preparando o estado inicial do desafio $nn..."
    Invoke-RecreateNodes
    Invoke-InControl /opt/lab/bin/lab-start $nn
    if ($LASTEXITCODE -ne 0) { Stop-Lab "Falha ao preparar o desafio $nn." }
    Write-Ok "Desafio $nn pronto. Abra desafios\ e leia o README do desafio."
}

function Invoke-Status {
    Test-DockerReady
    Invoke-Dc ps -a --format 'table {{.Service}}\t{{.Status}}\t{{.Ports}}'
    if (Test-ControlRunning) {
        Write-Host ''
        Write-Info 'Ansible alcançando os nós:'
        Invoke-InControl /opt/lab/bin/lab-status
    }
}

function Invoke-Down {
    Test-DockerReady
    Write-Info 'Parando e removendo os contêineres...'
    Invoke-Dc down @args
}

function Invoke-Hint($nn) {
    Assert-Nn $nn 'hint'
    Test-DockerReady; Assert-Running
    Invoke-InControl /opt/lab/bin/lab-hint $nn @args
}

function Invoke-Exec {
    Test-DockerReady; Assert-Running
    if ($args.Count -eq 0) { Stop-Lab 'Informe o comando. Exemplo: .\lab.ps1 exec ansible --version' }
    Invoke-InControl @args
}

function Invoke-Save($file) {
    Test-DockerReady
    if (-not $file) { $file = 'ansible-lab-imagens.tar' }
    if (-not (Test-ImagesPresent)) { Stop-Lab 'As imagens ainda não existem. Rode .\lab.ps1 build (ou up) antes.' }
    Write-Info "Salvando as imagens em $file (pode levar um minuto)..."
    & docker save -o $file @Images
    if ($LASTEXITCODE -ne 0) { Stop-Lab 'Falha ao salvar as imagens.' }
    $mb = [math]::Round((Get-Item $file).Length / 1MB)
    Write-Ok "Arquivo gerado: $file ($mb MB). Distribua-o e use: .\lab.ps1 load $file"
}

function Invoke-Load($file) {
    Test-DockerReady
    if (-not $file) { $file = 'ansible-lab-imagens.tar' }
    if (-not (Test-Path -LiteralPath $file)) { Stop-Lab "Arquivo não encontrado: $file" }
    Write-Info "Carregando as imagens de $file..."
    & docker load -i $file
    if ($LASTEXITCODE -ne 0) { Stop-Lab 'Falha ao carregar as imagens.' }
    Write-Ok 'Imagens carregadas. Agora rode: .\lab.ps1 up'
}

function Test-PortInUse([int]$port) {
    $client = New-Object System.Net.Sockets.TcpClient
    try {
        $async = $client.BeginConnect('127.0.0.1', $port, $null, $null)
        if ($async.AsyncWaitHandle.WaitOne(500) -and $client.Connected) { return $true }
        return $false
    } catch { return $false } finally { $client.Close() }
}

function Invoke-Doctor {
    $bad = $false
    Write-Info 'Verificando o ambiente'

    if (Get-Command docker -ErrorAction SilentlyContinue) {
        Write-Ok ("Docker CLI encontrado ($(& docker --version))")
    } else {
        Write-Bad 'Docker não encontrado. Instale conforme docs/00-preparacao.md'; exit 1
    }

    & docker info *> $null
    if ($LASTEXITCODE -eq 0) { Write-Ok 'O serviço do Docker está respondendo' }
    else { Write-Bad 'O serviço do Docker não responde. Abra o Docker Desktop.'; exit 1 }

    $cv = (& docker compose version --short 2>$null) -replace '^v', ''
    if ($cv -match '^(\d+)\.' -and [int]$Matches[1] -ge 2) { Write-Ok "Docker Compose v2 ($cv)" }
    else { Write-Bad "Docker Compose v2 não encontrado (precisa do comando 'docker compose')."; $bad = $true }

    $arch = (& docker info --format '{{.Architecture}}' 2>$null)
    switch -Regex ($arch) {
        '^(x86_64|amd64)$'  { Write-Ok "Arquitetura do Docker: $arch (amd64)" }
        '^(aarch64|arm64)$' { Write-Ok "Arquitetura do Docker: $arch (arm64)" }
        default             { Write-Warn2 "Arquitetura inesperada: $arch (suportadas: amd64 e arm64)" }
    }

    $cg = (& docker info --format '{{.CgroupVersion}}' 2>$null)
    if ($cg -eq '2') { Write-Ok 'cgroup v2 (necessário para o systemd dos nós)' }
    else { Write-Warn2 "cgroup v$cg : o laboratório foi validado em cgroup v2; os nós podem não iniciar." }

    $mem = [double](& docker info --format '{{.MemTotal}}' 2>$null)
    $gb = [math]::Floor($mem / 1GB)
    if ($gb -ge 4) { Write-Ok "Memória disponível para o Docker: ~$gb GB" }
    elseif ($gb -ge 3) { Write-Warn2 "Memória para o Docker: ~$gb GB. Recomendado: 4 GB ou mais (ajuste o .wslconfig)." }
    else { Write-Bad "Memória para o Docker: ~$gb GB. São necessários pelo menos 3 GB (ideal 4 GB)."; $bad = $true }

    $ours = $false
    if (Test-ControlRunning) { $ours = [bool](Invoke-Dc ps --status running -q lb1 2>$null) }
    if ($ours) { Write-Ok "Porta $LbPort em uso pelo próprio laboratório (lb1)" }
    elseif (Test-PortInUse ([int]$LbPort)) {
        Write-Bad "A porta $LbPort já está em uso no seu computador. Escolha outra em docker/lab.local.env (LAB_LB_PORT=9090)."; $bad = $true
    } else { Write-Ok "Porta $LbPort livre (balanceador)" }

    # Fim de linha: CRLF nos scripts quebra os contêineres (git autocrlf no Windows).
    $crlf = @()
    $files = @(Get-Item lab, docker/compose.yml) + @(Get-ChildItem docker/control, docker/nodes -Recurse -File)
    foreach ($f in $files) {
        if ([System.IO.File]::ReadAllBytes($f.FullName) -contains 13) { $crlf += $f.Name }
    }
    if ($crlf.Count -eq 0) { Write-Ok 'Arquivos do laboratório com fim de linha LF' }
    else {
        Write-Bad ("Arquivos com fim de linha CRLF (quebram os contêineres): " + ($crlf -join ' '))
        Write-Host '      Corrija com: git config core.autocrlf false; git rm --cached -r -q .; git reset --hard'
        $bad = $true
    }

    try {
        $drive = (Get-Item $Root).PSDrive
        $free = [math]::Floor($drive.Free / 1GB)
        if ($free -ge 5) { Write-Ok "Espaço livre em disco: ~$free GB" }
        else { Write-Warn2 "Pouco espaço livre em disco: ~$free GB (as imagens ocupam cerca de 1,5 GB)." }
    } catch { }

    if (Test-ImagesPresent) { Write-Ok 'Imagens do laboratório já construídas (funciona sem internet)' }
    else { Write-Warn2 "Imagens ainda não construídas: o primeiro '.\lab.ps1 up' precisa de internet (ou use '.\lab.ps1 load')." }

    if ($env:HTTP_PROXY -or $env:HTTPS_PROXY) {
        $p = if ($env:HTTPS_PROXY) { $env:HTTPS_PROXY } else { $env:HTTP_PROXY }
        Write-Warn2 "Proxy no ambiente: $p (sera usado no build)"
    }

    Write-Host ''
    if ($bad) { Write-Host 'Há problemas a resolver antes de subir o laboratório.' -ForegroundColor Red; exit 1 }
    Write-Host 'Ambiente pronto. Próximo passo: .\lab.ps1 up' -ForegroundColor Green
}

function Show-Usage {
@'
Uso: .\lab.ps1 <comando>

Comandos principais
  up              Constrói (se preciso), gera as chaves, sobe os 5 contêineres e espera o SSH
  shell           Abre um terminal no nó de controle, em /lab
  verify NN       Verifica o desafio NN (lista de itens aprovados/reprovados)
  reset           Recria os nós gerenciados no estado inicial (não apaga o seu trabalho)

Outros comandos
  start NN        Reset + prepara o estado inicial exigido pelo desafio NN
  hint NN         Mostra a próxima dica do desafio NN
  status          Mostra os contêineres e se o Ansible alcança cada nó
  down [-v]       Para e remove os contêineres (-v remove também as chaves SSH)
  build           Reconstrói as imagens
  doctor          Confere Docker, Compose v2, memória, arquitetura e portas
  exec CMD...     Executa um comando no nó de controle, sem abrir um terminal
  save [arquivo]  Salva as imagens em um arquivo (distribuição sem internet)
  load [arquivo]  Carrega as imagens de um arquivo
'@ | Write-Host
}

# ---------------------------------------------------------------- despacho
$cmd = if ($args.Count -gt 0) { [string]$args[0] } else { 'help' }
$rest = @(if ($args.Count -gt 1) { $args[1..($args.Count - 1)] })

switch ($cmd) {
    'up'      { Invoke-Up }
    'shell'   { Invoke-Shell }
    'verify'  { Invoke-Verify ($rest | Select-Object -First 1) }
    'reset'   { Invoke-Reset }
    'start'   { Invoke-Start ($rest | Select-Object -First 1) }
    'hint'    { Invoke-Hint ($rest | Select-Object -First 1) @($rest | Select-Object -Skip 1) }
    'status'  { Invoke-Status }
    'down'    { Invoke-Down @rest }
    'build'   { Invoke-Build @rest }
    'doctor'  { Invoke-Doctor }
    'exec'    { Invoke-Exec @rest }
    'save'    { Invoke-Save ($rest | Select-Object -First 1) }
    'load'    { Invoke-Load ($rest | Select-Object -First 1) }
    { $_ -in 'help', '-h', '--help' } { Show-Usage }
    default   { Write-Host "Comando desconhecido: $cmd" -ForegroundColor Red; Show-Usage; exit 2 }
}
