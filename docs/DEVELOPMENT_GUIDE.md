# Guía de Desarrollo para Aegra

Esta guía te enseña cómo desarrollar en Aegra y contribuir al proyecto open source.

## Tabla de Contenidos

- [Flujo de Implementación](#flujo-de-implementación)
- [Desarrollo Local](#desarrollo-local)
- [Testing](#testing)
- [Contribución Open Source](#contribución-open-source)
- [Convenciones del Proyecto](#convenciones-del-proyecto)
- [Comandos Git Útiles](#comandos-git-útiles)
- [Troubleshooting](#troubleshooting)

---

## Flujo de Implementación

### 1. Crear tu Grafo (Agente)

Crea un archivo en la carpeta `graphs/`:

```python
# graphs/mi_agente.py
from langgraph.graph import StateGraph
from typing import TypedDict

class MiEstado(TypedDict):
    messages: list[str]
    resultado: str

# Definir workflow
workflow = StateGraph(MiEstado)

# Agregar nodos
workflow.add_node("procesar", lambda state: {"resultado": "Procesado!"})

# Agregar edges
workflow.add_edge("__start__", "procesar")
workflow.add_edge("procesar", "__end__")

# IMPORTANTE: Debe exportarse como 'graph'
graph = workflow.compile()
```

---

### 2. Registrar en aegra.json

```json
{
  "graphs": {
    "mi_agente": "./graphs/mi_agente.py:graph",
    "otro_agente": "./graphs/otro_agente.py:graph"
  },
  "auth": {
    "path": "./auth.py:auth"
  }
}
```

**Formato:** `"nombre_api": "ruta/al/archivo.py:nombre_variable"`

---

### 3. Agregar Dependencias (si necesitás)

Edita `pyproject.toml`:

```toml
[project]
dependencies = [
    # ... dependencias existentes
    "requests>=2.31.0",  # Tu nueva dependencia
    "beautifulsoup4>=4.12.0",
]
```

Luego sincroniza:

```bash
uv sync
```

---

### 4. Aplicar Migraciones de Base de Datos

```bash
# IMPORTANTE: Activar virtual environment primero
source .venv/bin/activate

# Aplicar migraciones
python3 scripts/migrate.py upgrade

# Ver estado actual
python3 scripts/migrate.py current

# Ver historial
python3 scripts/migrate.py history
```

---

### 5. Iniciar el Servidor

**Opción A: Desarrollo Local (Recomendado para desarrollo activo)**

```bash
# Iniciar solo PostgreSQL
docker compose up postgres -d

# Iniciar servidor con hot reload
uv run uvicorn src.agent_server.main:app --reload

# Con puerto específico
uv run uvicorn src.agent_server.main:app --host 0.0.0.0 --port 8000 --reload
```

**Ventajas:**
- Hot reload instantáneo en cambios de código
- Logs directos en terminal
- Fácil debugging

---

**Opción B: Docker Completo (Recomendado para testing)**

```bash
# Rebuild solo si cambiaste dependencias
docker compose build aegra

# Iniciar todo
docker compose up aegra

# En background
docker compose up aegra -d
```

**Ventajas:**
- Entorno idéntico a producción
- Migraciones automáticas
- Setup completo en un comando

---

### 6. Verificar que Funciona

```bash
# Health check
curl http://localhost:8000/health

# Debería retornar:
# {
#   "status": "healthy",
#   "database": "connected",
#   "checkpointer": "connected",
#   "store": "connected"
# }
```

---

### 7. Probar tu Agente

#### Crear Assistant

```bash
curl -X POST http://localhost:8000/assistants \
  -H "Content-Type: application/json" \
  -d '{
    "graph_id": "mi_agente",
    "config": {}
  }'

# Respuesta:
# {
#   "assistant_id": "asst_abc123...",
#   "graph_id": "mi_agente",
#   "created_at": "2025-11-05T...",
#   ...
# }
```

#### Crear Thread

```bash
curl -X POST http://localhost:8000/threads

# Respuesta:
# {
#   "thread_id": "thread_xyz789...",
#   "created_at": "2025-11-05T...",
#   ...
# }
```

#### Crear Run

```bash
curl -X POST http://localhost:8000/threads/thread_xyz789/runs \
  -H "Content-Type: application/json" \
  -d '{
    "assistant_id": "asst_abc123",
    "input": {
      "messages": ["Hola, procesa esto!"]
    }
  }'

# Respuesta:
# {
#   "run_id": "run_123...",
#   "status": "pending",
#   ...
# }
```

#### Ver Resultado del Run

```bash
curl http://localhost:8000/threads/thread_xyz789/runs/run_123
```

---

## Desarrollo Local

### Setup Inicial (Primera Vez)

```bash
# 1. Instalar dependencias
uv install

# 2. Activar virtual environment
source .venv/bin/activate

# 3. Iniciar base de datos
docker compose up postgres -d

# 4. Aplicar migraciones
python3 scripts/migrate.py upgrade

# 5. Iniciar servidor
uv run uvicorn src.agent_server.main:app --reload
```

---

### Flujo Día a Día

```bash
# Iniciar PostgreSQL (si no está corriendo)
docker compose up postgres -d

# Iniciar servidor
uv run uvicorn src.agent_server.main:app --reload

# Editar código en src/ o graphs/
# → Hot reload automático ✨

# Ver logs en tiempo real en la terminal
```

---

### Cuándo Necesitás Rebuild de Docker

**SÍ necesitás rebuild:**
- ✅ Cambiaste `pyproject.toml` (nuevas dependencias)
- ✅ Cambiaste `uv.lock`
- ✅ Modificaste `Dockerfile`

```bash
docker compose build aegra --no-cache
docker compose up aegra
```

**NO necesitás rebuild:**
- ❌ Cambiaste código en `src/` (hot reload via volume mount)
- ❌ Cambiaste grafos en `graphs/` (volume mount)
- ❌ Modificaste `aegra.json` (volume mount)
- ❌ Modificaste `auth.py` (volume mount)

Solo necesitás reiniciar:
```bash
docker compose restart aegra
```

---

### Variables de Entorno

Crea un archivo `.env` en la raíz del proyecto:

```bash
# Base de datos
DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/aegra

# Autenticación
AUTH_TYPE=noop  # o "custom"

# Debug
DEBUG=true

# Puerto
PORT=8000

# Logging
DATABASE_ECHO=false  # true para ver SQL queries
```

---

## Testing

### Ejecutar Tests

```bash
# Todos los tests
uv run pytest

# Con verbose
uv run pytest -v

# Con async support
uv run pytest -v --asyncio-mode=auto

# Test específico
uv run pytest tests/test_api/test_assistants.py

# Con coverage
uv run pytest --cov=src --cov-report=html

# Ver coverage report
open htmlcov/index.html  # macOS
# xdg-open htmlcov/index.html  # Linux
```

---

### Escribir Tests

```python
# tests/test_mi_feature.py
import pytest
from httpx import AsyncClient
from src.agent_server.main import app

@pytest.mark.asyncio
async def test_crear_assistant():
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post(
            "/assistants",
            json={"graph_id": "mi_agente", "config": {}}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["graph_id"] == "mi_agente"
```

**Convenciones:**
- Tests en carpeta `tests/`
- Archivos `test_*.py` o `*_test.py`
- Funciones `test_*()`
- Usar `@pytest.mark.asyncio` para tests async

---

## Contribución Open Source

### 1. Fork y Clone

```bash
# 1. Fork en GitHub (botón "Fork" arriba a la derecha)
#    https://github.com/ibbybuilds/aegra → Fork

# 2. Clonar TU fork
git clone https://github.com/TU_USUARIO/aegra.git
cd aegra

# 3. Agregar upstream (repo original)
git remote add upstream https://github.com/ibbybuilds/aegra.git

# 4. Verificar
git remote -v
# origin    https://github.com/TU_USUARIO/aegra.git (tu fork)
# upstream  https://github.com/ibbybuilds/aegra.git (original)
```

---

### 2. Crear Branch para tu Feature

```bash
# Asegurarte de estar en main actualizado
git checkout main
git pull upstream main

# Crear branch descriptiva
git checkout -b feat/redis-integration

# Convenciones de nombres:
# feat/     → Nueva funcionalidad
# fix/      → Bug fix
# docs/     → Documentación
# refactor/ → Refactorización
# test/     → Tests
# chore/    → Mantenimiento
```

---

### 3. Hacer tus Cambios

```bash
# Editar archivos...

# Ver cambios
git status
git diff

# Agregar al staging
git add src/agent_server/core/database.py
git add pyproject.toml

# O agregar todo
git add .

# Commit con mensaje descriptivo
git commit -m "feat: add Redis support for checkpointer and store

- Replace AsyncPostgresSaver with AsyncRedisSaver
- Add langgraph-checkpoint-redis dependency
- Update DatabaseManager to support Redis URL
- Add Redis configuration to docker-compose.yml

Closes #82"
```

**Tips para buenos commits:**
- Primera línea: resumen conciso (50 caracteres)
- Línea en blanco
- Descripción detallada (72 caracteres por línea)
- Referencias a issues: `Closes #82`, `Fixes #45`

---

### 4. Ejecutar Tests

```bash
# Correr todos los tests
uv run pytest

# Verificar que pasan
uv run pytest -v --asyncio-mode=auto

# Si hay linter configurado
# uv run ruff check .
# uv run ruff format .
```

---

### 5. Push a tu Fork

```bash
# Push a origin (tu fork), NO a upstream (original)
git push origin feat/redis-integration

# Primera vez que pusheas esta branch:
git push -u origin feat/redis-integration
```

---

### 6. Crear Pull Request

1. **Ir a GitHub** (tu fork o el repo original)
2. Verás un banner: `"feat/redis-integration had recent pushes"`
3. Click en **"Compare & pull request"**

**Título del PR:**
```
feat: Add Redis support for LangGraph checkpointer
```

**Descripción del PR:**
```markdown
## Summary
Adds Redis as an alternative backend for LangGraph checkpoints and store.

## Changes
- ✅ Replace `AsyncPostgresSaver` with `AsyncRedisSaver`
- ✅ Add `langgraph-checkpoint-redis` dependency
- ✅ Update `DatabaseManager` to support Redis URL format
- ✅ Add Redis service to `docker-compose.yml`
- ✅ Update documentation with Redis setup instructions

## Test Plan
- [x] All existing tests pass
- [x] Added integration tests for Redis checkpointer
- [x] Tested with Redis Stack 7.2
- [x] Health check endpoint works with Redis
- [x] Checkpoints persist correctly across restarts

## Breaking Changes
None - PostgreSQL remains the default backend.

## Documentation
- Updated `README.md` with Redis setup instructions
- Added `docs/REDIS_SETUP.md` with detailed configuration

## Related Issues
Closes #82

---

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>
```

4. **Asegurarte de que:**
   - Base branch: `main` (del repo original)
   - Compare branch: `feat/redis-integration` (de tu fork)

5. Click **"Create pull request"**

---

### 7. Responder a Code Review

Los maintainers revisarán tu código y pueden pedir cambios:

```bash
# Hacer los cambios solicitados
# Editar código...

# Commit de los cambios
git add .
git commit -m "fix: add error handling for Redis connection failures"

# Push a la misma branch
git push origin feat/redis-integration

# El PR se actualizará automáticamente ✨
```

---

### 8. Mantener tu Branch Actualizada

Si el repo original tuvo cambios mientras trabajabas:

```bash
# Traer cambios de upstream
git fetch upstream

# Rebase tu branch sobre main actualizado
git rebase upstream/main

# Si hay conflictos, resolverlos
# Editar archivos en conflicto...
git add .
git rebase --continue

# Force push (solo en TU branch de feature, nunca en main)
git push origin feat/redis-integration --force
```

---

### 9. Después del Merge

```bash
# Actualizar tu fork's main
git checkout main
git pull upstream main
git push origin main

# Eliminar branch local (opcional)
git branch -d feat/redis-integration

# Eliminar branch remota (opcional)
git push origin --delete feat/redis-integration
```

---

## Convenciones del Proyecto

### Commit Messages (Conventional Commits)

Aegra sigue **Conventional Commits**:

```
<tipo>(<scope>): <descripción corta>

<descripción detallada opcional>

<footer opcional>
```

**Tipos:**
- `feat`: Nueva funcionalidad
- `fix`: Bug fix
- `docs`: Cambios en documentación
- `test`: Agregar o modificar tests
- `refactor`: Refactorización (sin cambiar funcionalidad)
- `chore`: Mantenimiento, dependencias
- `style`: Formato, espacios (no afecta código)
- `perf`: Mejoras de performance
- `ci`: Cambios en CI/CD

**Ejemplos:**

```bash
feat: add Redis checkpointer support

fix: resolve assistant creation race condition

docs: improve PostgreSQL inspection guide

test: add integration tests for store TTL

refactor: simplify DatabaseManager initialization

chore: update langgraph to v0.2.0
```

---

### Estructura de un Buen PR

**✅ Buenos PRs:**
- Un solo feature/fix por PR
- Tests incluidos
- Documentación actualizada
- Commits limpios y descriptivos
- Referencia a issues relevantes
- Descripción clara del problema y solución

**❌ Malos PRs:**
- Múltiples features no relacionados
- Sin tests
- Commits tipo "fix", "update", "changes"
- Breaking changes sin avisar
- Sin documentación
- Sin contexto sobre el problema

---

### Checklist Antes de Crear PR

```markdown
- [ ] Fork del repo original
- [ ] Branch descriptiva creada (feat/*, fix/*)
- [ ] Cambios implementados
- [ ] Tests agregados/actualizados
- [ ] Todos los tests pasan (`uv run pytest`)
- [ ] Commits con mensajes descriptivos (Conventional Commits)
- [ ] Documentación actualizada (si aplica)
- [ ] Push a tu fork
- [ ] PR creado con descripción completa
- [ ] Vinculado a issue relevante (Closes #XX)
- [ ] No hay conflictos con main
```

---

### Code Style

**Python:**
- PEP 8 compliant
- Type hints cuando sea posible
- Docstrings para funciones públicas
- Imports ordenados (stdlib, third-party, local)

**Ejemplos:**

```python
from typing import Optional, Dict, Any
from datetime import datetime

from fastapi import APIRouter, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from src.agent_server.core.database import DatabaseManager
from src.agent_server.models import Assistant


async def create_assistant(
    graph_id: str,
    config: Optional[Dict[str, Any]] = None,
    session: AsyncSession,
) -> Assistant:
    """Create a new assistant with the given graph_id.

    Args:
        graph_id: The ID of the graph to use
        config: Optional configuration dict
        session: Database session

    Returns:
        The created Assistant instance

    Raises:
        HTTPException: If graph_id is invalid
    """
    if config is None:
        config = {}

    # Implementation...
    return assistant
```

---

## Comandos Git Útiles

### Información

```bash
# Ver estado
git status

# Ver diferencias
git diff
git diff --staged  # Solo lo que está en staging

# Ver historial
git log --oneline
git log --graph --oneline --all  # Visual

# Ver branches
git branch -a  # Todas (local + remote)
git branch     # Solo locales
```

---

### Cambios

```bash
# Deshacer cambios (archivo no staged)
git checkout -- archivo.py
# O en Git 2.23+
git restore archivo.py

# Deshacer staging
git reset HEAD archivo.py
# O en Git 2.23+
git restore --staged archivo.py

# Editar último commit
git commit --amend
git commit --amend --no-edit  # Mantener mensaje

# Deshacer último commit (mantener cambios)
git reset --soft HEAD~1

# Deshacer último commit (descartar cambios)
git reset --hard HEAD~1
```

---

### Stash (Guardar Cambios Temporalmente)

```bash
# Guardar cambios
git stash
git stash save "WIP: working on feature X"

# Ver stashes
git stash list

# Aplicar último stash
git stash pop

# Aplicar stash específico
git stash apply stash@{0}

# Eliminar stash
git stash drop stash@{0}
```

---

### Branches

```bash
# Crear branch
git checkout -b nueva-branch

# Cambiar de branch
git checkout main

# Eliminar branch local
git branch -d feature-branch
git branch -D feature-branch  # Forzar

# Eliminar branch remota
git push origin --delete feature-branch
```

---

### Sincronización

```bash
# Actualizar desde upstream
git fetch upstream
git merge upstream/main
# O en un solo comando
git pull upstream main

# Push a tu fork
git push origin main

# Push forzado (CUIDADO, solo en tu branch de feature)
git push origin feature-branch --force
```

---

## Troubleshooting

### "ModuleNotFoundError" al Importar

```bash
# Asegurarte de que las dependencias están instaladas
uv sync

# Verificar que estás en el virtual environment
which python
# Debería mostrar: /Users/.../aegra/.venv/bin/python

# Si no está activado:
source .venv/bin/activate
```

---

### "Connection refused" al Conectar a PostgreSQL

```bash
# Verificar que PostgreSQL está corriendo
docker ps

# Si no está, iniciarlo
docker compose up postgres -d

# Ver logs de PostgreSQL
docker logs aegra-postgres-1

# Verificar health
docker inspect aegra-postgres-1 | grep -A 5 Health
```

---

### "Alembic migration failed"

```bash
# Ver estado actual
python3 scripts/migrate.py current

# Ver historial
python3 scripts/migrate.py history

# Si la BD está en mal estado, reset (¡SOLO DESARROLLO!)
python3 scripts/migrate.py reset

# Reaplicar migraciones
python3 scripts/migrate.py upgrade
```

---

### "Import errors" después de Cambiar Dependencias

```bash
# Re-sincronizar
uv sync

# Si usas Docker, rebuild
docker compose build aegra --no-cache
docker compose up aegra
```

---

### Hot Reload no Funciona

```bash
# Asegurarte de que iniciaste con --reload
uv run uvicorn src.agent_server.main:app --reload

# Verificar que el archivo está en una carpeta monitoreada
# (src/, graphs/, auth.py, aegra.json tienen volume mounts)

# Si usas Docker, los volumes deben estar montados
# Ver docker-compose.yml líneas 34-40
```

---

### Tests Fallan con "Database already exists"

```bash
# Los tests pueden usar una base de datos separada
# Verificar variables de entorno en conftest.py

# O limpiar la base de datos de test
docker compose down -v  # Elimina volumes
docker compose up postgres -d
```

---

### Git Merge Conflicts

```bash
# Cuando hay conflictos después de rebase:

# 1. Ver qué archivos tienen conflictos
git status

# 2. Editar archivos, buscar:
<<<<<<< HEAD
tu código
=======
código de upstream
>>>>>>> upstream/main

# 3. Resolver manualmente, luego:
git add archivo_resuelto.py

# 4. Continuar rebase
git rebase --continue

# Si querés abortar:
git rebase --abort
```

---

### "Permission denied" en scripts/migrate.py

```bash
# Asegurarte de que tienes permisos de ejecución
chmod +x scripts/migrate.py

# O ejecutar con Python explícitamente
python3 scripts/migrate.py upgrade
```

---

## Recursos Adicionales

### Documentación del Proyecto

- **README.md** - Introducción y setup básico
- **CLAUDE.md** - Guía para Claude Code (instrucciones del proyecto)
- **docs/POSTGRES_INSPECTION.md** - Cómo inspeccionar checkpoints y store
- **docs/DEVELOPMENT_GUIDE.md** - Esta guía

### Documentación Externa

- **LangGraph**: https://langchain-ai.github.io/langgraph/
- **FastAPI**: https://fastapi.tiangolo.com/
- **SQLAlchemy**: https://docs.sqlalchemy.org/
- **Alembic**: https://alembic.sqlalchemy.org/
- **Agent Protocol**: https://agentprotocol.ai/

### Soporte

- **Issues**: https://github.com/ibbybuilds/aegra/issues
- **Discussions**: https://github.com/ibbybuilds/aegra/discussions
- **Discord/Slack**: (Si el proyecto tiene comunidad)

---

## Plantillas Útiles

### Plantilla de Issue

```markdown
## Descripción del Problema
[Descripción clara del bug o feature request]

## Pasos para Reproducir (si es bug)
1. Crear assistant con graph_id "example"
2. Crear thread
3. Hacer POST a /threads/{id}/runs
4. Error ocurre...

## Comportamiento Esperado
[Qué debería pasar]

## Comportamiento Actual
[Qué pasa actualmente]

## Entorno
- OS: macOS 14.5
- Python: 3.11.5
- Aegra version: main branch (commit abc123)
- LangGraph version: 0.2.0

## Logs/Screenshots
[Agregar logs o screenshots relevantes]

## Posible Solución (opcional)
[Si tenés idea de cómo arreglarlo]
```

---

### Plantilla de PR

```markdown
## Summary
[Breve descripción del cambio]

## Changes
- ✅ Change 1
- ✅ Change 2
- ✅ Change 3

## Test Plan
- [x] All existing tests pass
- [x] Added test for X
- [ ] Manual testing: [describe steps]

## Breaking Changes
[None / Describe breaking changes]

## Documentation
- [ ] Updated README.md
- [ ] Updated CLAUDE.md
- [ ] Added/updated docstrings
- [ ] Added example in docs/

## Related Issues
Closes #XX
Relates to #YY

## Screenshots (if applicable)
[Add screenshots for UI changes]

---

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>
```

---

## Contacto

Para preguntas sobre desarrollo:
1. Buscar en Issues existentes
2. Crear nuevo Issue con label "question"
3. Contactar a los maintainers en Discussions

---

**Última actualización:** 2025-11-05

**Maintainers:** Ver CONTRIBUTORS.md o GitHub contributors page
