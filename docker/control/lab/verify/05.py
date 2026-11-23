#!/usr/bin/env python3
"""Verificador do desafio 05 — Templates e handlers."""
import glob
import os

from labcheck import (Desafio, Report, fmt_problems, for_nodes, http_get, iter_tasks, load_yaml,
                      plays, playbook_tasks, ran_task, run_internal_playbook, run_playbook, ssh,
                      style_checks, syntax_check, systemctl_state, task_module, warn_desenho)

d = Desafio("05")
rep = Report("05", "Templates e handlers")
warn_desenho(rep, d)

WEB = ("web1", "web2")
PORTA, AMBIENTE = 8081, "homologacao"
PORTA2, AMBIENTE2 = 8082, "producao"

# ------------------------------------------------------------------ estrutura
rep.section("Estrutura e boas práticas")
ok_syntax = syntax_check(rep, d, "site.yml")
tasks, handlers = [], []
if ok_syntax:
    try:
        tasks = playbook_tasks(d.p("site.yml"))
        for play in plays(d.p("site.yml")):
            handlers += list(iter_tasks(play.get("handlers")))
    except Exception as exc:
        rep.warn(f"Não consegui analisar o YAML: {exc}")
style_checks(rep, tasks, "o site.yml")

j2 = glob.glob(d.p("templates", "**", "*.j2"), recursive=True)
n_tpl = sum(1 for t in tasks if task_module(t) in ("ansible.builtin.template", "template"))
rep.check(n_tpl >= 2 and len(j2) >= 1,
          "O playbook usa o módulo template em pelo menos duas tasks, com arquivos .j2 em templates/",
          "O uso de templates não confere",
          f"tasks com template: {n_tpl} (esperado: 2 ou mais); arquivos .j2 em templates/: {len(j2)} (esperado: 1 ou mais)")


def reloads(t):
    mod = task_module(t)
    if mod not in ("ansible.builtin.service", "ansible.builtin.systemd", "service", "systemd"):
        return False
    return (t.get(mod) or {}).get("state") == "reloaded"


handler_names = {h.get("name") for h in handlers if h.get("name")}
reload_handlers = [h for h in handlers if reloads(h)]
notifiers = [t for t in tasks if t.get("notify")]
rep.check(bool(reload_handlers) and bool(notifiers),
          "Existe um handler que recarrega (state: reloaded) um serviço, e uma task o notifica",
          "O handler de recarga não confere",
          f"handlers com state: reloaded: {len(reload_handlers)}; tasks com notify: {len(notifiers)}")

def nginx_ok(h):
    active, enabled = systemctl_state(h, "nginx")
    probs = []
    if active != "active":
        probs.append(f"nginx está \"{active}\"; o esperado é \"active\"")
    if enabled != "enabled":
        probs.append(f"nginx está \"{enabled}\" na inicialização; o esperado é \"enabled\"")
    rc, _, err = ssh(h, "nginx -t", sudo=True)
    if rc != 0:
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
run1 = run2 = run3 = None
if not ok_syntax:
    for m in ("O playbook executa sem erros em web1 e web2 a partir dos nós sem nginx",
              "Segunda rodada sem nenhuma mudança (changed=0)",
              "Na segunda rodada, nenhum handler é executado",
              "Com -e site_porta=8082 -e site_ambiente=producao, o playbook termina sem erros",
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

    disparou = ran_task(run2, handler_names) if run2.data else {}
    rep.check(ok2 and bool(handler_names) and not disparou,
              "Na segunda rodada, nenhum handler é executado",
              "Na segunda rodada algum handler foi executado",
              "handlers executados: " + "; ".join(f"{h}: {', '.join(n)}" for h, n in disparou.items())
              if disparou else "o playbook não tem handlers")

    run3 = run_playbook(d, "site.yml", ["-e", f"site_porta={PORTA2}", "-e", f"site_ambiente={AMBIENTE2}"])
    ok3 = run3.rc == 0 and not run3.bad_hosts() and set(WEB) <= set(run3.stats)
    # Estado logo depois da rodada 3 (a rodada 4 devolve os nós ao padrão).
    nginx_prob = for_nodes(WEB, nginx_ok)
    nova = for_nodes(WEB, lambda h: pagina(h, PORTA2, AMBIENTE2))
    antiga = {h: f"a porta {PORTA} ainda responde" for h in WEB if http_get(f"http://{h}:{PORTA}/")[0] != 0}
    rep.check(ok3, "Com -e site_porta=8082 -e site_ambiente=producao, o playbook termina sem erros",
              "O playbook falhou ao ser executado com outra porta e outro ambiente",
              "\n".join(run3.errors()) if not ok3 else None)
    rodou = ran_task(run3, handler_names) if run3.data else {}
    faltou = [h for h in WEB if h not in rodou]
    rep.check(ok3 and bool(handler_names) and not faltou,
              "Nessa execução, o handler roda em web1 e web2",
              "O handler não rodou depois de a configuração mudar",
              "handler não executado em: " + ", ".join(faltou) if ok3 else "a execução falhou")

# ------------------------------------------------------------------ estado
rep.section("Estado dos nós web")


if ok_syntax and run3 is not None:
    prob = nginx_prob
else:
    prob = {h: "playbook inválido ou ausente" for h in WEB}
rep.check(not prob, "O nginx está ativo e habilitado, e nginx -t aprova a configuração, em web1 e web2",
          "O nginx não confere", fmt_problems(prob))

# Volta ao padrão para conferir a página na porta padrão.
if ok_syntax:
    run4 = run_playbook(d, "site.yml")
    prob = for_nodes(WEB, lambda h: pagina(h, PORTA, AMBIENTE))
    if run4.rc != 0:
        prob = {h: "não foi possível voltar ao padrão para conferir a página" for h in WEB}
else:
    prob = {h: "playbook inválido ou ausente" for h in WEB}
rep.check(not prob, f"A página responde na porta padrão ({PORTA}) e mostra o nome do host e {AMBIENTE}",
          "A página não confere na porta padrão", fmt_problems(prob))

rep.section("Efeito da mudança de porta")
if ok_syntax and run3 is not None and run3.rc == 0:
    rep.check(not nova, f"A página passa a responder na porta {PORTA2} e mostra {AMBIENTE2}",
              "A nova porta ou o novo ambiente não aparecem na página", fmt_problems(nova))
    rep.check(not antiga, f"A porta {PORTA} deixa de responder",
              f"A porta antiga ({PORTA}) continua respondendo", fmt_problems(antiga))
else:
    rep.failed(f"A página passa a responder na porta {PORTA2} e mostra {AMBIENTE2}", "a execução anterior falhou")
    rep.failed(f"A porta {PORTA} deixa de responder", "a execução anterior falhou")

# ------------------------------------------------------------------ extensão
if ok_syntax and "groups" in "".join(open(p, encoding="utf-8").read() for p in j2 if os.path.isfile(p)):
    rep.section("Extensão opcional — página que conhece o grupo", optional=True)

    def lista(h):
        _, corpo = http_get(f"http://{h}:{PORTA}/")
        falta = [w for w in WEB if w not in corpo]
        return f"a página não cita: {', '.join(falta)}" if falta else None

    prob = for_nodes(WEB, lista)
    rep.check(not prob, "Cada página lista web1 e web2", "A lista de servidores não confere", fmt_problems(prob))

raise SystemExit(rep.finish())
