# Role atualizar_app (fornecida)

Troca a versão da aplicação do Portal de Avisos em **um nó**: para o nginx, aguarda alguns
segundos, publica a página da nova versão e inicia o nginx de novo. **Ela não conhece o
balanceador**: durante a atualização o nó fica fora do ar, de propósito.

| Variável | Padrão | Para que serve |
|---|---|---|
| `atualizar_app_versao` | `2` | Versão publicada em `/srv/app/index.html`. |
| `atualizar_app_saudavel` | `true` | Com `false`, `/saude` passa a responder 503 depois da atualização (release com defeito). |
| `atualizar_app_pausa` | `8` | Segundos com o nginx parado. |

A role exige privilégios (usa `become` por conta própria). Quem a chama decide **quando** e **em quais nós** ela roda.
