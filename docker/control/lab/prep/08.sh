#!/bin/bash
# Desafio 08: sem a conta appportal nos nós web.
set -uo pipefail
export ANSIBLE_CONFIG=/etc/ansible/ansible.cfg
ansible-playbook -i /opt/lab/inventory.yml /opt/lab/prep/08.yml | grep -E "ok=" | sed 's/^/  /'
echo "  Sem a conta appportal nos nós web."
echo "  O segredo que você vai proteger está em /etc/lab/segredos/appportal-senha.txt (fora do projeto)."
