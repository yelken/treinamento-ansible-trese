# servidor_web

Instala e configura o nginx com uma página institucional que mostra o nome do
servidor e o ambiente. A configuração é gerada por template e o serviço é
recarregado por handler, somente quando a configuração muda.

## Requisitos

- Família Red Hat (usa `ansible.builtin.dnf`), com `become` habilitado.

## Variáveis

Definidas em `defaults/main.yml` (podem ser sobrepostas em `group_vars`,
`host_vars` ou `-e`):

| Variável | Padrão | Para que serve |
|---|---|---|
| `servidor_web_porta` | `8081` | Porta em que o nginx escuta. |
| `servidor_web_ambiente` | `homologacao` | Nome do ambiente exibido na página. |

Constante interna, em `vars/main.yml`: `servidor_web_raiz` (diretório do site).

## Exemplo

```yaml
- hosts: web
  become: true
  roles:
    - role: servidor_web
      servidor_web_porta: 8082
```

## Licença

MIT
