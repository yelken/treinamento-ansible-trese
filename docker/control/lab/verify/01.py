#!/usr/bin/env python3
"""Verificador do desafio 01 — Inventário e primeiro contato."""
import os
import re
import subprocess

from labcheck import (NODES, Desafio, Report, group_hosts, inventory_list, run_playbook, ssh,
                      warn_desenho)

d = Desafio("01")
rep = Report("01", "Inventário e primeiro contato")
warn_desenho(rep, d)

EXPECT = {"web": {"web1", "web2"}, "db": {"db1"}, "lb": {"lb1"}}
inv_dir = d.p("inventario")


def fmt(s):
    return "{" + ", ".join(sorted(s)) + "}" if s else "{} (vazio)"


# ------------------------------------------------------------------ estrutura do inventário
rep.section("Inventário")
files = [f for f in os.listdir(inv_dir) if not f.startswith(".")] if os.path.isdir(inv_dir) else []
inv, err = None, ("a pasta inventario/ não existe" if not os.path.isdir(inv_dir) else "a pasta inventario/ está vazia")
if files:
    inv, err = inventory_list(inv_dir, d)
rep.check(inv is not None, "O inventário em inventario/ é lido sem erro pelo ansible-inventory",
          "O inventário em inventario/ não pôde ser lido", err)

if inv is not None:
    for group, want in EXPECT.items():
        got = set(inv.get(group, {}).get("hosts", [])) if group in inv else None
        if got is None:
            rep.failed(f"Grupo {group} com exatamente {fmt(want)}", "o grupo não existe no inventário")
        else:
            rep.check(got == want, f"Grupo {group} contém exatamente {fmt(want)}",
                      f"Grupo {group} com os hosts errados",
                      f"encontrado: {fmt(got)}; esperado: {fmt(want)}")

    env_groups = [g for g, node in inv.items()
                  if g not in ("_meta", "all", "ungrouped", *EXPECT) and set(EXPECT) <= set(node.get("children", []))]
    rep.check(bool(env_groups), f"Existe um grupo de grupos do ambiente ({env_groups[0] if env_groups else ''}) que reúne web, db e lb",
              "Não existe um grupo de grupos que reúna web, db e lb",
              "procurei um grupo cujos filhos sejam os grupos web, db e lb")
    loose = set(inv.get("ungrouped", {}).get("hosts", []))
    rep.check(not loose, "Nenhum host ficou fora dos grupos",
              "Há hosts fora de qualquer grupo", f"hosts sem grupo: {fmt(loose)}")
    env_group = env_groups[0] if env_groups else None
else:
    for group, want in EXPECT.items():
        rep.failed(f"Grupo {group} contém exatamente {fmt(want)}", "sem inventário válido para conferir")
    rep.failed("Existe um grupo de grupos que reúne web, db e lb", "sem inventário válido para conferir")
    rep.failed("Nenhum host está fora dos grupos", "sem inventário válido para conferir")
    env_group = None

# ------------------------------------------------------------------ conectividade pelo grupo correto
rep.section("Conectividade")
if inv is None:
    for g in EXPECT:
        rep.failed(f"O grupo {g} responde ao ping", "sem inventário válido para testar")
else:
    run = run_playbook(d, "/opt/lab/verify/ping.yml", ["-i", inv_dir])
    results = {}
    for play in (run.data or {}).get("plays", []):
        name = play["play"]["name"]
        for task in play.get("tasks", []):
            for host, res in task.get("hosts", {}).items():
                results.setdefault(name, {})[host] = res.get("ping") == "pong"
    for g, want in EXPECT.items():
        got = results.get(g, {})
        bad = sorted(h for h, ok in got.items() if not ok)
        if not got:
            rep.failed(f"O grupo {g} responde ao ping", "nenhum host foi alcançado por esse grupo")
        elif bad or set(got) != want:
            detail = []
            if bad:
                detail.append(f"sem resposta: {', '.join(bad)}")
            if set(got) != want:
                detail.append(f"hosts alcançados: {fmt(set(got))}; esperado: {fmt(want)}")
            rep.failed(f"O grupo {g} responde ao ping", "\n".join(detail))
        else:
            rep.passed(f"O grupo {g} responde ao ping ({', '.join(sorted(got))})")

# ------------------------------------------------------------------ respostas registradas
rep.section("Respostas registradas")
resp_path = d.p("respostas.txt")
rows, bad_lines = {}, []
if os.path.isfile(resp_path):
    for n, line in enumerate(open(resp_path, encoding="utf-8"), 1):
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        parts = [p.strip() for p in line.split(";")]
        if len(parts) != 3 or not re.fullmatch(r"\d+", parts[2]):
            bad_lines.append(f"linha {n}: \"{line}\"")
        else:
            rows[parts[0]] = (parts[1], int(parts[2]))
has_all = os.path.isfile(resp_path) and not bad_lines and set(rows) == set(NODES)
detail = None
if not os.path.isfile(resp_path):
    detail = "o arquivo respostas.txt não existe na pasta do desafio"
elif bad_lines:
    detail = "linhas fora do formato host;distribuicao;memoria_mb: " + "; ".join(bad_lines)
elif set(rows) != set(NODES):
    detail = f"nós registrados: {fmt(set(rows))}; esperado: {fmt(set(NODES))}"
rep.check(has_all, "respostas.txt tem uma linha para cada um dos 4 nós, no formato esperado",
          "respostas.txt não está completo", detail)

distro_prob, mem_prob = {}, {}
for h in NODES:
    _, osid, _ = ssh(h, ". /etc/os-release; echo $ID")
    want_distro = {"rocky": "rocky", "debian": "debian"}.get(osid, osid)
    _, memkb, _ = ssh(h, "awk '/^MemTotal/ {print $2}' /proc/meminfo")
    want_mem = int(memkb) // 1024 if memkb.isdigit() else None
    if h in rows:
        got_d, got_m = rows[h]
        if want_distro not in got_d.lower():
            distro_prob[h] = f"registrado \"{got_d}\"; a distribuição real do nó é outra"
        if want_mem is not None and abs(got_m - want_mem) > 2:
            mem_prob[h] = f"registrado {got_m} MB; o nó reporta {want_mem} MB de memória total"
    else:
        distro_prob[h] = mem_prob[h] = "sem linha em respostas.txt"
rep.check(not distro_prob, "A distribuição registrada confere em todos os nós",
          "A distribuição registrada não confere", "\n".join(f"{h}: {m}" for h, m in distro_prob.items()))
rep.check(not mem_prob, "A memória registrada (MB) confere em todos os nós",
          "A memória registrada não confere", "\n".join(f"{h}: {m}" for h, m in mem_prob.items()))

# ------------------------------------------------------------------ extensão opcional
pat_path = d.p("padroes.txt")
if os.path.isfile(pat_path) and inv is not None:
    rep.section("Extensão opcional — padrões de hosts", optional=True)
    all_hosts = set(NODES)
    expected = {
        1: ("todos os hosts, menos os do grupo web", {"db1", "lb1"}),
        2: ("somente o último host do grupo web", {"web2"}),
        3: ("os hosts de web e de lb, exceto web1", {"web2", "lb1"}),
        4: ("todos os hosts cujo nome termina em 1", {"web1", "db1", "lb1"}),
    }
    patterns = {}
    for line in open(pat_path, encoding="utf-8"):
        m = re.match(r"^\s*([1-4])\s*[:;)]\s*(.+?)\s*$", line)
        if m:
            patterns[int(m.group(1))] = m.group(2)
    for n, (desc, want) in expected.items():
        pat = patterns.get(n)
        if not pat:
            rep.failed(f"Linha {n}: {desc}", "linha ausente em padroes.txt")
            continue
        proc = subprocess.run(["ansible", "-i", inv_dir, pat, "--list-hosts"], env=d.env(),
                              capture_output=True, text=True, check=False)
        got = {l.strip() for l in proc.stdout.splitlines()[1:] if l.strip()} if proc.returncode == 0 else set()
        rep.check(got == want, f"Linha {n}: seleciona {fmt(want)} ({desc})",
                  f"Linha {n}: o padrão não seleciona o esperado ({desc})",
                  f"seleciona: {fmt(got)}; esperado: {fmt(want)}")

raise SystemExit(rep.finish())
