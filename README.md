# Web ERP

ERP multi-empresa em modelo SaaS: utilizadores, vendas, stock, facturação e contabilidade,
com regras fiscais de Moçambique e um pacote genérico para outros países.

- **Backend:** FastAPI, PostgreSQL 16 (com Row-Level Security), SQLAlchemy 2, Alembic
- **Frontend:** Next.js + TypeScript sobre o tema Able Pro (ver [frontend/README.md](frontend/README.md))
- **App offline:** Flutter (fase 4)

O plano de arquitetura completo está no documento do projecto.

## Estado: fase 0 (fundações)

- Registo de organizações (clientes SaaS) com a primeira empresa e o administrador
- Várias empresas por organização, troca de empresa sem novo login
- Isolamento entre empresas no PostgreSQL (RLS), além dos filtros na aplicação
- Login com JWT de 15 minutos e refresh token rotativo, bloqueio após 5 tentativas
- Papéis por empresa com permissões `modulo.recurso.accao`, 7 papéis criados por omissão
- Filiais e registo de auditoria

## Correr em desenvolvimento

```bash
docker compose up
```

A documentação interactiva da API fica em http://localhost:8000/api/v1/docs.

Sem Docker:

```bash
cd backend
python -m venv .venv && . .venv/bin/activate
pip install -e ".[dev]"
cp .env.example .env          # ajuste WEBERP_DATABASE_URL
alembic upgrade head
uvicorn app.main:app --reload
```

A aplicação tem de se ligar à base de dados com um utilizador **sem** privilégios de
superutilizador; um superutilizador ignora o RLS. Veja `deploy/postgres/init.sql`.

## Testes

Os testes precisam de um PostgreSQL com uma base `weberp_test` do utilizador `weberp`:

```bash
cd backend
pytest
ruff check . && ruff format --check .
```

## Estrutura

```
backend/app/
  core/        configuração, base de dados e RLS, segurança, erros, dependências
  shared/      modelos base, permissões, auditoria, paginação
  modules/
    auth/      registo, login, tokens, troca de empresa
    core/      organizações, empresas, filiais, auditoria
    users/     utilizadores, papéis, permissões
backend/migrations/   Alembic (inclui as políticas RLS)
frontend/             código do ERP para integrar no Able Pro
deploy/               nginx e inicialização do PostgreSQL
```
