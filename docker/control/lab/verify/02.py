#!/usr/bin/env python3
"""Verificador do desafio 02 — Primeiro playbook idempotente."""
import subprocess

from labcheck import (PKG_SVC_WORDS, SHELL_MODULES, Desafio, Report, fmt_problems, for_nodes,
                      load_yaml, playbook_tasks, run_internal_playbook, run_playbook, ssh,
                      systemctl_state, task_args_text, task_module, warn_desenho)

d = Desafio("02")
rep = Report("02", "Primeiro playbook idempotente")
warn_desenho(rep, d)

WEB = ("web1", "web2")
PACOTES = ("cronie", "rsync", "tree", "lsof")
SERVICO = "crond"

# ------------------------------------------------------------------ estrutura do projeto
rep.section("Estrutura e boas práticas")
exists = d.exists("site.yml")
rep.check(exists, "site.yml existe", "site.yml não existe na pasta do desafio")

syntax_ok = False
if exists:
    p = subprocess.run(["ansible-playbook", "--syntax-check", "site.yml"], cwd=d.path, env=d.env(),
                       capture_output=True, text=True, check=False)
    syntax_ok = p.returncode == 0
    err = [l for l in (p.stderr or p.stdout).splitlines() if l.strip()]
    rep.check(syntax_ok, "site.yml passa na checagem de sintaxe (--syntax-check)",
              "site.yml não passa na checagem de sintaxe", err[-1] if err else None)
else:
    rep.failed("site.yml passa na checagem de sintaxe", "arquivo ausente")

tasks = []
if syntax_ok:
    try:
        tasks = playbook_tasks(d.p("site.yml"))
    except Exception as exc:  # YAML inválido já foi tratado pela sintaxe
        rep.warn(f"Não consegui analisar o YAML: {exc}")

if tasks:
    unnamed = [i for i, t in enumerate(tasks, 1) if not str(t.get("name", "")).strip()]
    rep.check(not unnamed, "Todas as tasks têm name",
              "Há tasks sem name", f"tasks sem name (posição no arquivo): {', '.join(map(str, unnamed))}")

    no_fqcn = [f"{task_module(t)} (task {i})" for i, t in enumerate(tasks, 1)
               if task_module(t) and "." not in task_module(t)]
    rep.check(not no_fqcn, "Todos os módulos usam o nome completo (FQCN)",
              "Há módulos sem FQCN", "módulos: " + ", ".join(no_fqcn))

    misuse = [f"task {i}" for i, t in enumerate(tasks, 1)
              if task_module(t) in SHELL_MODULES and PKG_SVC_WORDS.search(task_args_text(t))]
    rep.check(not misuse, "Nenhuma task usa command/shell para instalar pacote ou controlar serviço",
              "Há command/shell sendo usado para instalar pacote ou controlar serviço",
              "onde: " + ", ".join(misuse))
else:
    for msg in ("Todas as tasks têm name", "Todos os módulos usam o nome completo (FQCN)",
                "Nenhuma task usa command/shell para instalar pacote ou controlar serviço"):
        rep.failed(msg, "não foi possível analisar o playbook")

# ------------------------------------------------------------------ execução
rep.section("Execução e idempotência")
if not syntax_ok:
    rep.failed("O playbook executa sem erros a partir dos nós limpos", "playbook inválido ou ausente")
    rep.failed("Segunda rodada sem nenhuma mudança (changed=0)", "playbook inválido ou ausente")
    run1 = run2 = None
else:
    rep.info("(O verificador devolve os nós web ao estado limpo antes de rodar o seu playbook.)")
    run_internal_playbook("/opt/lab/verify/02-clean.yml")
    run1 = run_playbook(d, "site.yml")
    ok1 = run1.rc == 0 and not run1.bad_hosts() and set(WEB) <= set(run1.stats)
    rep.check(ok1, "O playbook executa sem erros a partir dos nós limpos",
              "O playbook falhou na primeira rodada, a partir dos nós limpos",
              "\n".join(run1.errors()) if not ok1 else None)
    run2 = run_playbook(d, "site.yml")
    ch = {h: c for h, c in run2.changed().items() if c}
    ok2 = run2.rc == 0 and not run2.bad_hosts() and not ch and set(WEB) <= set(run2.stats)
    detail = None
    if not ok2:
        detail = ("changed por host na segunda rodada: " + ", ".join(f"{h}={c}" for h, c in ch.items())
                  if ch else "\n".join(run2.errors()))
    rep.check(ok2, "Segunda rodada sem nenhuma mudança (changed=0)",
              "A segunda rodada não é idempotente", detail)

# ------------------------------------------------------------------ estado dos nós
rep.section("Estado dos nós web")


def pacotes(h):
    faltam = [p for p in PACOTES if ssh(h, f"rpm -q {p}")[0] != 0]
    return f"pacotes não instalados: {', '.join(faltam)}" if faltam else None


prob = for_nodes(WEB, pacotes)
rep.check(not prob, f"Pacotes instalados em web1 e web2: {', '.join(PACOTES)}",
          "Pacotes ausentes nos nós web", fmt_problems(prob))


def ativo(h):
    active, _ = systemctl_state(h, SERVICO)
    return None if active == "active" else f"o serviço {SERVICO} está \"{active}\"; o esperado é \"active\""


prob = for_nodes(WEB, ativo)
rep.check(not prob, f"O serviço {SERVICO} está ativo em web1 e web2",
          f"O serviço {SERVICO} não está ativo", fmt_problems(prob))


def habilitado(h):
    _, en = systemctl_state(h, SERVICO)
    return None if en == "enabled" else f"o serviço {SERVICO} está \"{en}\" na inicialização; o esperado é \"enabled\""


prob = for_nodes(WEB, habilitado)
rep.check(not prob, f"O serviço {SERVICO} está habilitado na inicialização em web1 e web2",
          f"O serviço {SERVICO} não está habilitado", fmt_problems(prob))

# hosts fora do grupo web não podem ter sido alterados
touched = []
rc, out, _ = ssh("lb1", "rpm -q " + " ".join(PACOTES) + " | grep -v 'not installed'")
if out:
    touched.append(f"lb1: {out.replace(chr(10), '; ')}")
rc, out, _ = ssh("db1", "dpkg -s cron tree rsync lsof 2>/dev/null | grep -c '^Status: install ok installed'")
if out.strip() not in ("", "0"):
    touched.append("db1: há pacotes instalados que pertencem ao desafio")
rep.check(not touched, "Os nós fora do grupo web (db1, lb1) não foram alterados",
          "Nós fora do grupo web foram alterados", "\n".join(touched))

# ------------------------------------------------------------------ extensão opcional
if tasks and any(task_module(t) in ("ansible.builtin.cron", "cron") for t in tasks):
    rep.section("Extensão opcional — agendamento com cron", optional=True)
    problems = {}
    for h in WEB:
        _, tab, _ = ssh(h, "crontab -l", sudo=True)
        lines = tab.splitlines()
        if "#Ansible: limpeza-tmp" not in lines:
            problems[h] = "não encontrei a entrada de nome limpeza-tmp no crontab do root"
            continue
        job = lines[lines.index("#Ansible: limpeza-tmp") + 1].strip()
        if not job.startswith("30 2 * * *"):
            problems[h] = f"agendamento encontrado: \"{' '.join(job.split()[:5])}\"; esperado: \"30 2 * * *\""
        elif "find /var/tmp" not in job or "-mtime +7" not in job or "-delete" not in job:
            problems[h] = "o comando agendado não é o pedido (find em /var/tmp, -mtime +7, -delete)"
    rep.check(not problems, "web1 e web2 têm a entrada limpeza-tmp, às 02:30, com o comando pedido",
              "A entrada de cron pedida na extensão não está correta", fmt_problems(problems))

raise SystemExit(rep.finish())
