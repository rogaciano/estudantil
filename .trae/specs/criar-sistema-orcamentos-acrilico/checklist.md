* [x] Projeto definido em Django com SQLite, HTML server-rendered, Tailwind via CDN e HTMX

* [x] Migrations ou scripts de criacao contemplam `tamanhos`, `espessuras`, `materiais`, `tipos_bases` e `orcamentos`

* [x] Seed inicial inclui tamanhos A6, A5, A4 e A3

* [x] Seed inicial inclui espessuras 2, 3 e 4

* [x] Seed inicial inclui materiais Acrílico Transparente (250.00) e Acrílico de Cor (300.00)

* [x] Seed inicial inclui ao menos Base Simples (1.0) e Base Reforçada (1.5)

* [x] Logica de calculo converte milimetros para metros antes de calcular a area

* [x] Formula final implementada como `area_m2 * espessura * preco_m2 * fator_base`

* [x] Controller/view publica delega o calculo a um servico isolado

* [x] Interface publica carrega selects a partir do banco

* [x] Interface publica envia requisicoes assíncronas com HTMX e atualiza apenas o alvo parcial

* [x] Resultado da cotacao e exibido formatado em R$ (BRL)

* [x] Data do orcamento e preenchida pelo backend

* [x] Historico do orcamento persiste `valor_total` e `detalhes_json`

* [x] Mudancas futuras nas tabelas de preco nao alteram o historico salvo

* [x] Rota `/admin` exige autenticacao por sessao

* [x] Area administrativa oferece CRUD para tamanhos, espessuras, materiais e tipos de base

* [x] Entregaveis incluem rotas, controllers/views, servico de calculo, migrations/seeds e templates HTML com HTMX/Tailwind

