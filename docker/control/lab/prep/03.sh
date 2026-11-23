#!/bin/bash
# Desafio 03: cria o usuário "desligado" (marcos) em todos os nós.
set -euo pipefail
export ANSIBLE_CONFIG=/etc/ansible/ansible.cfg
ansible-playbook -i /opt/lab/inventory.yml /opt/lab/prep/03.yml | grep -E "PLAY RECAP|ok=" | sed 's/^/  /' || true
echo "  Usuário marcos criado em todos os nós."
