"""RAG Tools - Tools for searching documentation using ChromaDB"""

import logging
import sys
from pathlib import Path
from typing import List, Dict, Any

# Add project root to path
# This allows the tool to work both from graph execution and standalone
project_root = Path(__file__).parent.parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from dotenv import load_dotenv
load_dotenv()

from ..core.rag_core import search_and_format

logger = logging.getLogger(__name__)


async def search_instructivo_general(
    query: str,
    k: int = 2,
) -> str:
    """Buscar en la documentación general (instructivos) usando búsqueda semántica
    con ChromaDB.

    Esta tool busca en todos los instructivos disponibles:
    - Perfil, datos personales y documentos
    - Operativo y propuesta al repartidor
    - Flujo de pagos y cobros

    REGLA IMPORTANTE: Usar esta tool UNA SOLA VEZ por query, luego sintetizar respuesta.
    No hacer búsquedas redundantes.

    Args:
        query: Consulta del usuario
        k: Número de resultados a retornar (default: 2)

    Returns:
        str: Resultados de la búsqueda en formato legible

    Example:
        >>> await search_instructivo_general("¿Cómo actualizo mi CBU?")
    """
    try:
        # Search in Instructivo_General database using ChromaDB
        results = search_and_format(query, "Instructivo_General", k=k)
        
        if not results or (len(results) == 1 and "error" in results[0].get("metadata", {})):
            return f"""
🔍 Búsqueda: "{query}"

❌ No se encontraron resultados relevantes en la documentación.

Sugerencias:
- Intenta reformular tu pregunta con términos más específicos
- Verifica que la documentación haya sido migrada correctamente
- Ejecuta el script de migración: uv run python3 scripts/migrate_instructivos_to_chromadb.py
"""

        # Format results for readability
        formatted_results = []
        for idx, result in enumerate(results, 1):
            content = result.get("content", "")
            metadata = result.get("metadata", {})
            source = result.get("source", "Desconocido")
            
            # Extract metadata
            h1 = metadata.get("Header 1", metadata.get("h1", ""))
            h2 = metadata.get("Header 2", metadata.get("h2", ""))
            h3 = metadata.get("Header 3", metadata.get("h3", ""))
            
            # Build result string
            result_str = f"""
📄 Resultado {idx}/{len(results)}: {source}
"""
            if h1:
                result_str += f"📑 H1: {h1}\n"
            if h2:
                result_str += f"📑 H2: {h2}\n"
            if h3:
                result_str += f"📑 H3: {h3}\n"
            
            result_str += f"""📝 Contenido relevante:
{content}
"""
            formatted_results.append(result_str)

        return f"""
🔍 Búsqueda: "{query}"
📊 Encontrados {len(results)} resultado(s) relevante(s):

{''.join(formatted_results)}

💡 Tip: Usa esta información para responder la consulta del usuario de manera precisa y completa.
"""

    except Exception as e:
        logger.error(f"Error searching instructivos: {e}", exc_info=True)
        return f"""
❌ Error al buscar en la documentación: {str(e)}

Por favor, intenta nuevamente o contacta al soporte técnico.
"""


# Legacy tools (kept for reference but not exposed)
# These were consolidated into search_instructivo_general

async def _search_instructivo_perfil(query: str, k: int = 5) -> str:
    """LEGACY: Búsqueda en instructivo de perfil/datos/documentos

    Ahora usar: search_instructivo_general()
    """
    return await search_instructivo_general(query, k)


async def _search_instructivo_operativo(query: str, k: int = 5) -> str:
    """LEGACY: Búsqueda en instructivo operativo y propuesta

    Ahora usar: search_instructivo_general()
    """
    return await search_instructivo_general(query, k)


async def _search_instructivo_pagos(query: str, k: int = 5) -> str:
    """LEGACY: Búsqueda en instructivo de flujo de pagos

    Ahora usar: search_instructivo_general()
    """
    return await search_instructivo_general(query, k)
