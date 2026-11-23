#!/usr/bin/env python3
"""Verificador do desafio 09 — Atualização gradual atrás do balanceador."""
import http.client
import shlex
import threading
import time

from labcheck import (Desafio, Report, fmt_problems, for_nodes, http_get, playbook_tasks, plays,
                      run_internal_playbook, run_playbook, ssh, style_checks, syntax_check,
                      uses_key, warn_desenho)

d = Desafio("09")
rep = Report("09", "Atualização gradual atrás do balanceador")
warn_desenho(rep, d)

WEB = ("web1", "web2")
SOCKET = "/var/lib/haproxy/admin.sock"
MIN_REQUISICOES = 50


class Carga:
    """Requisições contínuas ao balanceador (3 clientes, ~30 por segundo) em segundo plano."""

    def __init__(self, host="lb1", clientes=3, intervalo=0.1):
        self.host, self.intervalo = host, intervalo
        self.parar = threading.Event()
        self.lock = threading.Lock()
        self.total = 0
        self.falhas = []
        self.t0 = time.time()
        self.threads = [threading.Thread(target=self._cliente, daemon=True) for _ in range(clientes)]

    def _cliente(self):
        while not self.parar.is_set():
            motivo = None
            try:
                conn = http.client.HTTPConnection(self.host, 80, timeout=2)
                conn.request("GET", "/")
                resp = conn.getresponse()
                resp.read()
                if resp.status != 200:
                    motivo = f"resposta {resp.status}"
                conn.close()
            except Exception as exc:  # recusada, tempo esgotado, reset...
                motivo = type(exc).__name__
            with self.lock:
                self.total += 1
                if motivo:
                    self.falhas.append((round(time.time() - self.t0, 1), motivo))
            time.sleep(self.intervalo)

    def iniciar(self):
        self.t0 = time.time()
        for t in self.threads:
            t.start()

    def encerrar(self):
        self.parar.set()
        for t in self.threads:
            t.join(timeout=5)


def com_carga(fn, folga=3.0):
    """Executa fn() com carga contínua; devolve (resultado, carga). Mede um pouco antes e depois."""
    carga = Carga()
    carga.iniciar()
    time.sleep(2.0)
    resultado = fn()
    time.sleep(folga)  # pega falhas tardias (servidor devolvido cedo demais)
    carga.encerrar()
    return resultado, carga


def resumo_falhas(carga):
    contagem = {}
    for _, m in carga.falhas:
        contagem[m] = contagem.get(m, 0) + 1
    tipos = ", ".join(f"{m} x{n}" for m, n in contagem.items())
    return (f"{len(carga.falhas)} de {carga.total} requisições falharam ({tipos}); "
            f"a primeira falha foi aos {carga.falhas[0][0]} s")


def status_haproxy():
    """Mapa servidor -> status, lido do socket de administração do HAProxy em lb1."""
    codigo = (
        "import socket;s=socket.socket(socket.AF_UNIX);s.connect(%r);s.sendall(b'show stat\\n');d=b''\n"
        "while True:\n c=s.recv(65536)\n if not c:break\n d+=c\n"
        "print(d.decode())" % SOCKET
    )
    rc, saida, _ = ssh("lb1", f"python3 -c {shlex.quote(codigo)}")
    if rc != 0:
        return None
    linhas = [l for l in saida.splitlines() if l.strip()]
    if not linhas:
        return None
    cab = linhas[0].lstrip("# ").split(",")
    i_px, i_sv, i_st = cab.index("pxname"), cab.index("svname"), cab.index("status")
    estados = {}
    for l in linhas[1:]:
        c = l.split(",")
        if len(c) > i_st and c[i_px] == "web" and c[i_sv] in WEB:
            estados[c[i_sv]] = c[i_st].split()[0]
    return estados


def versao_direta(h):
    status, corpo = http_get(f"http://{h}/")
    return corpo.strip() if status == 200 else f"(sem resposta: {status or corpo})"


# ------------------------------------------------------------------ estrutura
rep.section("Estrutura e boas práticas")
ok_syntax = syntax_check(rep, d, "atualizar.yml")
tasks, play_list = [], []
if ok_syntax:
    try:
        tasks = playbook_tasks(d.p("atualizar.yml"))
        play_list = plays(d.p("atualizar.yml"))
    except Exception as exc:
        rep.warn(f"Não consegui analisar o YAML: {exc}")
style_checks(rep, tasks, "o atualizar.yml")

texto = open(d.p("atualizar.yml"), encoding="utf-8").read() if d.exists("atualizar.yml") else ""
rep.check("atualizar_app" in texto and ok_syntax, "O playbook usa a role atualizar_app fornecida",
          "A role atualizar_app não é usada",
          "não encontrei a role atualizar_app (nem em roles:, nem em include_role/import_role)")
rep.check(any(p.get("serial") for p in play_list), "O play usa serial",
          "Nenhum play usa serial", "esperado: pelo menos um play com a palavra-chave serial")
rep.check(ok_syntax and uses_key(tasks, "delegate_to"), "Alguma task usa delegate_to (o balanceador é outro host)",
          "Nenhuma task usa delegate_to", "esperado: pelo menos uma task com a palavra-chave delegate_to")

# ------------------------------------------------------------------ execução
rep.section("Execução sob carga contínua")
run1 = carga = None
if not ok_syntax:
    for m in ("O playbook executa sem erros", f"O serviço respondeu 200 em todas as requisições durante a execução"):
        rep.failed(m, "playbook inválido ou ausente")
else:
    rep.info("(O verificador põe a versão 1 no ar e dispara ~30 requisições por segundo ao balanceador durante o seu playbook.)")
    run_internal_playbook("/opt/lab/prep/09.yml")
    status0, corpo0 = http_get("http://lb1/")
    if status0 != 200:
        rep.warn(f"Antes de começar, http://lb1/ não respondeu 200 ({status0 or corpo0}): problema no laboratório, rode lab start 09.")
    run1, carga = com_carga(lambda: run_playbook(d, "atualizar.yml"))
    ok1 = run1.rc == 0 and not run1.bad_hosts() and set(WEB) <= set(run1.stats)
    rep.check(ok1, "O playbook executa sem erros", "O playbook falhou",
              "\n".join(run1.errors()) if not ok1 else None)
    sem_falha = not carga.falhas and carga.total >= MIN_REQUISICOES
    if carga.falhas:
        detalhe = resumo_falhas(carga)
    else:
        detalhe = f"só {carga.total} requisições foram feitas (esperado: {MIN_REQUISICOES} ou mais): o playbook terminou rápido demais?"
    rep.check(sem_falha, f"O serviço respondeu 200 em todas as requisições durante a execução ({carga.total} requisições)",
              "O serviço foi interrompido durante a execução", detalhe)

# ------------------------------------------------------------------ estado
rep.section("Estado ao final")
if ok_syntax and run1 is not None:
    versoes = for_nodes(WEB, lambda h: None if versao_direta(h).startswith("versao 2 ")
                        else f"a página diz \"{versao_direta(h)}\"; o esperado começa com \"versao 2\"")
    amostra = []
    for _ in range(20):
        s, c = http_get("http://lb1/")
        amostra.append(c.strip() if s == 200 else f"(sem resposta: {s or c})")
    fora = sorted({a for a in amostra if not a.startswith("versao 2 ")})
    hosts_vistos = {a.split("host ")[-1] for a in amostra if a.startswith("versao 2 ")}
    estados = status_haproxy()
    for _ in range(10):  # a devolução ao balanceador pode ainda estar passando pelo health check
        if estados and all(estados.get(h) == "UP" for h in WEB):
            break
        time.sleep(1)
        estados = status_haproxy()
else:
    versoes = {h: "playbook inválido ou ausente" for h in WEB}
    fora, hosts_vistos, estados = ["(playbook inválido)"], set(), None

rep.check(not versoes, "web1 e web2 respondem a versão 2 diretamente", "A versão dos nós não confere",
          fmt_problems(versoes))
rep.check(not fora and hosts_vistos == set(WEB),
          "O balanceador entrega a versão 2 pelos dois servidores",
          "O balanceador não entrega só a versão 2, pelos dois servidores",
          (f"respostas diferentes do esperado: {', '.join(fora)}" if fora
           else f"só responderam: {', '.join(sorted(hosts_vistos)) or 'ninguém'}"))
ruins = {} if not estados else {h: s for h, s in estados.items() if s != "UP"}
rep.check(bool(estados) and not ruins and set(estados) == set(WEB),
          "Os dois servidores terminam em rotação (UP) no balanceador",
          "Algum servidor não terminou em rotação no balanceador",
          "não consegui ler o estado do HAProxy" if not estados
          else "; ".join(f"{h}: {s}" for h, s in ruins.items()) + " (esperado: UP)")

# ------------------------------------------------------------------ extensão
if ok_syntax and run1 is not None and run1.rc == 0:
    rep.section("Extensão opcional — release com defeito", optional=True)
    rep.info("(O verificador publica a versão 3 com defeito: depois da atualização, /saude responde 503.)")
    run2, carga2 = com_carga(lambda: run_playbook(
        d, "atualizar.yml", ["-e", "atualizar_app_versao=3", "-e", "atualizar_app_saudavel=false"]))
    rep.check(run2.rc != 0, "Com a release com defeito, o playbook termina com erro",
              "O playbook terminou sem erro, mesmo com a release com defeito",
              "a verificação de saúde deveria reprovar o primeiro nó e interromper a atualização")
    sem_falha2 = not carga2.falhas and carga2.total >= MIN_REQUISICOES
    rep.check(sem_falha2, f"O serviço não foi interrompido nessa execução ({carga2.total} requisições)",
              "O serviço foi interrompido na execução com defeito",
              resumo_falhas(carga2) if carga2.falhas else "poucas requisições foram feitas")
    novas = {h: versao_direta(h) for h in WEB}
    estados2 = status_haproxy() or {}
    atualizados = [h for h, v in novas.items() if v.startswith("versao 3 ")]
    intactos = [h for h, v in novas.items() if v.startswith("versao 2 ")]
    problemas = []
    if len(atualizados) != 1 or len(intactos) != 1:
        problemas.append("esperado: um nó na versão 3 (o que falhou) e o outro intacto na versão 2; "
                         f"encontrado: {', '.join(f'{h}={v}' for h, v in novas.items())}")
    else:
        if estados2.get(atualizados[0], "?") == "UP":
            problemas.append(f"{atualizados[0]} (versão com defeito) voltou ao balanceador")
        if estados2.get(intactos[0], "?") != "UP":
            problemas.append(f"{intactos[0]} deveria seguir em rotação, mas está \"{estados2.get(intactos[0], '?')}\"")
    rep.check(not problemas, "O nó com defeito fica fora do balanceador e o outro segue em rotação na versão 2",
              "O estado do balanceador depois do defeito não confere", "; ".join(problemas))
    run_internal_playbook("/opt/lab/prep/09.yml")  # devolve o laboratório à versão 1

raise SystemExit(rep.finish())
