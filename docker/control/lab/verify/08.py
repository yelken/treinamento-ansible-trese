#!/usr/bin/env python3
"""Verificador do desafio 08 — Segredos com Ansible Vault."""
import os
import re
import subprocess

from labcheck import (Desafio, Report, fmt_problems, for_nodes, playbook_tasks, plays,
                      run_internal_playbook, run_playbook, ssh, style_checks, syntax_check,
                      task_module, tree_text, warn_desenho)

d = Desafio("08")
rep = Report("08", "Segredos com Ansible Vault")
warn_desenho(rep, d)

WEB = ("web1", "web2")
FORA = ("db1", "lb1")
USUARIO = "appportal"
SENHA_ARQ = "/etc/lab/segredos/appportal-senha.txt"
TOKEN_ARQ = "/etc/lab/segredos/portal-token.txt"
VAULT_PASS_ARQ = "/etc/lab/vault-pass"
CABECALHO = "$ANSIBLE_VAULT;"


def ler(path):
    with open(path, encoding="utf-8") as fh:
        return fh.read().strip()


SENHA, TOKEN, VAULT_PASS = ler(SENHA_ARQ), ler(TOKEN_ARQ), ler(VAULT_PASS_ARQ)


def rel(path):
    return os.path.relpath(path, d.path)


def vault_files():
    """Arquivos inteiros cifrados com o Vault (a primeira linha é o cabeçalho)."""
    return [p for p, txt in tree_text(d.path) if txt.startswith(CABECALHO)]


def decifrar(path):
    """Devolve (dados, erro) do arquivo cifrado, aberto com o ansible.cfg do projeto."""
    proc = subprocess.run(["ansible-vault", "view", path], cwd=d.path, env=d.env(),
                          capture_output=True, text=True, check=False)
    if proc.returncode != 0:
        return None, "não abriu com a senha do laboratório"
    try:
        dados = load_yaml_text(proc.stdout)
    except Exception:
        return None, "o conteúdo não é um YAML válido"
    return dados, None


def load_yaml_text(text):
    import yaml
    return yaml.safe_load(text)


def vazou(texto):
    achados = []
    if SENHA in texto:
        achados.append("a senha da conta")
    if VAULT_PASS in texto:
        achados.append("a senha do Vault")
    return achados


def com_no_log(items, herdado=False):
    """Tasks do módulo user que definem password, sem no_log (procura dentro de blocos)."""
    faltam, total = [], 0
    for t in items or []:
        if not isinstance(t, dict):
            continue
        ativo = herdado or str(t.get("no_log", "")).lower() == "true"
        for chave in ("block", "rescue", "always"):
            if chave in t:
                f, n = com_no_log(t[chave], ativo)
                faltam += f
                total += n
        mod = task_module(t)
        args = t.get(mod) if mod else None
        if mod in ("ansible.builtin.user", "user") and isinstance(args, dict) and "password" in args:
            total += 1
            if not ativo:
                faltam.append(str(t.get("name", "(sem name)")))
    return faltam, total


# ------------------------------------------------------------------ estrutura
rep.section("Estrutura e boas práticas")
ok_syntax = syntax_check(rep, d, "site.yml")
tasks = []
if ok_syntax:
    try:
        tasks = playbook_tasks(d.p("site.yml"))
    except Exception as exc:
        rep.warn(f"Não consegui analisar o YAML: {exc}")
style_checks(rep, tasks, "o site.yml")

rep.section("Proteção dos segredos")
cofres = vault_files()
rep.check(bool(cofres), "Existe pelo menos um arquivo cifrado com o Vault no projeto",
          "Não há nenhum arquivo cifrado com o Vault",
          f"nenhum arquivo começa com {CABECALHO} (esperado: 1 ou mais)")

# O cofre abre e só tem variáveis vault_*
cofre_ok, problemas = [], []
for c in cofres:
    dados, erro = decifrar(c)
    if erro:
        problemas.append(f"{rel(c)}: {erro}")
    elif not isinstance(dados, dict) or not dados:
        problemas.append(f"{rel(c)}: não define variáveis (esperado: um dicionário YAML)")
    else:
        fora = [k for k in dados if not str(k).startswith("vault_")]
        if fora:
            problemas.append(f"{rel(c)}: variáveis sem o prefixo vault_: {', '.join(fora)}")
        else:
            cofre_ok.append(c)
rep.check(bool(cofre_ok) and not problemas,
          "O arquivo cifrado abre com a senha do laboratório e só define variáveis com prefixo vault_",
          "O conteúdo do cofre não confere",
          "; ".join(problemas) if problemas else "sem arquivo cifrado para conferir")

# Um arquivo em claro aponta para o cofre
ponteiros = []
for p, txt in tree_text(d.path):
    if txt.startswith(CABECALHO) or not p.endswith((".yml", ".yaml")):
        continue
    if re.search(r"^[A-Za-z_][\w]*:\s*[\"']?\{\{\s*vault_\w+\s*\}\}", txt, re.M):
        ponteiros.append(p)
rep.check(bool(ponteiros),
          "Um arquivo em claro expõe os nomes, com variáveis que apontam para as vault_* do cofre",
          "Nenhum arquivo em claro aponta para as variáveis do cofre",
          "não achei, em arquivos .yml sem cifra, uma variável cujo valor é {{ vault_alguma_coisa }}")

# Nenhum segredo em claro
em_claro = []
for p, txt in tree_text(d.path):
    if txt.startswith(CABECALHO):
        continue
    achados = vazou(txt)
    if achados:
        em_claro.append(f"{rel(p)} ({' e '.join(achados)})")
rep.check(not em_claro and d.exists("site.yml"), "Nenhum arquivo do projeto contém a senha em claro",
          "Há segredo em claro dentro do projeto" if em_claro else "Ainda não há projeto para conferir",
          "arquivos: " + "; ".join(em_claro) if em_claro else "o site.yml não existe")

# no_log
if ok_syntax:
    try:
        faltam, total = [], 0
        for play in plays(d.p("site.yml")):
            f, n = com_no_log(play.get("tasks"), str(play.get("no_log", "")).lower() == "true")
            faltam += f
            total += n
    except Exception:
        faltam, total = [], 0
    rep.check(total > 0 and not faltam, "A task que define a senha do usuário usa no_log: true",
              "A task que define a senha não protege o resultado com no_log",
              ("tasks do módulo user com password sem no_log: " + ", ".join(faltam)) if faltam
              else "nenhuma task do módulo ansible.builtin.user define password")
else:
    rep.failed("A task que define a senha do usuário usa no_log: true", "playbook inválido ou ausente")

# ------------------------------------------------------------------ execução
rep.section("Execução, idempotência e saída")
run1 = run2 = None
saida_v = saida_vvv = None
if not ok_syntax:
    for m in ("O playbook executa sem erros em web1 e web2 a partir dos nós sem a conta",
              "Segunda rodada sem nenhuma mudança (changed=0)",
              "A saída com -v não mostra a senha",
              "A saída com -vvv não mostra a senha"):
        rep.failed(m, "playbook inválido ou ausente")
else:
    rep.info("(O verificador remove a conta appportal de web1 e web2 antes de rodar o seu playbook.)")
    run_internal_playbook("/opt/lab/prep/08.yml")
    run1 = run_playbook(d, "site.yml")
    ok1 = run1.rc == 0 and not run1.bad_hosts() and set(WEB) <= set(run1.stats)
    rep.check(ok1, "O playbook executa sem erros em web1 e web2 a partir dos nós sem a conta",
              "O playbook falhou na primeira rodada, a partir dos nós sem a conta",
              "\n".join(run1.errors()) if not ok1 else None)

    run2 = run_playbook(d, "site.yml")
    ch = {h: c for h, c in run2.changed(WEB).items() if c}
    ok2 = run2.rc == 0 and not run2.bad_hosts() and not ch and set(WEB) <= set(run2.stats)
    rep.check(ok2, "Segunda rodada sem nenhuma mudança (changed=0)", "A segunda rodada não é idempotente",
              ("changed por host na segunda rodada: " + ", ".join(f"{h}={c}" for h, c in ch.items()))
              if ch else "\n".join(run2.errors()))

    # Saída detalhada: sempre com uma execução que cria a conta (há o que vazar).
    for nivel, nome in (("-v", "-v"), ("-vvv", "-vvv")):
        run_internal_playbook("/opt/lab/prep/08.yml")
        r = run_playbook(d, "site.yml", [nivel])
        texto = (r.stdout or "") + "\n" + (r.stderr or "")
        achados = vazou(texto)
        if nivel == "-v":
            # inclui a saída da primeira rodada (sem -v) na conferência
            achados = sorted(set(achados + vazou((run1.stdout or "") + (run1.stderr or ""))))
        rep.check(not achados and r.rc == 0,
                  f"A saída com {nome} não mostra a senha",
                  f"A saída com {nome} mostra {' e '.join(achados)}" if achados
                  else f"a execução com {nome} falhou",
                  "\n".join(r.errors()) if not achados and r.rc != 0 else
                  "procure a task que imprime o valor (debug? diff? resultado sem no_log?)")
        if nivel == "-vvv":
            saida_vvv = texto

# ------------------------------------------------------------------ estado
rep.section("Estado dos nós")


def conta(h):
    rc, linha, _ = ssh(h, f"getent shadow {USUARIO}", sudo=True)
    if rc != 0 or not linha:
        return f"a conta {USUARIO} não existe"
    senha_hash = linha.split(":")[1]
    if not senha_hash.startswith("$6$"):
        return f"o hash da senha não é sha512 (começa com \"{senha_hash[:3]}\"; esperado: $6$)"
    return None


def senha_confere(h):
    rc, linha, _ = ssh(h, f"getent shadow {USUARIO}", sudo=True)
    if rc != 0 or not linha:
        return f"a conta {USUARIO} não existe"
    senha_hash = linha.split(":")[1]
    from passlib.hash import sha512_crypt
    try:
        ok = sha512_crypt.verify(SENHA, senha_hash)
    except ValueError:
        ok = False
    return None if ok else "o hash gravado não corresponde à senha do cofre de segredos"


def sem_conta(h):
    rc, _, _ = ssh(h, f"id {USUARIO}")
    return f"a conta {USUARIO} existe, mas este nó não pertence ao grupo web" if rc == 0 else None


if ok_syntax and run1 is not None:
    prob_conta = for_nodes(WEB, conta)
    prob_senha = for_nodes(WEB, senha_confere)
    prob_fora = for_nodes(FORA, sem_conta)
else:
    prob_conta = prob_senha = {h: "playbook inválido ou ausente" for h in WEB}
    prob_fora = {h: "playbook inválido ou ausente" for h in FORA}
rep.check(not prob_conta, f"A conta {USUARIO} existe em web1 e web2, com hash sha512 ($6$)",
          "A conta não confere", fmt_problems(prob_conta))
rep.check(not prob_senha, "O hash gravado corresponde à senha do cofre de segredos",
          "A senha gravada não confere", fmt_problems(prob_senha))
rep.check(not prob_fora, "db1 e lb1 não receberam a conta", "A conta apareceu fora do grupo web",
          fmt_problems(prob_fora))

# ------------------------------------------------------------------ extensão
usa_extensao = d.exists("site.yml") and "appportal.env" in open(d.p("site.yml"), encoding="utf-8").read()
if ok_syntax and usa_extensao:
    rep.section("Extensão opcional — token da aplicação (encrypt_string)", optional=True)

    def arquivo_token(h):
        rc, saida, _ = ssh(h, "stat -c '%a %U' /etc/appportal.env", sudo=True)
        if rc != 0:
            return "o arquivo /etc/appportal.env não existe"
        probs = []
        if saida != "600 root":
            probs.append(f"modo e dono são \"{saida}\"; o esperado é \"600 root\"")
        rc, conteudo, _ = ssh(h, "cat /etc/appportal.env", sudo=True)
        if f"PORTAL_TOKEN={TOKEN}" not in conteudo.splitlines():
            probs.append("o arquivo não tem a linha PORTAL_TOKEN=<token do cofre de segredos>")
        return "; ".join(probs) if probs else None

    prob = for_nodes(WEB, arquivo_token)
    rep.check(not prob, "/etc/appportal.env existe, com modo 0600 e dono root, e traz o token",
              "O arquivo do token não confere", fmt_problems(prob))

    claro, inline = [], False
    for p, txt in tree_text(d.path):
        if txt.startswith(CABECALHO):
            continue
        if TOKEN in txt:
            claro.append(rel(p))
        if re.search(r"!vault\s*\|", txt):
            inline = True
    rep.check(not claro, "O token não aparece em claro no projeto", "O token está em claro no projeto",
              "arquivos: " + ", ".join(claro))
    rep.check(inline, "O token está no projeto como valor cifrado inline (!vault)",
              "Não achei nenhum valor cifrado inline (!vault)",
              "esperado: um valor produzido por ansible-vault encrypt_string")
    rep.check(saida_vvv is not None and TOKEN not in saida_vvv,
              "A saída com -vvv não mostra o token", "A saída com -vvv mostra o token",
              "procure a task que grava o arquivo: o resultado precisa de no_log")

raise SystemExit(rep.finish())
