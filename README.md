# TIP Trello Intelligence Platform

Backend Django modular para inteligência operacional executiva a partir de dados de Trello e fontes de trabalho equivalentes. O sistema consolida tarefas, eventos, métricas, consultas analíticas, relatórios executivos e trilhas de decisão em uma plataforma SaaS orientada a diagnóstico operacional.

Este README descreve a arquitetura real observada no código. Capacidades preparadas, parciais ou placeholders são identificadas explicitamente.

## 1. Visão Estratégica do Sistema

O TIP Trello Intelligence Platform resolve o problema de transformar dados operacionais dispersos em quadros de trabalho, especialmente Trello, em leitura executiva estruturada: indicadores, riscos, gargalos, narrativa gerencial, trilhas de decisão, relatórios exportáveis e acompanhamento de impacto.

O público-alvo natural é composto por gestores de operação, líderes de projeto, PMOs, consultorias e times executivos que precisam explicar o estado real da execução sem depender apenas de leitura manual de cards.

A proposta de valor implementada é:

- Capturar dados de ferramentas externas e normalizar tarefas em um modelo canônico.
- Persistir histórico operacional e eventos relevantes.
- Gerar métricas, relatórios e narrativas executivas com trilha auditável.
- Suportar ciclos piloto com decisão humana no fluxo.
- Evoluir para um produto SaaS multi-tenant com conectores, dashboards, exportações e camadas de inteligência.

O diferencial técnico está na combinação de:

- Projeções Trello detalhadas em `integrations.trello`.
- Motor canônico de integrações em `apps.integrations`.
- Serviços especializados em `apps.intelligence`, incluindo semantic layer, query engine, report query, observability, decision layer, organizational learning, business value e pilot loop.
- Geração documental em PDF, DOCX, PPTX e XLSX na camada de document generator.
- Validação operacional do próprio workspace via comandos de readiness.

## 2. Visão Arquitetural

### Modelo arquitetural identificado

O projeto é um monolito modular híbrido.

Ele não é uma Clean Architecture pura nem uma arquitetura hexagonal completa, porque modelos Django, views e serviços ainda compartilham dependências diretas de ORM e apps internos. Porém, há módulos com fronteiras claras e elementos de arquitetura hexagonal, principalmente no motor de integrações, onde provedores externos são acessados por adapters registrados em `IntegrationRegistry`.

Também há traços event-driven em filas de integração e tarefas Celery, mas o sistema não é integralmente orientado a eventos. A fila padrão é persistida em banco (`local_db`) e Celery aparece como backend configurável.

### Camadas reais

```text
Cliente/API
  -> tip_backend.urls
  -> Django/DRF APIViews e urls por app
  -> Serviços de aplicação
  -> Motores de domínio e pipelines
  -> ORM Django / PostgreSQL
  -> Integrações externas: Trello API e OpenAI API
  -> Cache local ou Redis
  -> Celery/Redis quando habilitado
```

### Fluxo de requisição

1. A requisição entra por `tip_backend.urls`.
2. O middleware `TenantContextMiddleware` extrai `X-Tenant-Id` ou `tenant_id` e grava o contexto de tenant em thread-local.
3. A rota delega para apps legados (`analytics`, `reports`, `ai`, `dashboard`, `integrations.trello`) ou para o namespace novo em `api/v1/`.
4. Views DRF chamam serviços de domínio, motores de consulta ou adapters.
5. Serviços consultam modelos Django, cache, APIs externas ou filas.
6. Logs e registros de auditoria persistem execução, métricas, relatórios e trilhas de decisão.

## 3. Estrutura do Projeto

```text
TIP_Trello_Intelligence_Platform/
├── ai/                       # Análise OpenAI legada, validação de resposta JSON e endpoints de IA
├── analytics/                # Métricas operacionais legadas e builders de dashboard analítico
├── apps/
│   ├── integrations/         # Motor canônico de integrações, adapters, fila e persistência normalizada
│   ├── data_sources/         # Endpoints de descoberta e sincronização de fontes de dados
│   ├── dashboards/           # Métricas e relatórios canônicos para dashboards
│   ├── intelligence/         # Núcleo de inteligência operacional e executiva
│   ├── reports/              # Endpoints de relatórios no namespace novo
│   ├── exports/              # Endpoints de exportação
│   ├── users/                # Login demo, perfil atual e catálogo de permissões
│   ├── settings/             # Configuração singleton do workspace
│   └── ai_insights/          # Endpoints de insights de IA no namespace novo
├── core/                     # Base models, tenant context, middleware, healthcheck e system APIs
├── dashboard/                # Dashboard legado
├── integrations/trello/      # Projeções Trello, cliente HTTP, sincronização e comando sync_trello_board
├── reports/                  # Relatórios legados e engine PDF
├── tip_backend/              # Settings, URLs, ASGI/WSGI e Celery app
├── docker-compose.yml        # PostgreSQL 16 e Redis 7 para desenvolvimento
└── frontend/                 # Portal frontend presente no workspace
```

O código mostra uma evolução de produto: módulos legados coexistem com uma camada `apps/*` mais orientada a SaaS, conectores, escopo, readiness e inteligência avançada. Isso aumenta a cobertura funcional, mas também cria duplicidade de conceitos entre namespaces antigos e novos.

## 4. Modelo de Domínio

### Entidades principais

- `core.Tenant`: fronteira comercial para isolamento SaaS.
- `integrations.trello.Board`: board Trello, com `tenant` opcional e manager tenant-aware.
- `integrations.trello.BoardList`: lista de board.
- `integrations.trello.Card`: card operacional, status, responsáveis, datas, labels e JSON bruto.
- `integrations.trello.Member`: membro Trello.
- `integrations.trello.Action`: log imutável de ações Trello.
- `integrations.trello.CardStatusHistory`: histórico append-only de transições de status.
- `integrations.trello.EntityHistory`: histórico append-only de revisões de entidades.
- `integrations.trello.Snapshot`: captura diária do estado de um board.
- `apps.integrations.IntegrationConnection`: conexão externa por provedor, tenant, workspace e projeto.
- `apps.integrations.CanonicalTaskRecord`: tarefa normalizada entre provedores.
- `apps.integrations.IntegrationState`: cursor e estado incremental de sincronização.
- `apps.integrations.IngestionQueueEvent`: evento persistido de fila de ingestão.
- `apps.intelligence.TimelineEvent`: linha do tempo operacional consolidada.
- `apps.intelligence.CardEnrichment`: contexto executivo enriquecido por card.
- `apps.intelligence.OperationalScoreSnapshot`: score operacional por board.
- `apps.intelligence.ReportAuditLog`: auditoria de geração de relatórios segmentados.
- `apps.intelligence.ReportQueryLog` e `ReportQueryExecutionTrace`: logs e rastreamento de consultas EQL.
- `apps.intelligence.DecisionRecord` e `ActionExecutionLog`: decisão recomendada e execução auditada.
- `apps.intelligence.OrganizationalMemory` e `PlaybookRecord`: memória organizacional e playbooks.
- `apps.intelligence.BusinessValueRecordModel`: valor financeiro estimado e realizado.
- `apps.intelligence.PilotConfig`, `PilotCycleRun`, `DecisionFeedbackRecord` e `ActionImpactFollowUp`: controle de piloto operacional humano no fluxo.
- `apps.settings.WorkspaceConfig`: configuração singleton do workspace.

### Agregados e relacionamentos críticos

O agregado operacional primário é o board Trello:

```text
Tenant
  -> Board
      -> BoardList
      -> Card
          -> Member
          -> CardStatusHistory
          -> CardEnrichment
      -> Action
      -> EntityHistory
      -> Snapshot
      -> TimelineEvent
      -> KnowledgeBaseEntry
      -> OperationalScoreSnapshot
```

O agregado de integração canônica é:

```text
Tenant
  -> IntegrationConnection
      -> IntegrationState
      -> CanonicalTaskRecord
      -> IngestionQueueEvent
```

O agregado de decisão e aprendizado é mais distribuído, identificado por `board_id`, `decision_id`, `trace_id` e campos textuais, não por FKs rígidas. Essa escolha facilita pipelines e auditoria, mas reduz integridade referencial entre decisões, ações, impacto e memória.

### Regras de negócio identificadas

- Boards podem ser filtrados automaticamente por tenant quando há tenant no contexto.
- Tarefas canônicas são únicas por conexão, provedor e `source_id`.
- Snapshots são únicos por board e data.
- Eventos de timeline vindos de ações são únicos por `source_action` e tipo.
- Consultas de relatório registram auditoria com filtros, quantidade de cards e tempo de processamento.
- A execução automática de ações é controlada por variáveis como `DAL_AUTO_EXECUTION`, limites por hora e cooldown.
- POCL é opcional e depende de `POCL_ENABLED`, `POCL_ACTIVE` e escopo de board.

## 5. Fluxos Críticos

### Autenticação

O app `apps.users` implementa um login demo. `LoginView` aceita credenciais fornecidas no payload e retorna `tip-demo-token`, usuário demo e permissões calculadas por role.

As views de usuário definem `authentication_classes = []` e `permission_classes = []`. Portanto, a autenticação atual é adequada para protótipo/demo, mas não é segurança enterprise real.

### Autorização

Há um catálogo de roles e permissões em `apps.permissions`:

- `viewer`
- `manager`
- `admin`

Essas permissões alimentam navegação e guards de frontend, mas o código analisado não demonstra enforcement global de RBAC no backend. Isso deve ser tratado como risco antes de produção.

### Sincronização de integrações

O motor novo de integrações segue este fluxo:

```text
IntegrationConnection
  -> SyncEngine
  -> IntegrationRegistry.get(provider)
  -> Adapter.sync(connection)
  -> CanonicalTaskRecord.update_or_create()
  -> connection.mark_synced()
  -> emit_sync_completed()
```

O Trello possui dois caminhos coexistentes:

- `integrations.trello`: projeções e sincronização Trello mais direta para boards, cards, listas, membros e ações.
- `apps.integrations.trello`: adapter, mapper, incremental sync e integração com o motor canônico.

### Relatórios executivos

`execute_report_query` executa a cadeia:

```text
ReportQueryPayload
  -> cache opcional
  -> build_filtered_cards
  -> generate_report
  -> card rows, métricas e agrupamentos
  -> analytical enrichment
  -> executive narrative
  -> discovery insights
  -> executive story
  -> output contract
  -> export opcional
  -> ReportAuditLog
```

Essa camada é uma das mais maduras do sistema porque combina contrato de saída, auditoria, cache, enriquecimento analítico e testes dedicados.

### Pipeline de inteligência

`run_intelligence_pipeline` orquestra:

1. Construção de timeline.
2. Enriquecimento de cards.
3. Extração de conhecimento.
4. Score operacional.
5. Relatório executivo.

O pipeline usa dados Trello persistidos e serviços especializados em `apps.intelligence.services`.

### Processamento assíncrono

Celery está configurado em `tip_backend.celery` e há tasks para:

- Despachar eventos de integração.
- Drenar worker Trello.
- Executar decision stream POCL.
- Rodar ciclos POCL diários.
- Medir follow-ups de impacto.

Redis é provisionado no `docker-compose.yml`. A fila de integração também suporta backends `local_sync`, `local_db`, `local_background`, `celery` e placeholder `kafka`.

### Integrações externas

- Trello: cliente HTTP com API Key + Token, timeout de 30 segundos e endpoints para member, workspaces, boards, lists e cards.
- OpenAI: análise estruturada por JSON, com validação de chaves obrigatórias e compactação prévia das métricas.

## 6. Estratégia de Segurança

### Implementado

- `SECRET_KEY`, hosts, banco, Celery, CORS, Trello e OpenAI são lidos de variáveis de ambiente.
- `prod.py` força `DEBUG = False`, cookies seguros, SSL redirect, `X_FRAME_OPTIONS = DENY` e proteção de content sniffing.
- Credenciais sensíveis de integração podem ser criptografadas com Fernet em `apps.integrations.core.credentials`.
- Existe fallback de chave criptográfica derivada de `SECRET_KEY` quando `INTEGRATION_CREDENTIALS_KEY` não é configurada.
- `TenantContextMiddleware` injeta tenant por header ou query param.
- `TenantScopedManager` filtra automaticamente modelos tenant-aware quando há tenant no contexto.

### Riscos

- Login atual é placeholder e aceita qualquer credencial.
- Token retornado é fixo (`tip-demo-token`).
- Não há autenticação DRF global configurada em `REST_FRAMEWORK`.
- O tenant pode ser escolhido por header/query param sem validação contra usuário autenticado.
- RBAC existe como catálogo, mas não aparece como enforcement consistente no backend.
- Credenciais salvas antes da criptografia ou sem `INTEGRATION_CREDENTIALS_KEY` forte podem depender do `SECRET_KEY`.

## 7. Estratégia Multi-Tenant

O sistema possui base multi-tenant, mas ainda incompleta para produção.

Evidências implementadas:

- `core.Tenant` representa conta comercial.
- `Board.tenant` e `IntegrationConnection.tenant` associam dados a tenant.
- `TenantContextMiddleware` extrai tenant da requisição.
- `TenantScopedManager` aplica filtro automático quando existe tenant no contexto.
- Testes de escopo existem em `apps.dashboards.tests.test_scope`.

Limitações:

- Nem todos os modelos carregam FK de tenant.
- Muitos registros de inteligência usam `board_id` textual em vez de FK tenant-aware.
- O middleware confia em identificador recebido na requisição.
- Não há garantia global, no código analisado, de que usuário autenticado pertence ao tenant informado.

## 8. Estratégia de Persistência

O banco principal é PostgreSQL, configurado em `tip_backend.settings.base`. O `docker-compose.yml` sobe PostgreSQL 16 em `localhost:5433`.

O sistema usa ORM Django com:

- FKs para relações centrais.
- Índices em campos de consulta frequente.
- `UniqueConstraint` para identidade externa, snapshots, eventos e caches.
- JSONField para payloads externos, metadados canônicos, auditoria, traces e saídas analíticas.
- Migrations por app.

Há modo de teste com SQLite quando `EOR_TESTING=true` e `EOR_TEST_DATABASE_ENGINE=sqlite`.

O padrão de consulta mistura:

- ORM direto em services.
- Managers tenant-aware.
- Query builders de relatório.
- Projeções canônicas em banco.
- Cache para consultas de relatório.

## 9. Estratégia de Escalabilidade

### Escalabilidade horizontal

O monolito pode escalar horizontalmente como aplicação Django stateless em boa parte dos endpoints, desde que:

- Banco e Redis estejam externos ao processo.
- Workers Celery sejam separados.
- Chaves de criptografia e variáveis de ambiente sejam consistentes entre instâncias.

### Cache

`CACHES` usa Redis quando `REDIS_CACHE_URL` está definido. Sem isso, usa `LocMemCache`, adequado para desenvolvimento, mas inconsistente entre múltiplos processos.

### Filas

Celery existe para workloads assíncronos. O motor de integração possui fila local em banco por padrão e backend Celery opcional.

### Gargalos identificados

- Pipelines de inteligência e relatório podem se tornar caros se executados sincronicamente em requests.
- Uso extensivo de JSONField favorece flexibilidade, mas pode dificultar consultas analíticas pesadas sem índices específicos.
- Namespace legado e namespace novo coexistem, aumentando risco de duplicidade e inconsistência de comportamento.
- `local_db` como fila padrão simplifica operação, mas não substitui broker assíncrono para alto volume.

## 10. Estratégia de Observabilidade

Implementado:

- Logging console com formato verbose.
- `ReportAuditLog` para geração de relatórios.
- `ReportQueryLog` e `ReportQueryExecutionTrace` para EQL.
- `DecisionTraceRecord` para decisões.
- `ActionExecutionLog` para ações.
- Serviços dedicados em `apps.intelligence.services.observability`.
- Variável `EOR_DEBUG_MODE` para incluir trace completo em respostas.

Pontos cegos:

- Não há integração explícita com APM externo.
- Não há tracing distribuído.
- Não há métricas Prometheus/OpenTelemetry configuradas.
- Logs estruturados existem parcialmente via registros de domínio, mas o logging padrão ainda é console.

## 11. Estratégia de Deploy

### Desenvolvimento

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
docker compose up -d
python manage.py migrate
python manage.py runserver
```

Healthcheck:

```bash
curl http://127.0.0.1:8000/health/
```

### Serviços

O `docker-compose.yml` provisiona:

- PostgreSQL 16 Alpine
- Redis 7 Alpine

Não há Dockerfile de aplicação no conjunto analisado. Portanto, o deploy da aplicação Django ainda depende de empacotamento externo.

### Variáveis críticas

- `DJANGO_SETTINGS_MODULE`
- `DJANGO_SECRET_KEY`
- `DJANGO_ALLOWED_HOSTS`
- `POSTGRES_*`
- `CELERY_BROKER_URL`
- `CELERY_RESULT_BACKEND`
- `REDIS_CACHE_URL`
- `TRELLO_API_KEY`
- `TRELLO_API_TOKEN`
- `OPENAI_API_KEY`
- `OPENAI_MODEL`
- `INTEGRATION_CREDENTIALS_KEY`
- `INTEGRATION_QUEUE_BACKEND`
- `EOR_DEBUG_MODE`
- `EOR_SAFE_MODE`
- `DAL_AUTO_EXECUTION`
- `POCL_ENABLED`
- `POCL_ACTIVE`
- `POCL_BOARD_ID`

### Comandos operacionais relevantes

```bash
python manage.py validate_eor_workspace --json
python manage.py validate_eor
python manage.py validate_report_quality
python manage.py report_query
python manage.py generate_demo_package
python manage.py eor_release_gate
python manage.py sync_trello_board
celery -A tip_backend worker -l info
```

## 12. Enterprise Readiness Assessment

| Critério | Nota | Justificativa |
|---|---:|---|
| Maturidade arquitetural | 3.5/5 | Há modularidade real, serviços especializados, pipelines e comandos de validação. A coexistência de módulos legados e novos reduz clareza de fronteiras. |
| Escalabilidade | 3/5 | PostgreSQL, Redis, cache e Celery estão previstos. Porém, workloads críticos ainda podem rodar sincronicamente e a fila padrão local em banco não é ideal para alto volume. |
| Modularidade | 3.5/5 | `apps.integrations` e `apps.intelligence` possuem separação significativa. Ainda há acoplamento direto a ORM, Trello legado e IDs textuais distribuídos. |
| Segurança | 2/5 | Settings de produção e criptografia de credenciais existem, mas autenticação real, token seguro, RBAC backend e vínculo usuário-tenant ainda não estão implementados de forma enterprise. |
| Testabilidade | 4/5 | Há testes para métricas, builders, permissões, integrações, report query, EQL, decisão, semantic layer, document generator, observabilidade, pilot e readiness. |

Nota geral: 3.2/5.

O sistema está acima de um protótipo simples por volume de domínio, testes e mecanismos de auditoria, mas ainda não deve ser considerado production-ready enterprise sem endurecimento de autenticação, autorização, tenant isolation e deploy.

## 13. Roadmap Arquitetural Evolutivo

### Refatorações recomendadas

- Consolidar responsabilidades entre namespaces legados (`analytics`, `reports`, `ai`, `dashboard`, `integrations.trello`) e namespace novo (`apps/*`).
- Definir contratos públicos por módulo e reduzir imports cruzados diretos.
- Padronizar IDs críticos: substituir campos textuais por FKs quando a integridade referencial for necessária.
- Separar comandos, pipelines síncronos e jobs assíncronos com contratos idempotentes.

### Segurança e multi-tenancy

- Implementar autenticação real no backend: JWT, session auth corporativa ou provedor OIDC.
- Substituir `tip-demo-token` por token verificável.
- Aplicar permissões DRF por endpoint.
- Validar `tenant_id` contra usuário autenticado.
- Tornar tenant obrigatório nos dados comerciais.
- Revisar modelos de inteligência que usam apenas `board_id` textual.
- Exigir `INTEGRATION_CREDENTIALS_KEY` forte em produção.

### Escalabilidade

- Tornar Celery obrigatório para pipelines pesados.
- Usar Redis compartilhado para cache em produção.
- Criar políticas de retenção para logs, traces e JSONs analíticos.
- Avaliar índices específicos para campos JSON consultados com frequência.
- Substituir backend `local_db` por Celery ou broker dedicado em cenários de alto volume.

### Observabilidade

- Adotar logs estruturados JSON.
- Integrar APM ou OpenTelemetry.
- Expor métricas de latência, erros, cache hit, uso de IA, tempo de sync e filas.
- Criar dashboards operacionais para commands de readiness e geração documental.

### Deploy

- Criar Dockerfile de aplicação.
- Separar configurações de dev, staging e production.
- Adicionar pipeline CI com testes, migrations check, lint e comandos de readiness.
- Documentar runbooks de sincronização Trello, geração de pacote demo e validação de release.

## Comandos de Verificação

Use estes comandos antes de alterações arquiteturais ou entrega:

```bash
python manage.py validate_eor_workspace --json
python manage.py check
python manage.py test
```

Para validar a qualidade de relatórios, use:

```bash
python manage.py validate_report_quality
```

Quando o banco local PostgreSQL não estiver disponível, use os modos de fixture/teste disponíveis nos comandos específicos antes de concluir que a funcionalidade falhou.
