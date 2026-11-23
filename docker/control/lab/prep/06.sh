#!/bin/bash
# Desafio 06: portal no ar (versão "inicial") em web1 e web2, com duas áreas antigas.
set -uo pipefail
export ANSIBLE_CONFIG=/etc/ansible/ansible.cfg
ansible-playbook -i /opt/lab/inventory.yml /opt/lab/prep/06.yml | grep -E "ok=" | sed 's/^/  /'
echo "  Portal no ar em http://web1:8081 e http://web2:8081 (versão: inicial)."
