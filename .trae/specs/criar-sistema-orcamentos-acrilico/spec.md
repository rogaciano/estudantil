# Spec do Sistema Web de Orcamentos em Acrilico

## Why
O projeto precisa centralizar a formacao de preco para produtos em acrilico com um fluxo publico de cotacao e uma area administrativa simples para manutencao das tabelas. A formalizacao abaixo reduz ambiguidade na implementacao em Django, preserva historico de precos e define regras de calculo verificaveis.

## What Changes
- Criar uma aplicacao web em Django com frontend server-rendered em HTML + Tailwind CSS via CDN + HTMX para interacoes assincronas.
- Modelar o banco SQLite com as tabelas `tamanhos`, `espessuras`, `materiais`, `tipos_bases` e `orcamentos`.
- Implementar carga inicial de dados para tamanhos, espessuras, materiais e bases padrao.
- Disponibilizar uma calculadora publica que carregue selects a partir do banco e renderize o valor total em BRL sem recarregar a pagina.
- Persistir o historico do orcamento com `detalhes_json` contendo um espelho dos dados usados no momento da cotacao.
- Criar uma area `/admin` autenticada por sessao com CRUD HTML/Tailwind para tamanhos, espessuras, materiais e tipos de base.
- Isolar a logica matematica de calculo em uma camada de servico do backend para reutilizacao e teste.

## Impact
- Affected specs: calculo de orcamentos, persistencia de historico, autenticacao administrativa, gestao de cadastros de precificacao
- Affected code: configuracao do projeto Django, models, migrations, seeds/management command, servico de calculo, views publicas e administrativas, urls, templates HTML com HTMX

## ADDED Requirements
### Requirement: Modelagem de dados de precificacao
O sistema SHALL armazenar tamanhos, espessuras, materiais, tipos de base e orcamentos em SQLite com estrutura relacional compatível com o dominio.

#### Scenario: Estrutura minima do catalogo
- **WHEN** as migrations forem aplicadas
- **THEN** o banco deve conter as tabelas `tamanhos`, `espessuras`, `materiais`, `tipos_bases` e `orcamentos`
- **AND** `tamanhos` deve armazenar `nome`, `base_mm` e `altura_mm`
- **AND** `espessuras` deve armazenar `milimetros`
- **AND** `materiais` deve armazenar `tipo` e `preco_m2`
- **AND** `tipos_bases` deve armazenar `nome_base` e `fator_base`
- **AND** `orcamentos` deve armazenar `nome_orcamento`, `data_orcamento`, `valor_total` e `detalhes_json`

### Requirement: Carga inicial do catalogo
O sistema SHALL disponibilizar um seed/script inicial para popular o banco com dados minimos de operacao.

#### Scenario: Seed padrao executado
- **WHEN** o script de carga inicial for executado em ambiente vazio
- **THEN** devem ser inseridos os tamanhos `A6 (105x148)`, `A5 (148x210)`, `A4 (210x297)` e `A3 (297x420)`
- **AND** devem ser inseridas as espessuras `2`, `3` e `4`
- **AND** devem ser inseridos os materiais `Acrílico Transparente (250.00)` e `Acrílico de Cor (300.00)`
- **AND** devem ser inseridos os tipos de base `Base Simples (1.0)` e `Base Reforçada (1.5)` como dados minimos padrao

### Requirement: Calculo rigoroso de orcamento
O sistema SHALL calcular o valor total com base na conversao de milimetros para metros e na formula de negocio definida.

#### Scenario: Calculo do valor total
- **WHEN** o usuario selecionar tamanho, espessura, material e tipo de base
- **THEN** o backend deve converter `base_mm` e `altura_mm` para metros dividindo cada valor por `1000`
- **AND** deve calcular a area em metros quadrados como `(base_mm / 1000) * (altura_mm / 1000)`
- **AND** deve calcular o total final como `area_m2 * espessura * preco_m2 * fator_base`
- **AND** o resultado deve ser retornado formatado em BRL para exibicao na interface

### Requirement: Interface publica reativa
O sistema SHALL oferecer uma interface publica para geracao de orcamentos com envio assíncrono via HTMX e renderizacao parcial sem reload.

#### Scenario: Usuario interage com a calculadora
- **WHEN** a pagina publica for carregada
- **THEN** o formulario deve exibir campo de nome do orcamento, data preenchida pelo backend e selects de tamanho, espessura, material e tipo de base carregados do banco
- **AND** a alteracao dos selects ou o acionamento do botao `Calcular` deve disparar uma requisicao HTMX ao backend
- **AND** a resposta deve atualizar apenas a regiao de resultado configurada em `hx-target`

### Requirement: Persistencia do historico da cotacao
O sistema SHALL preservar o historico do orcamento independentemente de mudancas futuras nas tabelas de preco.

#### Scenario: Orcamento salvo
- **WHEN** uma cotacao for confirmada para registro
- **THEN** o sistema deve gravar `valor_total` calculado e `detalhes_json` com snapshot de tamanho, espessura, material, base e valores numericos usados no calculo
- **AND** alteracoes futuras em materiais, espessuras, tamanhos ou bases nao devem modificar orcamentos ja registrados

### Requirement: Area administrativa autenticada
O sistema SHALL proteger a rota `/admin` por autenticacao de sessao com login e senha simples.

#### Scenario: Acesso nao autenticado ao admin
- **WHEN** um visitante acessar `/admin` sem sessao valida
- **THEN** o sistema deve redirecionar para a tela de login

#### Scenario: Acesso autenticado ao admin
- **WHEN** um usuario autenticado acessar `/admin`
- **THEN** o sistema deve exibir navegacao para CRUD de tamanhos, espessuras, materiais e tipos de base

### Requirement: CRUD administrativo de precos
O sistema SHALL permitir criar, listar, editar e excluir os cadastros usados pela calculadora.

#### Scenario: Atualizacao de tabela de precos
- **WHEN** o administrador salvar alteracoes em um cadastro
- **THEN** os novos valores devem ficar disponiveis imediatamente para a calculadora publica
- **AND** os registros historicos de `orcamentos` devem permanecer inalterados

### Requirement: Separacao da logica de calculo
O sistema SHALL manter a formula de orcamento isolada em um servico do backend, separado das views/controllers.

#### Scenario: Reuso da regra de negocio
- **WHEN** a rota publica de calculo ou o fluxo de persistencia precisar calcular um total
- **THEN** ambos devem reutilizar o mesmo servico de calculo

## MODIFIED Requirements
Nenhum neste change.

## REMOVED Requirements
Nenhum neste change.
