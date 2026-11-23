#!/usr/bin/env bash
# Aplica ou restaura o gabarito de um desafio na pasta de trabalho (desafios/NN-...).
#
#   instrutor/gabarito.sh aplicar NN     salva o estado atual de desafios/NN-... e copia o gabarito por cima
#   instrutor/gabarito.sh restaurar NN   devolve desafios/NN-... ao estado salvo antes do "aplicar"
#
# Serve para demonstrar a solução e para o teste de regressão (testar-tudo.sh).
# O laboratório precisa estar no ar (./lab up).
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

acao="${1:-}"; nn="${2:-}"
[[ "$acao" =~ ^(aplicar|restaurar)$ && "$nn" =~ ^[0-9]{2}$ ]] || { echo "Uso: $0 aplicar|restaurar NN" >&2; exit 2; }

gab="$(ls -d instrutor/gabaritos/"$nn"-* 2>/dev/null | head -1 || true)"
des="$(ls -d desafios/"$nn"-* 2>/dev/null | head -1 || true)"
[[ -n "$gab" ]] || { echo "Gabarito do desafio $nn não encontrado." >&2; exit 1; }
[[ -n "$des" ]] || { echo "Pasta do desafio $nn não encontrada." >&2; exit 1; }
backup="instrutor/.backup/$nn.tar"

case "$acao" in
  aplicar)
    mkdir -p instrutor/.backup
    # só salva uma vez: um segundo "aplicar" não sobrescreve o estado original
    [[ -f "$backup" ]] || tar -cf "$backup" -C desafios "$(basename "$des")"
    cp -r "$gab"/. "$des"/
    # Gabaritos que dependem do ambiente (valores que mudam de máquina para máquina)
    if [[ "$nn" == "01" ]]; then
      ./lab exec bash -c '
        export ANSIBLE_DEPRECATION_WARNINGS=0
        cd /lab/01-inventario
        rm -rf /tmp/f1 /tmp/f2
        ansible -i inventario all -m ansible.builtin.setup -a "filter=ansible_distribution" --tree /tmp/f1 >/dev/null
        ansible -i inventario all -m ansible.builtin.setup -a "filter=ansible_memtotal_mb" --tree /tmp/f2 >/dev/null
        for h in web1 web2 db1 lb1; do
          echo "$h;$(jq -r .ansible_facts.ansible_distribution /tmp/f1/$h);$(jq -r .ansible_facts.ansible_memtotal_mb /tmp/f2/$h)"
        done > respostas.txt'
    fi
    echo "Gabarito do desafio $nn aplicado em $des"
    ;;
  restaurar)
    [[ -f "$backup" ]] || { echo "Não há estado salvo para o desafio $nn." >&2; exit 1; }
    rm -rf "$des"
    tar -xf "$backup" -C desafios
    rm -f "$backup"
    echo "Desafio $nn restaurado ao estado anterior ao gabarito."
    ;;
esac
