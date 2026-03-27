# ApiGenerator

ApiGenerator is a python project that takes SQL DDL schema input and generates a ready-to-run backend project from it

---

## Run with Docker

### Requirements

- Docker Desktop (or Docker Engine + Compose plugin)
- Git

### 1) Clone project

```bash
git clone https://github.com/noilq/ApiGenerator.git
cd ApiGenerator
```

### 2) Start project

```bash
docker compose up --build
```

Builds all services and starts the full stack

- `gateway` (public entrypoint) on `localhost:8000`
- `ingestion` on `localhost:8001`
- `normalizer` on `localhost:8002`
- `generator` on `localhost:8003`
- `exporter` on `localhost:8004`

### 3) Stop

```bash
docker compose down
```

### How to use

(Currently only via POST localhost:8000/api/generate endpoint)

TODO

---

## Technical overview

This project is designed as a system, where each service has one clear responsibility, and the `gateway` orchestrates the whole flow

### High-level architecture

- `gateway` service receives the main API request and coordinates all internal services
- `ingestion` service parses incoming SQL DDL into structured models
- `normalizer` service standardizes data types and schema relations
- `generator` service renders project files from Jinja templates
- `exporter` service writes generated files to disk and returns URL's to download and browse repo
- `shared` package keeps common data models and logging setup used by multiple services

### Pipeline used by gateway

Main orchestration lives in `services/gateway/app/orchestration.py`

1. `ingest(...)` -> parse raw SQL into table models
2. `normalize(...)` -> apply type mapping + dependency ordering
3. `generate(...)` -> render code files from templates
4. `export(...)` -> save generated project and return URL's

### Repository structure

```text
ApiGenerator2/
  docker-compose.yml
  docker-compose.override.yml
  JenkinsFile
  shared/
    models.py
    logging_config.py
  services/
    gateway/
      app/
        main.py
        routers/
        clients/
        orchestration.py
    ingestion/
      app/
        main.py
        strategy.py
        parsers/
      tests/
    normalizer/
      app/
        main.py
        normalizer.py
      tests/
    generator/
      app/
        main.py
        generator.py
        templates/
          python/...
          shared/...
    exporter/
      app/
        main.py
        exporter.py
```

### Service-by-service details

#### 1) Gateway (`services/gateway`)

- Public API entrypoint (`/api/...`)
- Accepts generation request DTO (`GenerateRequest`)
- Calls internal services
- Returns download/view endpoints for generated projects

Main endpoint

- `POST /api/generate`

#### 2) Ingestion (`services/ingestion`)

- Converts raw SQL DDL into `TableModel` objects
- Currently implemented parsers: SQLite

Main endpoint

- `POST /ingest`

#### 3) Normalizer (`services/normalizer`)

- Maps raw database types to internal application types (`int`, `str`, `datetime`, etc)
- Detects enum-like `CHECK` constraints
- Ensures indexes for FK columns
- Sorts tables in dependency order

Main endpoint

- `POST /normalize`

#### 4) Generator (`services/generator`)

- Uses `jinja2` templates to generate source code files
- Supports configurable target stack via options
  - language
  - framework
  - ORM
  - version
  - auth / CI-CD / docker toggles
- Includes custom template filters (snake_case, pascal_case, type mapping, enum parsing)
- Returns file map `{"path/to/file.py": "file content"}`

Main endpoint

- `POST /generate`

#### 5) Exporter (`services/exporter`)

- Writes generated files into `generated_projects` volume
- Cleans previous folder for same project name
- Returns URLs to download and browse repo

Main endpoint

- `POST /export`

### Shared files

`shared/models.py` contains the core schema for different services

- `TableModel`
- `ColumnModel`
- `ForeignKeyModel`
- `IndexModel`
- `PartitionModel`

### Template system

Templates live in `services/generator/app/templates/`

- Stack-specific templates are inside paths like
  - `python/fastapi/sqlalchemy/v1_0/...`
- Optional shared addons are in
  - `shared/docker/...`
  - `shared/<language>/auth/...`
  - `shared/ci_cd/...`

### Custom template implementation

TODO