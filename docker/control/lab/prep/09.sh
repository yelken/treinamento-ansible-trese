#!/bin/bash
# Desafio 09: aplicação na versão 1 atrás do HAProxy (lb1).
set -uo pipefail
export ANSIBLE_CONFIG=/etc/ansible/ansible.cfg
ansible-playbook -i /opt/lab/inventory.yml /opt/lab/prep/09.yml | grep -E "ok=|fatal|FAILED" | sed 's/^/  /'
echo "  Versão 1 no ar atrás do balanceador: http://lb1/ (no computador: http://localhost:8080)."
echo "  Servidores do balanceador: web1 e web2, backend \"web\"; socket de administração em /var/lib/haproxy/admin.sock."
