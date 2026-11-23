"""Biblioteca comum dos verificadores do laboratório.

Regras de ouro dos verificadores:
  * conferem o RESULTADO (estado dos nós, estrutura do projeto, idempotência);
  * dizem O QUE está diferente do esperado, nunca COMO corrigir;
  * uma linha por critério, com marca de aprovado/reprovado e um resumo final.
"""
import atexit
import glob
import json
import os
import re
import shlex
import subprocess
import sys

import yaml

NODES = ("web1", "web2", "db1", "lb1")
LAB_DIR = "/lab"
DEFAULT_CFG = "/etc/ansible/ansible.cfg"
INTERNAL_INVENTORY = "/opt/lab/inventory.yml"
CM_PATH = "/tmp/lab-cm-%C"

COLOR = os.environ.get("FORCE_COLOR") == "1"
G, R, Y, B, Z = ("\033[32m", "\033[31m", "\033[33m", "\033[1m", "\033[0m") if COLOR else ("",) * 5


# --------------------------------------------------------------------------- relatório
class Report:
    """Acumula os critérios e imprime a lista de aprovados/reprovados."""

    def __init__(self, nn, titulo):
        self.nn = nn
        self.blocks = [{"title": None, "optional": False, "ok": 0, "total": 0}]
        print(f"{B}Desafio {nn} — {titulo}{Z}")

    @property
    def cur(self):
        return self.blocks[-1]

    def section(self, title, optional=False):
        print(f"\n{B}{title}{Z}")
        self.blocks.append({"title": title, "optional": optional, "ok": 0, "total": 0})

    def passed(self, msg):
        self.cur["ok"] += 1
        self.cur["total"] += 1
        print(f"  {G}✔{Z} {msg}")
        return True

    def failed(self, msg, detail=None):
        self.cur["total"] += 1
        print(f"  {R}✘{Z} {msg}")
        if detail:
            for line in str(detail).strip().splitlines():
                print(f"      {line}")
        return False

    def check(self, cond, ok_msg, fail_msg, detail=None):
        if cond:
            return self.passed(ok_msg)
        return self.failed(fail_msg, detail)

    def warn(self, msg):
        print(f"  {Y}!{Z} {msg}")

    def info(self, msg):
        print(f"    {msg}")

    def finish(self):
        main = [b for b in self.blocks if not b["optional"]]
        ok = sum(b["ok"] for b in main)
        total = sum(b["total"] for b in main)
        print()
        color = G if ok == total and total else R
        print(f"{color}{B}Resultado: {ok} de {total} critérios atendidos.{Z}")
        for b in self.blocks:
            if b["optional"] and b["total"]:
                print(f"{B}{b['title']}:{Z} {b['ok']} de {b['total']} critérios atendidos (não conta para o resultado).")
        if ok == total and total:
            print("Missão essencial concluída. Se quiser ir além, veja a extensão opcional do README.")
        return 0 if ok == total and total else 1


# --------------------------------------------------------------------------- desafio / projeto
class Desafio:
    def __init__(self, nn):
        self.nn = nn
        found = sorted(glob.glob(f"{LAB_DIR}/{nn}-*"))
        found = [p for p in found if os.path.isdir(p)]
        if not found:
            print(f"Não encontrei a pasta do desafio {nn} dentro de {LAB_DIR}.", file=sys.stderr)
            sys.exit(2)
        self.path = found[0]

    def p(self, *parts):
        return os.path.join(self.path, *parts)

    def exists(self, *parts):
        return os.path.exists(self.p(*parts))

    @property
    def cfg(self):
        c = self.p("ansible.cfg")
        return c if os.path.isfile(c) else DEFAULT_CFG

    def env(self, extra=None):
        env = dict(os.environ)
        env.update(
            ANSIBLE_CONFIG=self.cfg,
            ANSIBLE_STDOUT_CALLBACK="ansible.builtin.json",
            ANSIBLE_FORCE_COLOR="0",
            ANSIBLE_NOCOLOR="1",
            ANSIBLE_DEPRECATION_WARNINGS="0",
        )
        if extra:
            env.update(extra)
        return env


# --------------------------------------------------------------------------- Ansible
class Run:
    """Resultado de uma execução de ansible-playbook com o callback JSON."""

    def __init__(self, proc):
        self.rc = proc.returncode
        self.stdout = proc.stdout
        self.stderr = proc.stderr
        self.data = None
        try:
            self.data = json.loads(proc.stdout)
        except ValueError:
            pass

    @property
    def stats(self):
        return (self.data or {}).get("stats", {})

    def changed(self, hosts=None):
        return {h: s.get("changed", 0) for h, s in self.stats.items() if hosts is None or h in hosts}

    def bad_hosts(self):
        return [h for h, s in self.stats.items() if s.get("failures") or s.get("unreachable")]

    def errors(self, limit=3):
        """Mensagens de erro das tasks que falharam (texto do próprio Ansible)."""
        out = []
        for play in (self.data or {}).get("plays", []):
            for task in play.get("tasks", []):
                for host, res in task.get("hosts", {}).items():
                    if res.get("failed") or res.get("unreachable"):
                        msg = str(res.get("msg") or res.get("stderr") or "").strip().splitlines()
                        out.append(f"{host} / {task['task'].get('name', '?')}: {msg[0] if msg else 'falhou'}")
        if not out and self.rc != 0:
            err = (self.stderr or self.stdout).strip().splitlines()
            out = [err[-1]] if err else ["(sem saída)"]
        return out[:limit]


def run_playbook(desafio, playbook, extra_args=(), extra_env=None, cwd=None, timeout=900):
    """Executa um playbook como o aluno executaria: com o ansible.cfg do projeto."""
    cmd = ["ansible-playbook", playbook, *extra_args]
    try:
        proc = subprocess.run(
            cmd, cwd=cwd or desafio.path, env=desafio.env(extra_env),
            capture_output=True, text=True, timeout=timeout, check=False,
        )
    except subprocess.TimeoutExpired:
        proc = subprocess.CompletedProcess(cmd, 124, "", "tempo esgotado")
    return Run(proc)


def run_internal_playbook(playbook, extra_args=(), timeout=600):
    """Playbooks do próprio laboratório (limpeza, preparação), com o inventário interno."""
    env = dict(os.environ, ANSIBLE_CONFIG=DEFAULT_CFG, ANSIBLE_STDOUT_CALLBACK="ansible.builtin.json",
               ANSIBLE_FORCE_COLOR="0", ANSIBLE_NOCOLOR="1", ANSIBLE_DEPRECATION_WARNINGS="0")
    proc = subprocess.run(
        ["ansible-playbook", "-i", INTERNAL_INVENTORY, playbook, *extra_args],
        env=env, capture_output=True, text=True, timeout=timeout, check=False,
    )
    return Run(proc)


def inventory_list(inventory_path, desafio=None):
    """Retorna (dados_json, erro) de `ansible-inventory --list`."""
    env = desafio.env() if desafio else dict(os.environ, ANSIBLE_CONFIG=DEFAULT_CFG)
    proc = subprocess.run(
        ["ansible-inventory", "-i", inventory_path, "--list"],
        env=env, capture_output=True, text=True, check=False,
    )
    if proc.returncode != 0:
        err = [l for l in proc.stderr.splitlines() if l.strip()]
        return None, (err[-1] if err else "erro ao ler o inventário")
    try:
        return json.loads(proc.stdout), None
    except ValueError:
        return None, "saída inválida do ansible-inventory"


def group_hosts(inv, group, _seen=None):
    """Hosts de um grupo, incluindo os dos grupos filhos."""
    _seen = _seen or set()
    if group in _seen or group not in inv:
        return set()
    _seen.add(group)
    node = inv[group]
    hosts = set(node.get("hosts", []))
    for child in node.get("children", []):
        hosts |= group_hosts(inv, child, _seen)
    return hosts


# --------------------------------------------------------------------------- nós gerenciados
def ssh(host, cmd, sudo=False, timeout=40):
    """Roda um comando em um nó. Retorna (rc, stdout, stderr)."""
    remote = f"sudo -n sh -c {shlex.quote(cmd)}" if sudo else cmd
    try:
        p = subprocess.run(
            ["ssh", "-n", "-o", "BatchMode=yes", "-o", "ConnectTimeout=5",
             "-o", "ControlMaster=auto", "-o", f"ControlPath={CM_PATH}", "-o", "ControlPersist=30",
             host, remote],
            capture_output=True, text=True, timeout=timeout, check=False,
        )
    except subprocess.TimeoutExpired:
        return 124, "", "tempo esgotado"
    return p.returncode, p.stdout.strip(), p.stderr.strip()


def _close_connections():
    for h in NODES:
        subprocess.run(["ssh", "-O", "exit", "-o", f"ControlPath={CM_PATH}", h],
                       capture_output=True, check=False)


atexit.register(_close_connections)


def mode4(octal_text):
    """'750' -> '0750'; '2770' -> '2770'."""
    return f"{int(octal_text, 8):04o}"


def stat(host, path):
    """Dono, grupo, modo (4 dígitos) e tipo de um caminho, ou None se não existir."""
    rc, out, _ = ssh(host, f"stat -c '%U|%G|%a|%F' {shlex.quote(path)}", sudo=True)
    if rc != 0:
        return None
    user, group, mode, kind = out.split("|", 3)
    return {"user": user, "group": group, "mode": mode4(mode), "kind": kind}


def read_file(host, path):
    rc, out, _ = ssh(host, f"cat {shlex.quote(path)}", sudo=True)
    return out if rc == 0 else None


def systemctl_state(host, unit):
    """(ativo, habilitado) como textos: 'active'/'inactive'..., 'enabled'/'disabled'..."""
    _, active, _ = ssh(host, f"systemctl is-active {shlex.quote(unit)}")
    _, enabled, _ = ssh(host, f"systemctl is-enabled {shlex.quote(unit)}")
    return active or "unidade não encontrada", enabled or "unidade não encontrada"


def for_nodes(hosts, fn):
    """Aplica fn(host) -> None|str (str = problema). Retorna dict host->problema."""
    problems = {}
    for h in hosts:
        res = fn(h)
        if res:
            problems[h] = res
    return problems


def fmt_problems(problems):
    return "\n".join(f"{h}: {msg}" for h, msg in problems.items())


# --------------------------------------------------------------------------- análise estática de playbooks
TASK_KEYWORDS = {
    "name", "action", "local_action", "args", "become", "become_user", "become_method", "become_flags",
    "become_exe", "check_mode", "collections", "connection", "debugger", "delay", "delegate_to",
    "delegate_facts", "diff", "environment", "failed_when", "ignore_errors", "ignore_unreachable",
    "loop", "loop_control", "module_defaults", "no_log", "notify", "poll", "port", "register",
    "remote_user", "retries", "run_once", "tags", "throttle", "timeout", "until", "vars", "when",
    "changed_when", "any_errors_fatal", "async", "listen", "block", "rescue", "always",
}


def load_yaml(path):
    with open(path, encoding="utf-8") as fh:
        return yaml.safe_load(fh)


def iter_tasks(items):
    """Todas as tasks de uma lista (entra em block/rescue/always)."""
    for t in items or []:
        if not isinstance(t, dict):
            continue
        if "block" in t:
            yield from iter_tasks(t.get("block"))
            yield from iter_tasks(t.get("rescue"))
            yield from iter_tasks(t.get("always"))
        else:
            yield t


def playbook_tasks(path):
    """Lista de tasks de todos os plays (tasks, pre_tasks, post_tasks, handlers)."""
    data = load_yaml(path)
    tasks = []
    for play in data if isinstance(data, list) else []:
        if not isinstance(play, dict):
            continue
        for key in ("pre_tasks", "tasks", "post_tasks", "handlers"):
            tasks.extend(iter_tasks(play.get(key)))
    return tasks


def task_module(task):
    for key in task:
        if key in TASK_KEYWORDS or key.startswith("with_"):
            continue
        return key
    return task.get("action") if isinstance(task.get("action"), str) else None


def task_args_text(task):
    mod = task_module(task)
    val = task.get(mod)
    if isinstance(val, dict):
        val = " ".join(str(v) for v in val.values())
    return str(val or "")


SHELL_MODULES = {"command", "shell", "raw", "script",
                 "ansible.builtin.command", "ansible.builtin.shell", "ansible.builtin.raw",
                 "ansible.builtin.script", "ansible.legacy.command", "ansible.legacy.shell"}
PKG_SVC_WORDS = re.compile(r"\b(dnf|yum|rpm|apt|apt-get|dpkg|systemctl|service|chkconfig|rc-service)\b")


def desenho_preenchido(path):
    """True se as cinco perguntas do DESENHO.md têm resposta (>= 4 palavras cada)."""
    try:
        text = open(path, encoding="utf-8").read()
    except OSError:
        return False
    parts = re.split(r"(?m)^## ", text)[1:]
    answered = 0
    for part in parts:
        m = re.search(r"\*\*Sua resposta:\*\*(.*)", part, re.S)
        if not m:
            continue
        body = re.sub(r"<!--.*?-->", "", m.group(1), flags=re.S)
        if len(re.findall(r"\w+", body)) >= 4:
            answered += 1
    return answered >= 5


def warn_desenho(rep, desafio):
    if not desenho_preenchido(desafio.p("DESENHO.md")):
        rep.warn("Lembrete: o DESENHO.md ainda não está preenchido (as cinco perguntas). "
                 "Desenhar antes de digitar é parte do método.")


# --------------------------------------------------------------------------- verificações reutilizáveis
def http_get(url, timeout=5):
    """(status, corpo) de um GET. Status 0 = sem resposta (corpo traz o motivo)."""
    import urllib.error
    import urllib.request
    try:
        with urllib.request.urlopen(url, timeout=timeout) as resp:
            return resp.status, resp.read().decode("utf-8", "replace")
    except urllib.error.HTTPError as exc:
        return exc.code, ""
    except Exception as exc:  # recusa de conexão, tempo esgotado, DNS...
        return 0, str(exc)


def syntax_check(rep, desafio, playbook, label=None):
    """Critérios 'existe' e 'passa na sintaxe'. Retorna True se o playbook é utilizável."""
    label = label or playbook
    exists = desafio.exists(playbook)
    rep.check(exists, f"{label} existe", f"{label} não existe na pasta do desafio")
    if not exists:
        rep.failed(f"{label} passa na checagem de sintaxe (--syntax-check)", "arquivo ausente")
        return False
    p = subprocess.run(["ansible-playbook", "--syntax-check", playbook], cwd=desafio.path,
                       env=desafio.env(), capture_output=True, text=True, check=False)
    err = [l for l in (p.stderr or p.stdout).splitlines() if l.strip()]
    return rep.check(p.returncode == 0, f"{label} passa na checagem de sintaxe (--syntax-check)",
                     f"{label} não passa na checagem de sintaxe", err[-1] if err else None)


def style_checks(rep, tasks, label="o playbook"):
    """Todas as tasks com name e todos os módulos com FQCN."""
    if not tasks:
        rep.failed("Todas as tasks têm name", f"não foi possível analisar {label}")
        rep.failed("Todos os módulos usam o nome completo (FQCN)", f"não foi possível analisar {label}")
        return
    unnamed = [str(i) for i, t in enumerate(tasks, 1) if not str(t.get("name", "")).strip()]
    rep.check(not unnamed, "Todas as tasks têm name", "Há tasks sem name",
              "tasks sem name (posição no arquivo): " + ", ".join(unnamed))
    no_fqcn = [f"{task_module(t)} (task {i})" for i, t in enumerate(tasks, 1)
               if task_module(t) and "." not in task_module(t)]
    rep.check(not no_fqcn, "Todos os módulos usam o nome completo (FQCN)", "Há módulos sem FQCN",
              "módulos: " + ", ".join(no_fqcn))


def plays(path):
    data = load_yaml(path)
    return [p for p in data if isinstance(p, dict)] if isinstance(data, list) else []


def all_tasks_deep(path):
    """Tasks de um playbook, incluindo block/rescue/always e handlers (uma lista plana)."""
    try:
        return playbook_tasks(path)
    except Exception:
        return []


def uses_key(tasks, key):
    """Alguma task (ou bloco) usa a palavra-chave `key`? Procura também dentro de blocos."""
    def walk(items):
        for t in items or []:
            if not isinstance(t, dict):
                continue
            if key in t:
                return True
            for sub in ("block", "rescue", "always"):
                if walk(t.get(sub)):
                    return True
        return False
    return walk(tasks)


def ran_task(run, names):
    """Hosts em que alguma task com um dos `names` apareceu na saída JSON (executou ou foi pulada)."""
    hosts = {}
    for play in (run.data or {}).get("plays", []):
        for task in play.get("tasks", []):
            if task["task"].get("name") in names:
                for h, res in task.get("hosts", {}).items():
                    if not res.get("skipped"):
                        hosts.setdefault(h, []).append(task["task"]["name"])
    return hosts


def tree_text(root, skip=(".git", ".ansible", "__pycache__", "node_modules")):
    """Gera (caminho, texto) de todos os arquivos legíveis em texto abaixo de root."""
    for base, dirs, files in os.walk(root):
        dirs[:] = [d for d in dirs if d not in skip]
        for f in files:
            path = os.path.join(base, f)
            try:
                with open(path, "rb") as fh:
                    raw = fh.read(2_000_000)
            except OSError:
                continue
            yield path, raw.decode("utf-8", "replace")


def failed_results(run):
    """[(host, módulo, msg)] de todos os resultados com falha na saída JSON (inclusive os resgatados)."""
    out = []
    for play in (run.data or {}).get("plays", []):
        for task in play.get("tasks", []):
            for host, res in task.get("hosts", {}).items():
                if res.get("failed"):
                    out.append((host, str(res.get("action", "")), str(res.get("msg", ""))))
    return out


def block_parts(path):
    """Conjunto de {'block','rescue','always'} presentes juntos em algum bloco do playbook."""
    found = set()

    def walk(items):
        for t in items or []:
            if isinstance(t, dict):
                if "block" in t:
                    here = {k for k in ("block", "rescue", "always") if k in t}
                    if len(here) > len(found):
                        found.clear()
                        found.update(here)
                    for sub in ("block", "rescue", "always"):
                        walk(t.get(sub))

    for play in plays(path):
        for key in ("pre_tasks", "tasks", "post_tasks", "handlers"):
            walk(play.get(key))
    return found
