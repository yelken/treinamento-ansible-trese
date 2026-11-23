#!/usr/bin/env python3
"""Verificador do desafio 03 — Arquivos, usuários e permissões."""
import subprocess

from labcheck import (NODES, Desafio, Report, fmt_problems, for_nodes, playbook_tasks,
                      read_file, run_internal_playbook, run_playbook, ssh, stat, task_module,
                      warn_desenho)

d = Desafio("03")
rep = Report("03", "Arquivos, usuários e permissões")
warn_desenho(rep, d)

BANNER = "ACESSO RESTRITO - USO EXCLUSIVO DE PESSOAL AUTORIZADO"
GRUPO = "adm-infra"
USUARIOS = ("ana", "bruno", "carla")
DIRS = (
    ("/opt/infra", "root", "root", "0755"),
    ("/opt/infra/scripts", "root", GRUPO, "0750"),
    ("/opt/infra/relatorios", "root", GRUPO, "2770"),
)

# ------------------------------------------------------------------ projeto
rep.section("Estrutura do projeto")
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

validated = False
if syntax_ok:
    for t in playbook_tasks(d.p("site.yml")):
        args = t.get(task_module(t))
        if isinstance(args, dict) and "visudo" in str(args.get("validate", "")):
            validated = True
rep.check(validated, "A regra de sudo é gravada com validate (visudo)",
          "Nenhuma task grava a regra de sudo usando validate com o visudo",
          "o sudoers é um arquivo crítico: um erro de sintaxe pode trancar o acesso administrativo")

# ------------------------------------------------------------------ execução
rep.section("Execução e idempotência")
if not syntax_ok:
    rep.failed("O playbook executa sem erros nos 4 nós", "playbook inválido ou ausente")
    rep.failed("Segunda rodada sem nenhuma mudança (changed=0)", "playbook inválido ou ausente")
else:
    rep.info("(O verificador recria o usuário desligado antes de rodar o seu playbook.)")
    run_internal_playbook("/opt/lab/prep/03.yml")
    run1 = run_playbook(d, "site.yml")
    ok1 = run1.rc == 0 and not run1.bad_hosts() and set(NODES) <= set(run1.stats)
    rep.check(ok1, "O playbook executa sem erros nos 4 nós",
              "O playbook falhou na primeira rodada", "\n".join(run1.errors()) if not ok1 else None)
    run2 = run_playbook(d, "site.yml")
    ch = {h: c for h, c in run2.changed().items() if c}
    ok2 = run2.rc == 0 and not run2.bad_hosts() and not ch and set(NODES) <= set(run2.stats)
    detail = None
    if not ok2:
        detail = ("changed por host na segunda rodada: " + ", ".join(f"{h}={c}" for h, c in ch.items())
                  if ch else "\n".join(run2.errors()))
    rep.check(ok2, "Segunda rodada sem nenhuma mudança (changed=0)",
              "A segunda rodada não é idempotente", detail)

# ------------------------------------------------------------------ estado dos nós
rep.section("Estado dos 4 nós")


def banner(h):
    st = stat(h, "/etc/motd")
    if not st:
        return "/etc/motd não existe"
    probs = []
    if (st["user"], st["group"]) != ("root", "root"):
        probs.append(f"dono {st['user']}:{st['group']}; esperado root:root")
    if st["mode"] != "0644":
        probs.append(f"o modo é {st['mode']}; o esperado é 0644")
    lines = [l.strip() for l in (read_file(h, "/etc/motd") or "").splitlines()]
    if BANNER not in lines:
        probs.append("o texto do banner pedido não está no arquivo")
    return "; ".join(probs) or None


prob = for_nodes(NODES, banner)
rep.check(not prob, "Banner de acesso em /etc/motd (texto, dono e modo)",
          "O banner de acesso não confere", fmt_problems(prob))

for path, user, group, mode in DIRS:
    def check_dir(h, path=path, user=user, group=group, mode=mode):
        st = stat(h, path)
        if not st:
            return f"{path} não existe"
        if "directory" not in st["kind"]:
            return f"{path} existe, mas não é um diretório ({st['kind']})"
        probs = []
        if st["user"] != user or st["group"] != group:
            probs.append(f"dono {st['user']}:{st['group']}; esperado {user}:{group}")
        if st["mode"] != mode:
            probs.append(f"o modo é {st['mode']}; o esperado é {mode}")
        return "; ".join(probs) or None

    prob = for_nodes(NODES, check_dir)
    rep.check(not prob, f"Diretório {path} ({user}:{group}, modo {mode})",
              f"Diretório {path} não confere", fmt_problems(prob))


def grupo(h):
    rc, _, _ = ssh(h, f"getent group {GRUPO}")
    return None if rc == 0 else f"o grupo {GRUPO} não existe"


prob = for_nodes(NODES, grupo)
rep.check(not prob, f"Grupo {GRUPO} existe", f"O grupo {GRUPO} não existe", fmt_problems(prob))


def usuarios(h):
    probs = []
    for u in USUARIOS:
        rc, out, _ = ssh(h, f"getent passwd {u}")
        if rc != 0:
            probs.append(f"usuário {u} não existe")
            continue
        shell = out.split(":")[-1]
        if shell != "/bin/bash":
            probs.append(f"{u}: shell {shell}; esperado /bin/bash")
        _, groups, _ = ssh(h, f"id -nG {u}")
        if GRUPO not in groups.split():
            probs.append(f"{u}: não é membro de {GRUPO}")
        if stat(h, f"/home/{u}") is None:
            probs.append(f"{u}: diretório pessoal /home/{u} não existe")
    return "; ".join(probs) or None


prob = for_nodes(NODES, usuarios)
rep.check(not prob, f"Usuários {', '.join(USUARIOS)} existem, com shell /bin/bash, home e membros de {GRUPO}",
          "Os usuários administrativos não conferem", fmt_problems(prob))


def sudoers(h):
    st = stat(h, f"/etc/sudoers.d/{GRUPO}")
    if not st:
        return f"/etc/sudoers.d/{GRUPO} não existe"
    probs = []
    if (st["user"], st["group"]) != ("root", "root") or st["mode"] != "0440":
        probs.append(f"dono {st['user']}:{st['group']} e modo {st['mode']}; esperado root:root e 0440")
    rc, out, err = ssh(h, f"/usr/sbin/visudo -cf /etc/sudoers.d/{GRUPO}", sudo=True)
    if rc != 0:
        probs.append("o visudo rejeita a sintaxe do arquivo")
    for u in USUARIOS:
        _, listing, _ = ssh(h, f"sudo -l -U {u}", sudo=True)
        if "NOPASSWD: ALL" not in listing:
            probs.append(f"{u} não pode executar qualquer comando via sudo sem senha")
            break
    return "; ".join(probs) or None


prob = for_nodes(NODES, sudoers)
rep.check(not prob, f"Regra de sudo do grupo {GRUPO}: arquivo, dono, modo, sintaxe válida e efeito",
          "A regra de sudo não confere", fmt_problems(prob))


def login_defs(h):
    _, out, _ = ssh(h, "grep -E '^PASS_MAX_DAYS' /etc/login.defs")
    lines = [l.split() for l in out.splitlines() if l.strip()]
    if len(lines) != 1:
        return f"há {len(lines)} linhas PASS_MAX_DAYS ativas em /etc/login.defs; o esperado é exatamente 1"
    return None if lines[0][1:] == ["90"] else f"PASS_MAX_DAYS vale {' '.join(lines[0][1:])}; o esperado é 90"


prob = for_nodes(NODES, login_defs)
rep.check(not prob, "PASS_MAX_DAYS vale 90 em /etc/login.defs (uma única linha)",
          "PASS_MAX_DAYS não confere", fmt_problems(prob))


def desligado(h):
    probs = []
    if ssh(h, "getent passwd marcos")[0] == 0:
        probs.append("o usuário marcos ainda existe")
    if stat(h, "/home/marcos") is not None:
        probs.append("o diretório /home/marcos ainda existe")
    return "; ".join(probs) or None


prob = for_nodes(NODES, desligado)
rep.check(not prob, "O usuário desligado (marcos) e o diretório pessoal dele não existem mais",
          "O usuário desligado não foi totalmente removido", fmt_problems(prob))

# ------------------------------------------------------------------ extensão opcional
tasks = []
try:
    tasks = playbook_tasks(d.p("site.yml")) if syntax_ok else []
except Exception:
    pass
if any(task_module(t) in ("ansible.posix.authorized_key", "authorized_key") for t in tasks):
    rep.section("Extensão opcional — chave SSH autorizada", optional=True)
    chave = (open(d.p("dados", "ana.pub"), encoding="utf-8").read().split() if d.exists("dados", "ana.pub") else [])

    def authorized(h):
        st_dir = stat(h, "/home/ana/.ssh")
        st_f = stat(h, "/home/ana/.ssh/authorized_keys")
        if not st_dir or not st_f:
            return "não encontrei /home/ana/.ssh/authorized_keys"
        probs = []
        if (st_dir["user"], st_dir["mode"]) != ("ana", "0700"):
            probs.append(f".ssh: {st_dir['user']} {st_dir['mode']}; esperado ana 0700")
        if (st_f["user"], st_f["mode"]) != ("ana", "0600"):
            probs.append(f"authorized_keys: {st_f['user']} {st_f['mode']}; esperado ana 0600")
        if not chave or chave[1] not in (read_file(h, "/home/ana/.ssh/authorized_keys") or ""):
            probs.append("a chave de dados/ana.pub não está autorizada")
        return "; ".join(probs) or None

    prob = for_nodes(NODES, authorized)
    rep.check(not prob, "A chave pública de dados/ana.pub está autorizada para ana (dono e modos corretos)",
              "A chave autorizada de ana não confere", fmt_problems(prob))

raise SystemExit(rep.finish())
