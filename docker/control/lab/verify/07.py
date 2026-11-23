#!/usr/bin/env python3
"""Verificador do desafio 07 — Da lista de tasks à role."""
import glob
import os
import re
import subprocess

import yaml

from labcheck import (Desafio, Report, fmt_problems, for_nodes, http_get, load_yaml, plays,
                      run_internal_playbook, run_playbook, ssh, syntax_check, systemctl_state,
                      iter_tasks, task_module, warn_desenho)

d = Desafio("07")
rep = Report("07", "Da lista de tasks à role")
warn_desenho(rep, d)

WEB = ("web1", "web2")
ROLE = d.p("roles", "servidor_web")
PORTA, AMBIENTE = 8081, "homologacao"
PORTA2, AMBIENTE2 = 8082, "producao"
EXTRA = ["-e", f"servidor_web_porta={PORTA2}", "-e", f"servidor_web_ambiente={AMBIENTE2}"]


def carregar(path):
    try:
        return load_yaml(path)
    except Exception:
        return None


# ------------------------------------------------------------------ estrutura
rep.section("Estrutura do projeto e da role")
ok_syntax = syntax_check(rep, d, "site.yml")

solto = []
if ok_syntax:
    try:
        for play in plays(d.p("site.yml")):
            for k in ("tasks", "pre_tasks", "post_tasks", "handlers"):
                if play.get(k):
                    solto.append(k)
            if not play.get("roles"):
                solto.append("(sem roles:)")
    except Exception as exc:
        solto.append(f"YAML ilegível: {exc}")
rep.check(ok_syntax and not solto, "site.yml usa só a role (sem tasks, pre_tasks, post_tasks ou handlers soltos)",
          "site.yml tem conteúdo além da role" if ok_syntax else "não foi possível analisar o site.yml",
          "encontrado no play: " + ", ".join(sorted(set(solto))) if solto else None)

arquivos = ["tasks/main.yml", "handlers/main.yml", "defaults/main.yml", "README.md"]
faltam = [a for a in arquivos if not os.path.isfile(os.path.join(ROLE, a))]
j2 = glob.glob(os.path.join(ROLE, "templates", "**", "*.j2"), recursive=True)
if not j2:
    faltam.append("templates/*.j2")
rep.check(not faltam, "A role servidor_web tem tasks/main.yml, handlers/main.yml, defaults/main.yml, README.md e .j2 em templates/",
          "A estrutura da role não confere",
          "faltam em roles/servidor_web/: " + ", ".join(faltam) if faltam else None)

defaults = carregar(os.path.join(ROLE, "defaults", "main.yml")) or {}
defaults = defaults if isinstance(defaults, dict) else {}
fora_prefixo = [k for k in defaults if not str(k).startswith("servidor_web_")]
obrig = [k for k in ("servidor_web_porta", "servidor_web_ambiente") if k not in defaults]
rep.check(bool(defaults) and not fora_prefixo and not obrig,
          "As variáveis de defaults/main.yml têm o prefixo servidor_web_ e incluem servidor_web_porta e servidor_web_ambiente",
          "As variáveis de defaults/main.yml não conferem",
          "; ".join(x for x in (
              ("variáveis sem o prefixo servidor_web_: " + ", ".join(map(str, fora_prefixo))) if fora_prefixo else "",
              ("faltam: " + ", ".join(obrig)) if obrig else "",
              "defaults/main.yml vazio ou ausente" if not defaults else "") if x))

try:
    readme = open(os.path.join(ROLE, "README.md"), encoding="utf-8").read()
except OSError:
    readme = ""
sem_doc = [k for k in defaults if str(k) not in readme]
rep.check(bool(defaults) and bool(readme) and not sem_doc, "O README.md da role cita todas as variáveis de defaults/main.yml",
          "O README.md da role não documenta todas as variáveis",
          "não citadas no README: " + ", ".join(map(str, sem_doc)) if sem_doc else "README.md ou defaults ausente")

role_tasks = []
for nome in ("tasks", "handlers"):
    for f in glob.glob(os.path.join(ROLE, nome, "**", "*.yml"), recursive=True):
        itens = carregar(f)
        if isinstance(itens, list):
            role_tasks += list(iter_tasks(itens))
sem_nome = [t for t in role_tasks if not str(t.get("name", "")).strip()]
sem_fqcn = [task_module(t) for t in role_tasks if task_module(t) and "." not in task_module(t)]
rep.check(bool(role_tasks) and not sem_nome and not sem_fqcn,
          "As tasks e handlers da role têm name e usam FQCN",
          "As tasks e handlers da role não seguem o padrão",
          "; ".join(x for x in (f"tasks sem name: {len(sem_nome)}" if sem_nome else "",
                                ("módulos sem FQCN: " + ", ".join(sem_fqcn)) if sem_fqcn else "",
                                "a role não tem tasks" if not role_tasks else "") if x))

vars_main = carregar(os.path.join(ROLE, "vars", "main.yml")) or {}
vars_main = vars_main if isinstance(vars_main, dict) else {}
presas = [k for k in vars_main if "porta" in str(k) or "ambiente" in str(k)]
rep.check(os.path.isdir(ROLE) and not presas, "A porta e o ambiente não estão em vars/main.yml da role",
          "A porta ou o ambiente estão em vars/main.yml" if os.path.isdir(ROLE) else "A role servidor_web não existe",
          ("variáveis em vars/main.yml: " + ", ".join(map(str, presas))) if presas
          else "esperado: a role em roles/servidor_web/")

# handlers da role (para checar se executaram)
handler_names = set()
for f in glob.glob(os.path.join(ROLE, "handlers", "**", "*.yml"), recursive=True):
    itens = carregar(f)
    if isinstance(itens, list):
        handler_names |= {t.get("name") for t in iter_tasks(itens) if t.get("name")}


def handler_rodou(run):
    """Hosts em que algum handler da role apareceu (nome pode vir com o prefixo 'role : ')."""
    hosts = {}
    for play in (run.data or {}).get("plays", []):
        for task in play.get("tasks", []):
            nome = str(task["task"].get("name", "")).split(" : ")[-1]
            if nome in handler_names:
                for h, res in task.get("hosts", {}).items():
                    if not res.get("skipped"):
                        hosts.setdefault(h, []).append(nome)
    return hosts


def nginx_ok(h):
    active, enabled = systemctl_state(h, "nginx")
    probs = []
    if active != "active":
        probs.append(f"nginx está \"{active}\"; o esperado é \"active\"")
    if enabled != "enabled":
        probs.append(f"nginx está \"{enabled}\" na inicialização; o esperado é \"enabled\"")
    if ssh(h, "nginx -t", sudo=True)[0] != 0:
        probs.append("nginx -t reprova a configuração")
    return "; ".join(probs) if probs else None


def pagina(h, porta, ambiente):
    status, corpo = http_get(f"http://{h}:{porta}/")
    if status != 200:
        return f"http://{h}:{porta}/ não respondeu 200 (resposta: {status or corpo})"
    probs = []
    if h not in corpo:
        probs.append(f"a página não cita o nome do host ({h})")
    if ambiente not in corpo:
        probs.append(f"a página não cita o ambiente ({ambiente})")
    return "; ".join(probs) if probs else None


# ------------------------------------------------------------------ execução
rep.section("Execução, idempotência e handler")
run3 = None
nginx_prob = nova = antiga = None
if not ok_syntax:
    for m in ("O playbook executa sem erros em web1 e web2 a partir dos nós sem nginx",
              "Segunda rodada sem nenhuma mudança (changed=0)",
              "Na segunda rodada, nenhum handler é executado",
              "Com -e servidor_web_porta=8082 -e servidor_web_ambiente=producao, o playbook termina sem erros",
              "Nessa execução, o handler roda em web1 e web2"):
        rep.failed(m, "playbook inválido ou ausente")
else:
    rep.info("(O verificador remove o nginx de web1 e web2 antes de rodar o seu playbook.)")
    run_internal_playbook("/opt/lab/prep/05.yml")
    run1 = run_playbook(d, "site.yml")
    ok1 = run1.rc == 0 and not run1.bad_hosts() and set(WEB) <= set(run1.stats)
    rep.check(ok1, "O playbook executa sem erros em web1 e web2 a partir dos nós sem nginx",
              "O playbook falhou na primeira rodada, a partir dos nós sem nginx",
              "\n".join(run1.errors()) if not ok1 else None)

    run2 = run_playbook(d, "site.yml")
    ch = {h: c for h, c in run2.changed(WEB).items() if c}
    ok2 = run2.rc == 0 and not run2.bad_hosts() and not ch and set(WEB) <= set(run2.stats)
    rep.check(ok2, "Segunda rodada sem nenhuma mudança (changed=0)", "A segunda rodada não é idempotente",
              ("changed por host na segunda rodada: " + ", ".join(f"{h}={c}" for h, c in ch.items()))
              if ch else "\n".join(run2.errors()))
    disparou = handler_rodou(run2) if run2.data else {}
    rep.check(ok2 and bool(handler_names) and not disparou, "Na segunda rodada, nenhum handler é executado",
              "Na segunda rodada algum handler foi executado",
              "handlers executados: " + "; ".join(f"{h}: {', '.join(n)}" for h, n in disparou.items())
              if disparou else "a role não tem handlers")

    run3 = run_playbook(d, "site.yml", EXTRA)
    ok3 = run3.rc == 0 and not run3.bad_hosts() and set(WEB) <= set(run3.stats)
    nginx_prob = for_nodes(WEB, nginx_ok)
    nova = for_nodes(WEB, lambda h: pagina(h, PORTA2, AMBIENTE2))
    antiga = {h: f"a porta {PORTA} ainda responde" for h in WEB if http_get(f"http://{h}:{PORTA}/")[0] != 0}
    rep.check(ok3, "Com -e servidor_web_porta=8082 -e servidor_web_ambiente=producao, o playbook termina sem erros",
              "O playbook falhou ao ser executado com outra porta e outro ambiente",
              "\n".join(run3.errors()) if not ok3 else None)
    rodou = handler_rodou(run3) if run3.data else {}
    faltou = [h for h in WEB if h not in rodou]
    rep.check(ok3 and bool(handler_names) and not faltou, "Nessa execução, o handler roda em web1 e web2",
              "O handler não rodou depois de a configuração mudar",
              "handler não executado em: " + ", ".join(faltou) if ok3 else "a execução falhou")

# ------------------------------------------------------------------ estado
rep.section("Estado dos nós web")
prob = nginx_prob if nginx_prob is not None else {h: "playbook inválido ou ausente" for h in WEB}
rep.check(not prob, "O nginx está ativo e habilitado, e nginx -t aprova a configuração, em web1 e web2",
          "O nginx não confere", fmt_problems(prob))

if ok_syntax:
    run4 = run_playbook(d, "site.yml")
    prob = for_nodes(WEB, lambda h: pagina(h, PORTA, AMBIENTE))
    if run4.rc != 0:
        prob = {h: "não foi possível voltar ao padrão para conferir a página" for h in WEB}
else:
    prob = {h: "playbook inválido ou ausente" for h in WEB}
rep.check(not prob, f"A página responde na porta padrão ({PORTA}) e mostra o nome do host e {AMBIENTE}",
          "A página não confere na porta padrão", fmt_problems(prob))

if run3 is not None and run3.rc == 0:
    rep.check(not nova, f"Com os valores sobrepostos, a página passa a responder na porta {PORTA2} e mostra {AMBIENTE2}",
              "A nova porta ou o novo ambiente não aparecem na página", fmt_problems(nova))
    rep.check(not antiga, f"A porta {PORTA} deixa de responder", f"A porta antiga ({PORTA}) continua respondendo",
              fmt_problems(antiga))
else:
    rep.failed(f"Com os valores sobrepostos, a página passa a responder na porta {PORTA2} e mostra {AMBIENTE2}",
               "a execução anterior falhou")
    rep.failed(f"A porta {PORTA} deixa de responder", "a execução anterior falhou")

# ------------------------------------------------------------------ extensão
if os.path.isfile(os.path.join(ROLE, "meta", "main.yml")) and ok_syntax:
    rep.section("Extensão opcional — role publicável", optional=True)
    p = subprocess.run(["ansible-lint", "-q", "site.yml", "roles/servidor_web"], cwd=d.path, env=d.env(),
                       capture_output=True, text=True, check=False)
    linhas = [l for l in (p.stdout + p.stderr).splitlines()
              if re.match(r"^\S+\s+\S+|^[\w./-]+:\d+", l) and "WARNING" not in l and "UserWarning" not in l
              and "Passed" not in l and "cache" not in l.lower()]
    rep.check(p.returncode == 0, "ansible-lint (perfil production) não aponta nada em site.yml e na role",
              "O ansible-lint ainda aponta problemas", "\n".join(linhas[:6]))

raise SystemExit(rep.finish())
