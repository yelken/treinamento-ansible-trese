#!/usr/bin/env python3
"""Verificador do desafio 04 — Variáveis, facts e precedência."""
import json
import os
import re
import subprocess

from labcheck import (Desafio, Report, fmt_problems, for_nodes, playbook_tasks, read_file,
                      run_internal_playbook, run_playbook, ssh, stat, style_checks, syntax_check,
                      warn_desenho)

d = Desafio("04")
rep = Report("04", "Variáveis, facts e precedência")
warn_desenho(rep, d)

NODES = ("web1", "web2", "db1", "lb1")
DEBIAN = ("db1",)
PACOTE = {"RedHat": "bind-utils", "Debian": "dnsutils"}
FAMILIA = {h: ("Debian" if h in DEBIAN else "RedHat") for h in NODES}
ACHE_FAMILIA = re.compile(r"os_family|distribution|pkg_mgr|ansible_system|lsb", re.I)


def when_texts(path):
    """Textos de todas as condições `when` do playbook (inclusive em blocos)."""
    import yaml
    data = yaml.safe_load(open(path, encoding="utf-8"))
    out = []

    def walk(items):
        for t in items or []:
            if not isinstance(t, dict):
                continue
            w = t.get("when")
            if w is not None:
                out.append(" ".join(map(str, w)) if isinstance(w, list) else str(w))
            for sub in ("block", "rescue", "always"):
                walk(t.get(sub))

    for play in data if isinstance(data, list) else []:
        if isinstance(play, dict):
            for key in ("pre_tasks", "tasks", "post_tasks", "handlers"):
                walk(play.get(key))
    return out


# ------------------------------------------------------------------ estrutura
rep.section("Estrutura do projeto")
ok_syntax = syntax_check(rep, d, "site.yml")
tasks = []
if ok_syntax:
    try:
        tasks = playbook_tasks(d.p("site.yml"))
    except Exception as exc:
        rep.warn(f"Não consegui analisar o YAML: {exc}")
style_checks(rep, tasks, "o site.yml")

if ok_syntax and tasks:
    por_familia = [w for w in when_texts(d.p("site.yml")) if ACHE_FAMILIA.search(w)]
    rep.check(not por_familia, "Nenhuma task usa when para separar distribuição ou família",
              "Há tasks usando when para separar distribuição ou família",
              "condições encontradas: " + " | ".join(por_familia))
    raw = open(d.p("site.yml"), encoding="utf-8").read()
    escritos = [p for p in PACOTE.values() if p in raw]
    rep.check(not escritos, "Os nomes dos pacotes não estão escritos no site.yml",
              "Os nomes dos pacotes estão escritos dentro do site.yml",
              "encontrados no arquivo: " + ", ".join(escritos))
else:
    rep.failed("Nenhuma task usa when para separar distribuição ou família", "não foi possível analisar o playbook")
    rep.failed("Os nomes dos pacotes não estão escritos no site.yml", "não foi possível analisar o playbook")


def arquivos(*dirs):
    found = []
    for dire in dirs:
        base = d.p(dire)
        if os.path.isdir(base):
            for root, _, files in os.walk(base):
                found += [os.path.join(root, f) for f in files if not f.startswith(".")]
    return found


gv = arquivos("inventario/group_vars", "group_vars")
rep.check(bool(gv), "Existe ao menos um arquivo em group_vars/",
          "Não há nenhum arquivo em group_vars/",
          "procurei em inventario/group_vars/ e em group_vars/ (ao lado do playbook)")

hv = [p for p in arquivos("inventario/host_vars", "host_vars")
      if os.path.basename(os.path.dirname(p)) in NODES
      or os.path.splitext(os.path.basename(p))[0] in NODES]
rep.check(bool(hv), "Existe ao menos um arquivo em host_vars/ de um host do inventário (a exceção por host)",
          "Não há arquivo em host_vars/ de nenhum host do inventário",
          "esperado: um arquivo com o nome de um host (web1, web2, db1 ou lb1) em host_vars/")

# ------------------------------------------------------------------ execução
rep.section("Execução e idempotência")
if not ok_syntax:
    rep.failed("O playbook executa sem erros nos 4 nós a partir do estado inicial", "playbook inválido ou ausente")
    rep.failed("Segunda rodada sem nenhuma mudança (changed=0)", "playbook inválido ou ausente")
else:
    rep.info("(O verificador desinstala os pacotes e apaga a ficha antes de rodar o seu playbook.)")
    run_internal_playbook("/opt/lab/prep/04.yml")
    run1 = run_playbook(d, "site.yml")
    ok1 = run1.rc == 0 and not run1.bad_hosts() and set(NODES) <= set(run1.stats)
    rep.check(ok1, "O playbook executa sem erros nos 4 nós a partir do estado inicial",
              "O playbook falhou na primeira rodada, a partir do estado inicial",
              "\n".join(run1.errors()) if not ok1 else None)
    run2 = run_playbook(d, "site.yml")
    ch = {h: c for h, c in run2.changed().items() if c}
    ok2 = run2.rc == 0 and not run2.bad_hosts() and not ch and set(NODES) <= set(run2.stats)
    detail = None
    if not ok2:
        detail = ("changed por host na segunda rodada: " + ", ".join(f"{h}={c}" for h, c in ch.items())
                  if ch else "\n".join(run2.errors()))
    rep.check(ok2, "Segunda rodada sem nenhuma mudança (changed=0)", "A segunda rodada não é idempotente", detail)

# ------------------------------------------------------------------ estado dos nós
rep.section("Estado dos 4 nós")


def pacote(h):
    nome = PACOTE[FAMILIA[h]]
    if FAMILIA[h] == "RedHat":
        rc, _, _ = ssh(h, f"rpm -q {nome}")
    else:
        _, out, _ = ssh(h, f"dpkg-query -W -f='${{Status}}' {nome}")
        rc = 0 if "install ok installed" in out else 1
    if rc != 0:
        return f"o pacote {nome} não está instalado (a família é {FAMILIA[h]})"
    rc, _, _ = ssh(h, "dig -v")
    return None if rc == 0 else "o pacote está instalado, mas o comando dig não funciona"


prob = for_nodes(NODES, pacote)
rep.check(not prob, "O pacote certo de cada família está instalado e o dig funciona (bind-utils/dnsutils)",
          "O pacote de DNS não confere em todos os nós", fmt_problems(prob))


def parse_ficha(text):
    out = {}
    for line in (text or "").splitlines():
        if "=" in line:
            k, v = line.split("=", 1)
            out[k.strip()] = v.strip()
    return out


fichas = {h: read_file(h, "/etc/ficha-servidor") for h in NODES}


def ficha(h):
    st = stat(h, "/etc/ficha-servidor")
    if not st:
        return "/etc/ficha-servidor não existe"
    probs = []
    if (st["user"], st["group"]) != ("root", "root"):
        probs.append(f"dono {st['user']}:{st['group']}; o esperado é root:root")
    if st["mode"] != "0644":
        probs.append(f"modo {st['mode']}; o esperado é 0644")
    campos = parse_ficha(fichas[h])
    esperado = {"host": h, "familia": FAMILIA[h], "ambiente": "homologacao", "pacote_dns": PACOTE[FAMILIA[h]]}
    for k, v in esperado.items():
        if k not in campos:
            probs.append(f"falta a linha {k}=")
        elif campos[k] != v:
            probs.append(f"{k}={campos[k]}; o esperado é {k}={v}")
    return "; ".join(probs) if probs else None


prob = for_nodes(NODES, ficha)
rep.check(not prob, "/etc/ficha-servidor: dono, modo e as linhas host, familia, ambiente e pacote_dns",
          "A ficha não confere", fmt_problems(prob))


def retencao(h):
    esperado = "90" if h == "db1" else "30"
    campos = parse_ficha(fichas[h])
    got = campos.get("retencao_dias")
    if got is None:
        return "falta a linha retencao_dias="
    return None if got == esperado else f"retencao_dias={got}; o esperado é retencao_dias={esperado}"


prob = for_nodes(NODES, retencao)
rep.check(not prob, "retencao_dias vale 30 em web1, web2 e lb1, e 90 em db1",
          "retencao_dias não confere", fmt_problems(prob))

# ------------------------------------------------------------------ previsões
rep.section("Parte B: previsões e precedência")

QUESTOES = {
    1: ("web1", "retencao_dias", []),
    2: ("web1", "nivel_log", []),
    3: ("db1", "ambiente", ["-e", "ambiente=teste"]),
}


def verdade(host, var, extra):
    inv = d.p("conflitos", "inventario")
    if not os.path.isdir(inv):
        return None
    cmd = ["ansible", "-i", inv, host, "-c", "local", "-m", "ansible.builtin.debug",
           "-a", f"var={var}", *extra]
    p = subprocess.run(cmd, cwd=d.path, env=d.env({"ANSIBLE_LOAD_CALLBACK_PLUGINS": "1"}),
                       capture_output=True, text=True, check=False)
    try:
        data = json.loads(p.stdout)
        res = data["plays"][0]["tasks"][0]["hosts"][host]
        return str(res[var])
    except Exception:
        return None


linhas = {}
if d.exists("previsoes.txt"):
    for raw in open(d.p("previsoes.txt"), encoding="utf-8"):
        raw = raw.strip()
        if not raw or raw.startswith("#"):
            continue
        partes = [x.strip() for x in raw.split(";")]
        if len(partes) == 3 and partes[0].isdigit():
            linhas[int(partes[0])] = (partes[1], partes[2])

faltam = [str(n) for n in QUESTOES if n not in linhas or not all(linhas[n])]
rep.check(not faltam, "previsoes.txt tem as três questões com previsão e observado preenchidos",
          "previsoes.txt está incompleto",
          ("questões sem previsão ou sem observado: " + ", ".join(faltam) +
           "\nformato de cada linha: questão;previsão;observado") if d.exists("previsoes.txt")
          else "o arquivo previsoes.txt não existe na pasta do desafio")

erros = []
acertos_previsao = 0
for n, (host, var, extra) in QUESTOES.items():
    real = verdade(host, var, extra)
    if n not in linhas or not linhas[n][1] or real is None:
        erros.append(f"questão {n}: sem valor observado para conferir")
        continue
    prev, obs = linhas[n]
    if obs != real:
        erros.append(f"questão {n}: observado \"{obs}\"; o valor que o Ansible usa é diferente")
    elif prev == real:
        acertos_previsao += 1
rep.check(not erros, "Os três valores observados conferem com o que o Ansible realmente usa",
          "Há valores observados que não conferem", "\n".join(erros))
if not erros and not faltam:
    rep.info(f"(Informativo: você previu corretamente {acertos_previsao} de 3. "
             "O que importa é entender por que os outros valores vencem.)")

# ------------------------------------------------------------------ extensão
usa_local = ok_syntax and "ansible_local" in open(d.p("site.yml"), encoding="utf-8").read()
tem_fato = ssh("web1", "test -f /etc/ansible/facts.d/ficha.fact")[0] == 0
if usa_local or tem_fato:
    rep.section("Extensão opcional — fato local", optional=True)

    def fato(h):
        txt = read_file(h, "/etc/ansible/facts.d/ficha.fact")
        if txt is None:
            return "/etc/ansible/facts.d/ficha.fact não existe"
        if not re.search(r"(?m)^\[dados\]\s*$", txt) or not re.search(r"(?m)^responsavel\s*=\s*infra\s*$", txt):
            return "o arquivo .fact não tem a seção [dados] com responsavel=infra"
        campos = parse_ficha(fichas[h])
        if campos.get("responsavel") != "infra":
            return "a ficha não tem a linha responsavel=infra"
        return None

    prob = for_nodes(NODES, fato)
    rep.check(not prob, "O fato local existe e a ficha traz responsavel=infra, nos 4 nós",
              "O fato local ou a linha da ficha não conferem", fmt_problems(prob))

raise SystemExit(rep.finish())
