#!/bin/bash
# Entrypoint do nó de controle.
# Em hosts Linux, o dono de /lab é o usuário do host (uid qualquer). Ajustamos o uid/gid do
# usuário "aluno" para coincidir, senão ele não conseguiria gravar na pasta de trabalho.
# No Windows e no macOS o dono aparece como root (uid 0) com permissão aberta: nada a fazer.
set -euo pipefail

if [[ -d /lab ]]; then
    lab_uid="$(stat -c %u /lab)"
    lab_gid="$(stat -c %g /lab)"
    if [[ "$lab_gid" != 0 && "$lab_gid" != "$(id -g aluno)" ]]; then
        groupmod -o -g "$lab_gid" aluno
    fi
    if [[ "$lab_uid" != 0 && "$lab_uid" != "$(id -u aluno)" ]]; then
        usermod -o -u "$lab_uid" aluno
    fi
    chown -R aluno:aluno /home/aluno 2>/dev/null || true
fi

touch /run/lab-ready
exec "$@"
