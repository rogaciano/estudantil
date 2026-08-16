# Tasks

- [x] Task 1: Estruturar o projeto Django para o sistema de orcamentos em acrilico.
  - [x] SubTask 1.1: Criar o projeto/app base com configuracao para SQLite, templates e arquivos estaticos minimos.
  - [x] SubTask 1.2: Configurar rotas iniciais para a area publica, autenticacao simples e area administrativa customizada em `/admin`.

- [x] Task 2: Implementar a modelagem relacional e a carga inicial do catalogo.
  - [x] SubTask 2.1: Criar models e migrations para `tamanhos`, `espessuras`, `materiais`, `tipos_bases` e `orcamentos`.
  - [x] SubTask 2.2: Criar seed/script inicial com os dados padrao de tamanhos, espessuras, materiais e bases.
  - [x] SubTask 2.3: Validar tipos numericos, precisao decimal e campos obrigatorios.

- [x] Task 3: Implementar a regra de negocio de calculo em servico isolado.
  - [x] SubTask 3.1: Criar servico que converte milimetros para metros, calcula area e retorna `valor_total`.
  - [x] SubTask 3.2: Garantir formatacao monetaria BRL para exibicao na resposta da interface.
  - [x] SubTask 3.3: Cobrir a formula com testes automatizados do backend.

- [x] Task 4: Construir a calculadora publica com HTML, Tailwind e HTMX.
  - [x] SubTask 4.1: Criar template publico com campo `nome_orcamento`, data vinda do backend e selects alimentados pelo banco.
  - [x] SubTask 4.2: Implementar endpoint HTMX para recalcular o valor sem reload completo.
  - [x] SubTask 4.3: Exibir parcial de resultado com valor total formatado e estado de erro amigavel.

- [x] Task 5: Persistir o historico de orcamentos com snapshot dos dados.
  - [x] SubTask 5.1: Definir fluxo para registrar o orcamento calculado na tabela `orcamentos`.
  - [x] SubTask 5.2: Salvar em `detalhes_json` os dados usados no calculo para preservar historico.
  - [x] SubTask 5.3: Cobrir o salvamento com testes de integracao ou request tests.

- [x] Task 6: Construir a area administrativa autenticada para manutencao das tabelas.
  - [x] SubTask 6.1: Implementar login/logout com sessao e protecao de acesso.
  - [x] SubTask 6.2: Criar telas CRUD em HTML/Tailwind para tamanhos, espessuras, materiais e tipos de base.
  - [x] SubTask 6.3: Garantir validacoes e feedback visual de sucesso/erro nas operacoes administrativas.

- [x] Task 7: Validar o fluxo completo e preparar os entregaveis esperados.
  - [x] SubTask 7.1: Verificar rotas, controllers/views, servico de calculo, migrations/seeds e templates HTMX.
  - [x] SubTask 7.2: Executar testes principais do backend e revisar o fluxo manual da calculadora e do admin.

- [x] Task 8: Corrigir achados da verificacao final.
  - [x] SubTask 8.1: Corrigir a atualizacao HTMX da calculadora para sempre refletir os valores atuais do formulario.
  - [x] SubTask 8.2: Alinhar a nomenclatura acentuada de materiais e base entre seed, spec e checklist.
  - [x] SubTask 8.3: Reexecutar os testes e a validacao manual dos fluxos impactados.

# Task Dependencies
- Task 2 depends on Task 1
- Task 3 depends on Task 2
- Task 4 depends on Task 1, Task 2 and Task 3
- Task 5 depends on Task 3 and Task 4
- Task 6 depends on Task 1 and Task 2
- Task 7 depends on Task 3, Task 4, Task 5 and Task 6
- Task 8 depends on Task 7

# Parallel Work Notes
- Task 6 pode iniciar depois de Task 1 e Task 2, em paralelo com Task 4.
- SubTask 2.2 pode ocorrer em paralelo com SubTask 2.3 apos a definicao das tabelas.
