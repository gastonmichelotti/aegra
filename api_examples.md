# API Examples - Soporte ODS Agent

Ejemplos de requests para crear assistant, thread y run en la API de Aegra.

## Base URL
```
http://localhost:8000
```

## 1. Crear Assistant (Soporte ODS)

**POST** `/assistants`

```json
{
  "graph_id": "soporte_ods",
  "name": "Agente Soporte ODS",
  "description": "Agente de soporte para repartidores ODS con acceso a documentación y servicios",
  "config": {},
  "context": {},
  "metadata": {
    "version": "1.0",
    "type": "support_agent"
  },
  "if_exists": "do_nothing"
}
```

**Respuesta:**
```json
{
  "assistant_id": "uuid-del-assistant",
  "name": "Agente Soporte ODS",
  "description": "Agente de soporte para repartidores ODS con acceso a documentación y servicios",
  "graph_id": "soporte_ods",
  "config": {},
  "context": {},
  "metadata": {
    "version": "1.0",
    "type": "support_agent"
  },
  "user_id": "user-identity",
  "version": 1,
  "created_at": "2025-11-07T18:00:00Z",
  "updated_at": "2025-11-07T18:00:00Z"
}
```

## 2. Crear Thread con ID de Motoboy

**POST** `/threads`

```json
{
  "metadata": {
    "motoboy_id": "12345",
    "thread_name": "Conversación con Motoboy 12345"
  }
}
```

**Respuesta:**
```json
{
  "thread_id": "uuid-del-thread",
  "status": "idle",
  "metadata": {
    "motoboy_id": "12345",
    "thread_name": "Conversación con Motoboy 12345",
    "owner": "user-identity",
    "assistant_id": null,
    "graph_id": null
  },
  "user_id": "user-identity",
  "created_at": "2025-11-07T18:00:00Z"
}
```

## 3. Crear Run

**POST** `/threads/{thread_id}/runs`

Reemplaza `{thread_id}` con el ID del thread creado anteriormente.

```json
{
  "assistant_id": "uuid-del-assistant",
  "input": {
    "messages": [
      {
        "type": "human",
        "content": [
          {
            "type": "text",
            "text": "¿Cómo actualizo mi CBU en la app?"
          }
        ]
      }
    ]
  },
  "config": {},
  "context": {}
}
```

**Respuesta:**
```json
{
  "run_id": "uuid-del-run",
  "thread_id": "uuid-del-thread",
  "assistant_id": "uuid-del-assistant",
  "status": "pending",
  "input": {
    "messages": [
      {
        "type": "human",
        "content": [
          {
            "type": "text",
            "text": "¿Cómo actualizo mi CBU en la app?"
          }
        ]
      }
    ]
  },
  "output": null,
  "error_message": null,
  "config": {},
  "context": {},
  "user_id": "user-identity",
  "created_at": "2025-11-07T18:00:00Z",
  "updated_at": "2025-11-07T18:00:00Z"
}
```

## Ejemplo Completo con cURL

```bash
# 1. Crear Assistant
ASSISTANT_RESPONSE=$(curl -X POST http://localhost:8000/assistants \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "graph_id": "soporte_ods",
    "name": "Agente Soporte ODS",
    "description": "Agente de soporte para repartidores ODS",
    "if_exists": "do_nothing"
  }')

ASSISTANT_ID=$(echo $ASSISTANT_RESPONSE | jq -r '.assistant_id')
echo "Assistant ID: $ASSISTANT_ID"

# 2. Crear Thread con motoboy_id
THREAD_RESPONSE=$(curl -X POST http://localhost:8000/threads \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "metadata": {
      "motoboy_id": "12345",
      "thread_name": "Conversación con Motoboy 12345"
    }
  }')

THREAD_ID=$(echo $THREAD_RESPONSE | jq -r '.thread_id')
echo "Thread ID: $THREAD_ID"

# 3. Crear Run
curl -X POST http://localhost:8000/threads/$THREAD_ID/runs \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d "{
    \"assistant_id\": \"$ASSISTANT_ID\",
    \"input\": {
      \"messages\": [
        {
          \"type\": \"human\",
          \"content\": [
            {
              \"type\": \"text\",
              \"text\": \"¿Cómo actualizo mi CBU en la app?\"
            }
          ]
        }
      ]
    }
  }"
```

## Ejemplo con Python

```python
import requests
import json

BASE_URL = "http://localhost:8000"
HEADERS = {
    "Content-Type": "application/json",
    "Authorization": "Bearer YOUR_TOKEN"  # Omitir si AUTH_TYPE=noop
}

# 1. Crear Assistant
assistant_data = {
    "graph_id": "soporte_ods",
    "name": "Agente Soporte ODS",
    "description": "Agente de soporte para repartidores ODS",
    "if_exists": "do_nothing"
}

response = requests.post(
    f"{BASE_URL}/assistants",
    headers=HEADERS,
    json=assistant_data
)
assistant = response.json()
assistant_id = assistant["assistant_id"]
print(f"✅ Assistant creado: {assistant_id}")

# 2. Crear Thread con motoboy_id
thread_data = {
    "metadata": {
        "motoboy_id": "12345",
        "thread_name": "Conversación con Motoboy 12345"
    }
}

response = requests.post(
    f"{BASE_URL}/threads",
    headers=HEADERS,
    json=thread_data
)
thread = response.json()
thread_id = thread["thread_id"]
print(f"✅ Thread creado: {thread_id}")

# 3. Crear Run
run_data = {
    "assistant_id": assistant_id,
    "input": {
        "messages": [
            {
                "type": "human",
                "content": [
                    {
                        "type": "text",
                        "text": "¿Cómo actualizo mi CBU en la app?"
                    }
                ]
            }
        ]
    }
}

response = requests.post(
    f"{BASE_URL}/threads/{thread_id}/runs",
    headers=HEADERS,
    json=run_data
)
run = response.json()
run_id = run["run_id"]
print(f"✅ Run creado: {run_id}")
print(f"   Status: {run['status']}")

# 4. (Opcional) Esperar resultado
response = requests.post(
    f"{BASE_URL}/threads/{thread_id}/runs/wait",
    headers=HEADERS,
    json=run_data
)
result = response.json()
print(f"✅ Resultado: {json.dumps(result, indent=2)}")
```

## Notas Importantes

1. **Autenticación**: Si `AUTH_TYPE=noop`, no necesitas el header `Authorization`. Si usas autenticación custom, incluye el token.

2. **graph_id**: Debe coincidir con una entrada en `aegra.json`. Para soporte_ods, usa `"soporte_ods"`.

3. **motoboy_id**: Se guarda en `metadata` del thread y puede ser usado por el agente para cargar contexto del motoboy.

4. **Input format**: El input debe seguir el formato de mensajes de LangGraph con `type: "human"` y `content` como array.

5. **Streaming**: Para respuestas en tiempo real, usa `/threads/{thread_id}/runs/stream` en lugar de `/runs`.

