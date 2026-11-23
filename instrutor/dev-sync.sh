#!/usr/bin/env bash
# Para quem mantém o laboratório: copia docker/control/lab/ para o contêiner control em execução,
# sem reconstruir a imagem. Útil ao editar verificadores e scripts de preparação.
# (Em produção vale a imagem: rode `./lab build` antes de distribuir.)
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")/.."
export MSYS_NO_PATHCONV=1
docker compose -f docker/compose.yml cp docker/control/lab/. control:/opt/lab/
docker compose -f docker/compose.yml exec -T -u root control bash -c \
  'chmod -R a+rX /opt/lab; chmod 0755 /opt/lab/bin/*; find /opt/lab -type f \( -name "*.sh" -o -name "*.py" \) -exec chmod 0755 {} +'
echo "Sincronizado: /opt/lab atualizado no contêiner control."
