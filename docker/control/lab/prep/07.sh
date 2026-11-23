#!/bin/bash
# Desafio 07: nós web sem nginx e playbook monolítico de partida na pasta do desafio.
set -uo pipefail
export ANSIBLE_CONFIG=/etc/ansible/ansible.cfg
dest="$(ls -d /lab/07-* 2>/dev/null | head -1)"
if [[ -z "$dest" ]]; then
    echo "Não encontrei a pasta do desafio 07 em /lab." >&2
    exit 1
fi
ansible-playbook -i /opt/lab/inventory.yml /opt/lab/prep/05.yml | grep -E "ok=" | sed 's/^/  /'
cp /opt/lab/prep/07/monolitico.yml "$dest/monolitico.yml"
mkdir -p "$dest/templates"
cp /opt/lab/prep/07/templates/*.j2 "$dest/templates/"
echo "  Nós web sem nginx. Ponto de partida: monolitico.yml e templates/ na pasta do desafio."
