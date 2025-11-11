# Soporte ODS - Agent de Soporte para Repartidores

Agent de soporte AI para repartidores de Pedidos Ya, migrado a la arquitectura Aegra desde AgenteSoporteODS.

## Arquitectura

### ReactAgent Centralizado

El agent utiliza un patrón **ReactAgent** simple en lugar del sistema multiagente anterior:

- **Single LLM** con todas las tools disponibles
- **Prompt engineering** para especialización de dominio
- **Context pre-computation** para optimización de performance
- **PostgreSQL checkpointing** para state persistence
- **PostgreSQL Store** para long-term memory

### Flow del Graph

```
START → load_context → agent → [tools / observer / END]
                         ↑        ↓
                         └────────┘
```

**Nodos**:
1. `load_context`: Pre-computa contexto (motoboy, viaje, reserva, location)
2. `agent`: LLM principal con todas las tools
3. `tools`: Ejecuta tool calls
4. `observer`: Extrae insights para memoria de largo plazo

## State Schema

El state incluye **clases de dominio** (Pydantic models), no dicts:

```python
@dataclass
class SoporteState:
    messages: Annotated[Sequence[AnyMessage], add_messages]

    # Domain models
    motoboy: Optional[MotoboyModel]
    viaje: Optional[ViajeModel | List[ViajeModel]]
    reserva: Optional[ReservaModel]
    location_info: Optional[dict]
    last_context_refresh: Optional[datetime]

    # Confirmation flow
    pending_confirmation: Optional[dict]

    # Observer flag
    should_observe: bool
    is_last_step: IsLastStep
```

## Configuration (MODE)

El graph soporta 3 modos de ejecución:

- **MODE 1**: Production (datos reales, APIs de producción)
- **MODE 2**: Staging (datos de staging, APIs de staging)
- **MODE 3**: Evaluation (datos mock para testing)

El MODE se define al crear el assistant:

```bash
POST /assistants
{
    "graph_id": "soporte_ods",
    "metadata": {
        "mode": 2  # Staging
    }
}
```

## Tools Disponibles

1. **gestionar_estado_viaje** - Gestión de estado de viajes (liberar, cancelar, no entregado)
2. **obtener_desafios** - Consultar desafíos/bonos activos
3. **search_instructivo_general** - Búsqueda semántica en documentación
4. **get_motoboy_location** - Ubicación en tiempo real desde Firebase
5. **derive_to_human** - Escalación a soporte humano

## Usage

### 1. Crear Assistant

```bash
POST /assistants
{
    "graph_id": "soporte_ods",
    "name": "Soporte Motoboy Staging",
    "metadata": {
        "mode": 2
    }
}
```

### 2. Crear Thread (opcional)

```bash
POST /threads
{
    "thread_id": "motoboy_12345_session_1699999999"
}
```

### 3. Crear Run con Motoboy ID en Input

```bash
POST /threads/{thread_id}/runs
{
    "assistant_id": "asst_xxx",
    "input": {
        "motoboy_id": 12345,  # ← Pass ONCE at initialization
        "messages": [
            {"role": "user", "content": "¿Cuál es mi viaje actual?"}
        ]
    },
    "context": {
        "mode": 2,  # Optional: defaults to 1 (production)
        "model": "openai/gpt-4-turbo",
        "temperature": 0.3
    },
    "multitask_strategy": "interrupt"
}
```

**Notas importantes**:
- El `motoboy_id` se pasa **UNA SOLA VEZ** en el `input` del primer run
- Se persiste automáticamente en el state (PostgreSQL checkpoints)
- No es necesario pasarlo en mensajes subsecuentes de la conversación
- El `context` solo contiene configuración que puede variar (mode, model, etc.)

## Context Refresh

El contexto (motoboy, viaje, reserva, location) se:
- Carga al inicio de la conversación
- Se cachea en PostgreSQL checkpoints
- Se refresca automáticamente cada 5 minutos (configurable)

## Long-Term Memory

El observer node extrae insights de las conversaciones y los guarda en PostgreSQL Store:

- **Namespace**: `("motoboy", "{motoboy_id}", "preferences")`
- **Namespace**: `("motoboy", "{motoboy_id}", "recurring_issues")`

## Pending Implementations

### Alta Prioridad
- [ ] Implementar `gestionar_estado_viaje` - Llamada a API real
- [ ] Implementar `search_instructivo_general` - Vector search con Store
- [ ] Migrar instructivos de ChromaDB a PostgreSQL Store
- [ ] Implementar agent_node - LLM call real con tools
- [ ] Implementar observer_node - Insight extraction con structured output

### Media Prioridad
- [ ] Database connections para services (reemplazar mock data en MODE 1 y 2)
- [ ] Firebase integration para `get_motoboy_location`
- [ ] Confirmation flow logic en `gestionar_estado_viaje`
- [ ] Escalation logic en `derive_to_human`

### Baja Prioridad
- [ ] API call metadata logging
- [ ] Performance monitoring
- [ ] Error recovery strategies

## Environment Variables

```bash
# Database URLs
PROD_DB_URL=postgresql://...
STAGING_DB_URL=postgresql://...

# API URLs
PROD_API_BASE_URL=https://api.pedidosya.com
STAGING_API_BASE_URL=https://staging-api.pedidosya.com

# Firebase (TODO: Add paths to config files)
```

## Development

```bash
# Install dependencies
uv install

# Start database
docker compose up postgres -d

# Run migrations (activate venv first)
source .venv/bin/activate
python3 scripts/migrate.py upgrade

# Start server
uv run uvicorn src.agent_server.main:app --reload

# Test health
curl http://localhost:8000/health
```

## Testing

```bash
# Run all tests
uv run pytest

# Run soporte_ods specific tests
uv run pytest tests/test_soporte_ods_graph.py -v

# Test graph compilation
uv run python3 -c "from graphs.soporte_ods.graph import graph; print(f'✓ Graph: {graph.name}')"
```

## Important Notes

⚠️ **Always use `uv run`** when executing Python commands that import the graph. This ensures the correct LangGraph dependencies are available.

✅ **Graph compilation verified**: The graph compiles successfully and all nodes are connected properly.
