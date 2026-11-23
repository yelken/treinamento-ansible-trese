#!/usr/bin/env python3
"""Verificador do desafio 06 — Condicionais, loops e erros."""
import os

import yaml

from labcheck import (Desafio, Report, block_parts, failed_results, fmt_problems, for_nodes, http_get,
                      playbook_tasks, read_file, run_internal_playbook, run_playbook, ssh, stat,
                      style_checks, syntax_check, task_module, warn_desenho)

d = Desafio("06")
rep = Report("06", "Condicionais, loops e erros")
warn_desenho(rep, d)

WEB = ("web1", "web2")
FIX = "/opt/lab/verify/fixtures/06"
RAIZ = "/var/www/portal"
PADRAO = [{"nome": "protocolo", "ativa": True}, {"nome": "transparencia", "ativa": True},
          {"nome": "ouvidoria", "ativa": True}, {"nome": "arquivo-morto", "ativa": False},
          {"nome": "concursos-2019", "ativa": False}]


def lista_padrao():
    try:
        return yaml.safe_load(open(d.p("dados", "areas.yml"), encoding="utf-8"))["areas"]
    except Exception:
        return PADRAO


def lista_alt():
    return yaml.safe_load(open(f"{FIX}/areas-alt.yml", encoding="utf-8"))["areas"]


# ------------------------------------------------------------------ estrutura
rep.section("Estrutura e boas práticas")
ok_a = syntax_check(rep, d, "areas.yml")
ok_p = syntax_check(rep, d, "publicar.yml")
tasks_a, tasks_p = [], []
for ok, nome, dest in ((ok_a, "areas.yml", tasks_a), (ok_p, "publicar.yml", tasks_p)):
    if ok:
        try:
            dest.extend(playbook_tasks(d.p(nome)))
        except Exception as exc:
            rep.warn(f"Não consegui analisar {nome}: {exc}")
style_checks(rep, tasks_a + tasks_p if (tasks_a and tasks_p) else [], "os dois playbooks")


def texto(path):
    try:
        return open(path, encoding="utf-8").read()
    except OSError:
        return ""


usa_loop = any("loop" in t for t in tasks_a)
usa_when = any("when" in t for t in tasks_a)
rep.check(usa_loop and usa_when, "areas.yml usa loop e when",
          "areas.yml não usa loop e when",
          f"loop: {'sim' if usa_loop else 'não'}; when: {'sim' if usa_when else 'não'}")

partes = block_parts(d.p("publicar.yml")) if ok_p else set()
rep.check(partes == {"block", "rescue", "always"}, "publicar.yml usa block, rescue e always",
          "publicar.yml não usa block, rescue e always juntos",
          "encontrado: " + (", ".join(sorted(partes)) if partes else "nenhum bloco"))

until = any("until" in t and "retries" in t for t in tasks_p)
rep.check(until, "publicar.yml usa until com retries", "publicar.yml não usa until com retries",
          "nenhuma task combina until e retries")

# ------------------------------------------------------------------ áreas
rep.section("Parte A: áreas (loop e when)")


def estado_areas(h, areas):
    probs = []
    for a in areas:
        base = f"{RAIZ}/areas/{a['nome']}"
        st = stat(h, base)
        if a["ativa"]:
            if not st:
                probs.append(f"{a['nome']}: o diretório não existe")
                continue
            if (st["user"], st["group"], st["mode"]) != ("root", "root", "0755"):
                probs.append(f"{a['nome']}: diretório {st['user']}:{st['group']} {st['mode']}; esperado root:root 0755")
            fs = stat(h, base + "/index.html")
            if not fs:
                probs.append(f"{a['nome']}: falta index.html")
            else:
                if fs["mode"] != "0644":
                    probs.append(f"{a['nome']}: index.html com modo {fs['mode']}; esperado 0644")
                if a["nome"] not in (read_file(h, base + "/index.html") or ""):
                    probs.append(f"{a['nome']}: index.html não cita o nome da área")
        elif st:
            probs.append(f"{a['nome']}: área inativa ainda existe")
    return "; ".join(probs) if probs else None


run_a1 = run_a2 = None
if not ok_a:
    for m in ("areas.yml executa sem erros a partir do estado inicial",
              "Segunda rodada de areas.yml sem nenhuma mudança (changed=0)",
              "Áreas ativas existem e áreas inativas não existem, em web1 e web2",
              "Com outra lista de áreas, o resultado nos nós acompanha a nova lista"):
        rep.failed(m, "playbook inválido ou ausente")
else:
    rep.info("(O verificador devolve o portal ao estado inicial antes de rodar o seu playbook.)")
    run_internal_playbook("/opt/lab/prep/06.yml")
    run_a1 = run_playbook(d, "areas.yml")
    ok1 = run_a1.rc == 0 and not run_a1.bad_hosts() and set(WEB) <= set(run_a1.stats)
    rep.check(ok1, "areas.yml executa sem erros a partir do estado inicial",
              "areas.yml falhou na primeira rodada", "\n".join(run_a1.errors()) if not ok1 else None)
    run_a2 = run_playbook(d, "areas.yml")
    ch = {h: c for h, c in run_a2.changed(WEB).items() if c}
    ok2 = run_a2.rc == 0 and not run_a2.bad_hosts() and not ch and set(WEB) <= set(run_a2.stats)
    rep.check(ok2, "Segunda rodada de areas.yml sem nenhuma mudança (changed=0)",
              "A segunda rodada de areas.yml não é idempotente",
              ("changed por host na segunda rodada: " + ", ".join(f"{h}={c}" for h, c in ch.items()))
              if ch else "\n".join(run_a2.errors()))
    prob = for_nodes(WEB, lambda h: estado_areas(h, lista_padrao()))
    rep.check(not prob, "Áreas ativas existem e áreas inativas não existem, em web1 e web2",
              "As áreas nos nós não conferem com a lista", fmt_problems(prob))
    ra = run_playbook(d, "areas.yml", ["-e", f"@{FIX}/areas-alt.yml"])
    prob = {h: "areas.yml falhou com a outra lista" for h in WEB} if ra.rc != 0 else \
        for_nodes(WEB, lambda h: estado_areas(h, lista_alt()))
    rep.check(not prob, "Com outra lista de áreas, o resultado nos nós acompanha a nova lista",
              "Com outra lista de áreas, o resultado não acompanha a lista",
              fmt_problems(prob) + ("\n(o playbook deve obedecer à variável areas, não a nomes escritos nele)"
                                    if ra.rc == 0 else ""))
    run_playbook(d, "areas.yml")  # devolve a lista padrão

# ------------------------------------------------------------------ publicação
rep.section("Parte B: publicação com plano de retorno")


def pub(versao):
    return run_playbook(d, "publicar.yml", ["-e", f"versao={versao}", "-e", f"dir_releases={FIX}"])


def serve(h, versao):
    status, corpo = http_get(f"http://{h}:8081/")
    if status != 200:
        return f"o portal não respondeu 200 (resposta: {status or corpo})"
    probs = []
    if "PORTAL-OK" not in corpo:
        probs.append("a página não contém PORTAL-OK")
    if f"versao: {versao}" not in corpo:
        achada = [l.strip() for l in corpo.splitlines() if "versao:" in l]
        probs.append(f"a página serve \"{achada[0] if achada else 'outra versão'}\"; esperado \"versao: {versao}\"")
    return "; ".join(probs) if probs else None


def registro(h, versao, resultado):
    txt = read_file(h, "/var/log/portal/ultima-publicacao.txt")
    if txt is None:
        return "/var/log/portal/ultima-publicacao.txt não existe"
    linhas = [l.strip() for l in txt.splitlines()]
    probs = []
    if f"versao={versao}" not in linhas:
        probs.append(f"falta a linha versao={versao}")
    if f"resultado={resultado}" not in linhas:
        achada = [l for l in linhas if l.startswith("resultado=")]
        probs.append(f"{achada[0] if achada else 'falta a linha resultado='}; esperado resultado={resultado}")
    return "; ".join(probs) if probs else None


if not ok_p:
    for m in ("Publicar uma versão válida termina sem erros",
              "Publicar a mesma versão de novo termina com changed=0",
              "Publicar uma segunda versão válida a coloca no ar, nos dois nós",
              "O registro da publicação traz versao= e resultado=ok",
              "Publicar uma versão defeituosa termina com falha e uma mensagem que cita a versão",
              "Depois da falha, a versão anterior continua respondendo PORTAL-OK nos dois nós",
              "O registro da falha traz a versão rejeitada e resultado=falha"):
        rep.failed(m, "playbook inválido ou ausente")
else:
    rep.info("(As versões de teste vêm do verificador: a sua pasta releases/ não é usada.)")
    p1 = pub("2025.1")
    okp1 = p1.rc == 0 and not p1.bad_hosts() and set(WEB) <= set(p1.stats)
    rep.check(okp1, "Publicar uma versão válida termina sem erros",
              "Publicar uma versão válida falhou", "\n".join(p1.errors()) if not okp1 else None)
    p1b = pub("2025.1")
    ch = {h: c for h, c in p1b.changed(WEB).items() if c}
    okb = p1b.rc == 0 and not p1b.bad_hosts() and not ch and set(WEB) <= set(p1b.stats)
    rep.check(okb, "Publicar a mesma versão de novo termina com changed=0",
              "Publicar a mesma versão de novo não é idempotente",
              ("changed por host: " + ", ".join(f"{h}={c}" for h, c in ch.items())) if ch
              else "\n".join(p1b.errors()))
    p2 = pub("2025.2")
    prob = for_nodes(WEB, lambda h: serve(h, "2025.2")) if p2.rc == 0 else \
        {h: "a publicação da segunda versão válida falhou" for h in WEB}
    rep.check(not prob, "Publicar uma segunda versão válida a coloca no ar, nos dois nós",
              "A segunda versão válida não está no ar", fmt_problems(prob) or None)
    prob = for_nodes(WEB, lambda h: registro(h, "2025.2", "ok"))
    rep.check(not prob, "O registro da publicação traz versao= e resultado=ok",
              "O registro da publicação não confere", fmt_problems(prob))

    p3 = pub("2025.3-defeito")
    msgs = [m for _, act, m in failed_results(p3)
            if act.split(".")[-1] in ("fail", "assert") and "2025.3-defeito" in m]
    if p3.rc == 0:
        det = "o play terminou com sucesso: uma versão defeituosa foi aceita ou a falha foi engolida"
    else:
        det = ("nenhuma falha explícita (fail ou assert) com uma mensagem que cite 2025.3-defeito; "
               "falhas encontradas: " + "; ".join(sorted({f"{a.split('.')[-1]}: {m[:60]}" for _, a, m in
                                                           failed_results(p3)})[:3] or ["nenhuma"]))
    rep.check(p3.rc != 0 and bool(msgs), "Publicar uma versão defeituosa termina com falha e uma mensagem que cita a versão",
              "A publicação defeituosa não termina com falha clara", det)
    prob = for_nodes(WEB, lambda h: serve(h, "2025.2"))
    rep.check(not prob, "Depois da falha, a versão anterior continua respondendo PORTAL-OK nos dois nós",
              "Depois da falha, o portal não serve a versão anterior", fmt_problems(prob))
    prob = for_nodes(WEB, lambda h: registro(h, "2025.3-defeito", "falha"))
    rep.check(not prob, "O registro da falha traz a versão rejeitada e resultado=falha",
              "O registro da falha não confere", fmt_problems(prob))

# ------------------------------------------------------------------ extensão
if ok_p and any(task_module(t) in ("ansible.builtin.find", "find") for t in tasks_p):
    rep.section("Extensão opcional — histórico enxuto", optional=True)
    for v in ("2025.4", "2025.5", "2025.6", "2025.7"):
        pub(v)

    def historico(h):
        _, out, _ = ssh(h, f"ls -1 {RAIZ}/releases | wc -l", sudo=True)
        n = int(out or 0)
        probs = []
        if n > 3:
            probs.append(f"há {n} versões em releases/; o máximo é 3")
        rc, alvo, _ = ssh(h, f"readlink {RAIZ}/atual", sudo=True)
        if rc != 0 or not alvo.endswith("2025.7") or ssh(h, f"test -d {alvo}", sudo=True)[0] != 0:
            probs.append("a versão no ar (2025.7) não está presente em releases/")
        return "; ".join(probs) if probs else None

    prob = for_nodes(WEB, historico)
    rep.check(not prob, "Sobraram no máximo 3 versões e a ativa continua presente",
              "O histórico não confere", fmt_problems(prob))

raise SystemExit(rep.finish())
