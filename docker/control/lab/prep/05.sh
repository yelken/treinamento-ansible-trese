#!/bin/bash
# Desafio 05: web1 e web2 sem nginx.
set -uo pipefail
export ANSIBLE_CONFIG=/etc/ansible/ansible.cfg
ansible-playbook -i /opt/lab/inventory.yml /opt/lab/prep/05.yml | grep -E "ok=" | sed 's/^/  /'
echo "  Nós web limpos: sem nginx e sem configuração."
