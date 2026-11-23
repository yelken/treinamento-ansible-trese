# Certificados de CA corporativa (opcional)

Se a sua rede usa um proxy com inspeção TLS, o `lab build` falha com erros de
certificado (`SSL certificate problem`, `self-signed certificate in certificate chain`).

Para resolver, copie o certificado da CA corporativa para **esta pasta**:

- formato PEM, extensão `.crt` (para o nó Rocky também vale `.pem`);
- exemplo: `docker/certs/ca-corporativa.crt`.

Ele será instalado no repositório de confiança das três imagens durante o `lab build`.
Nenhum certificado é versionado (veja `.gitignore`); esta pasta pode ficar vazia.
