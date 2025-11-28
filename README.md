# Sistema de Autenticação de Usuários

Sistema de autenticação completo usando FastAPI, PostgreSQL, Docker e PDM.

## Estrutura do Projeto

```
user-auth-system/
├── pyproject.toml
├── docker-compose.yml
├── Dockerfile
├── .env.example
├── app/
│   ├── __init__.py
│   ├── main.py
│   ├── database.py
│   ├── models.py
│   ├── schemas.py
│   ├── auth.py
│   └── crud.py
└── scripts/
    └── init_db.py
```

## Pré-requisitos

- Python 3.12+
- Docker e Docker Compose
- PDM (Python Dependency Manager)

## Instalação

### 1. Instalar PDM

```bash
pip install pdm
```

### 2. Configurar variáveis de ambiente

Copie o arquivo `.env.example` para `.env` e ajuste as variáveis conforme necessário:

```bash
cp .env.example .env
```

### 3. Instalar dependências

```bash
pdm install
```

## Como Executar

### Opção 1: Usando Docker Compose (Recomendado)

```bash
# Build e execução
docker-compose up --build

# Ou em background
docker-compose up -d
```

### Opção 2: Executar localmente

```bash
# Iniciar banco de dados
docker-compose up postgres -d

# Executar aplicação
pdm run python -m app.main

# Ou com uvicorn diretamente
pdm run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## Endpoints da API

### Registrar usuário

```bash
curl -X POST "http://localhost:8000/register" \
     -H "Content-Type: application/json" \
     -d '{
       "email": "usuario@exemplo.com",
       "username": "usuario",
       "full_name": "Usuário Teste",
       "password": "senha123"
     }'
```

### Login

```bash
curl -X POST "http://localhost:8000/login" \
     -H "Content-Type: application/x-www-form-urlencoded" \
     -d "username=usuario&password=senha123"
```

### Acessar perfil (com token)

```bash
curl -X GET "http://localhost:8000/users/me" \
     -H "Authorization: Bearer SEU_TOKEN_AQUI"
```

## Documentação Interativa

Após iniciar a aplicação, acesse:

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Tecnologias Utilizadas

- **FastAPI**: Framework web moderno e rápido
- **PostgreSQL**: Banco de dados relacional
- **SQLAlchemy**: ORM para Python
- **JWT**: Autenticação baseada em tokens
- **Docker**: Containerização
- **PDM**: Gerenciador de dependências Python

