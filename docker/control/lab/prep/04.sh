#!/bin/bash
# Desafio 04: nós sem as ferramentas de DNS e sem a ficha.
set -uo pipefail
export ANSIBLE_CONFIG=/etc/ansible/ansible.cfg
ansible-playbook -i /opt/lab/inventory.yml /opt/lab/prep/04.yml | grep -E "ok=" | sed 's/^/  /'
echo "  Nós limpos: sem bind-utils/dnsutils e sem /etc/ficha-servidor."
