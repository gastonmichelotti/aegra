"""
Módulo consolidado para funcionalidad RAG (Retrieval-Augmented Generation) usando ChromaDB
Optimizado con cache LRU para reducir consumo de RAM.
"""
import os
from typing import List, Dict, Any, Optional
from pathlib import Path
from functools import lru_cache

from dotenv import load_dotenv

# Load environment variables
load_dotenv()

from langchain_chroma import Chroma
from langchain_openai.embeddings import OpenAIEmbeddings
from langchain_text_splitters import MarkdownHeaderTextSplitter
from langchain_core.documents import Document
from langchain_core.retrievers import BaseRetriever
import chromadb


# Instancia única de embeddings para evitar duplicación
_embeddings_instance = None

def get_embeddings() -> OpenAIEmbeddings:
    """
    Obtiene instancia única de OpenAI embeddings con lazy loading.
    Evita crear múltiples instancias innecesarias.
    Optimizado: Solo se carga cuando se necesita por primera vez.
    """
    global _embeddings_instance
    if _embeddings_instance is None:
        _embeddings_instance = OpenAIEmbeddings(model="text-embedding-3-small")
    return _embeddings_instance


# Cache LRU para retrievers (Optimización de RAM)
# Mantiene hasta 3 retrievers en memoria, limpiando automáticamente los menos usados
@lru_cache(maxsize=3)
def _get_cached_chroma_db(db_name: str, k: int) -> Chroma:
    """
    Cache LRU para instancias de ChromaDB.
    Reduce consumo de RAM al reutilizar retrievers.

    Args:
        db_name: Nombre de la base de datos
        k: Número de documentos a recuperar

    Returns:
        Chroma: Instancia en caché de ChromaDB
    """
    database_path = _get_database_path(db_name)

    if not os.path.exists(database_path):
        raise ValueError(f"Base de datos '{db_name}' no encontrada en {database_path}")

    # ChromaDB: Crear cliente persistente con telemetría deshabilitada
    client_settings = chromadb.Settings(
        anonymized_telemetry=False,
        is_persistent=True
    )
    client = chromadb.PersistentClient(
        path=database_path,
        settings=client_settings
    )

    db = Chroma(
        persist_directory=database_path,
        embedding_function=get_embeddings(),
        client=client
    )

    return db


def create_embeddings_from_markdown(markdown_file: str, db_name: str) -> None:
    """
    Crea base de datos vectorial desde archivo Markdown usando chunking por jerarquía.
    
    Args:
        markdown_file (str): Ruta al archivo Markdown
        db_name (str): Nombre de la base de datos
    """
    with open(markdown_file, 'r', encoding='utf-8') as f:
        markdown_text = f.read()

    headers_to_split_on = [
        ("#", "Header 1"),
        ("##", "Header 2"), 
        ("###", "Header 3"),
    ]

    markdown_splitter = MarkdownHeaderTextSplitter(headers_to_split_on=headers_to_split_on)
    documents = markdown_splitter.split_text(markdown_text)

    persist_directory = _get_database_path(db_name)
    
    # Ensure directory exists
    Path(persist_directory).mkdir(parents=True, exist_ok=True)

    # Crear cliente con telemetría deshabilitada
    client_settings = chromadb.Settings(
        anonymized_telemetry=False,
        is_persistent=True
    )
    client = chromadb.PersistentClient(
        path=persist_directory,
        settings=client_settings
    )

    db = Chroma.from_documents(
        documents,
        get_embeddings(),
        persist_directory=persist_directory,
        client=client
    )
    # Note: In ChromaDB, persistence happens automatically


def create_retriever(db_name: str, k: int = 2) -> BaseRetriever:
    """
    Crea retriever usando ChromaDB con cache LRU (optimizado).
    Reutiliza instancias en caché para reducir consumo de RAM.

    Args:
        db_name (str): Nombre de la base de datos
        k (int): Número de documentos a recuperar

    Returns:
        BaseRetriever: Retriever configurado (puede ser de caché)
    """
    # Usar cache LRU para reutilizar instancias de ChromaDB
    db = _get_cached_chroma_db(db_name, k)
    return db.as_retriever(search_kwargs={"k": k})


def search_documents(query: str, db_name: str, k: int = 2) -> List[Document]:
    """
    Busca documentos relevantes en una base de datos vectorial.
    
    Args:
        query (str): Consulta de búsqueda
        db_name (str): Nombre de la base de datos
        k (int): Número de documentos a retornar
        
    Returns:
        List[Document]: Documentos relevantes
    """
    retriever = create_retriever(db_name, k)
    return retriever.invoke(query)


def format_search_results(documents: List[Document]) -> List[Dict[str, Any]]:
    """
    Formatea resultados de búsqueda RAG en formato estándar.
    
    Args:
        documents (List[Document]): Documentos de resultado
        
    Returns:
        List[Dict[str, Any]]: Resultados formateados
    """
    if not documents:
        return [{
            "content": "No se encontraron documentos relevantes para la consulta.",
            "metadata": {},
            "source": "Sistema"
        }]
    
    formatted_results = []
    for doc in documents:
        formatted_results.append({
            "content": doc.page_content,
            "metadata": doc.metadata,
            "source": doc.metadata.get("source", "Unknown")
        })
    
    return formatted_results


def search_and_format(query: str, db_name: str, k: int = 2) -> List[Dict[str, Any]]:
    """
    Función de conveniencia que combina búsqueda y formateo.
    
    Args:
        query (str): Consulta de búsqueda
        db_name (str): Nombre de la base de datos
        k (int): Número de documentos a retornar
        
    Returns:
        List[Dict[str, Any]]: Resultados formateados
    """
    try:
        documents = search_documents(query, db_name, k)
        return format_search_results(documents)
    except Exception as e:
        return [{
            "content": f"Error al buscar en la base de datos: {str(e)}",
            "metadata": {"error": str(e)},
            "source": "Sistema"
        }]


# Funciones de gestión de caché
def get_cache_info() -> Dict[str, Any]:
    """
    Obtiene información sobre el estado del caché LRU de retrievers.

    Returns:
        Dict con estadísticas del caché (hits, misses, size, maxsize)
    """
    cache_info = _get_cached_chroma_db.cache_info()
    return {
        "hits": cache_info.hits,
        "misses": cache_info.misses,
        "current_size": cache_info.currsize,
        "max_size": cache_info.maxsize,
        "hit_rate": cache_info.hits / (cache_info.hits + cache_info.misses) if (cache_info.hits + cache_info.misses) > 0 else 0
    }


def clear_retriever_cache() -> None:
    """
    Limpia el caché de retrievers.
    Útil para liberar RAM o forzar recarga de bases de datos.
    """
    _get_cached_chroma_db.cache_clear()


# Funciones privadas de utilidad
def _get_database_path(db_name: str) -> str:
    """Obtiene ruta estandarizada para base de datos."""
    # Usar ruta relativa desde la raíz del proyecto
    project_root = Path(__file__).parent.parent.parent.parent
    
    # Crear estructura RAG_resources/vector_databases si no existe
    base_dir = project_root / "RAG_resources" / "vector_databases"
    base_dir.mkdir(parents=True, exist_ok=True)

    return str(base_dir / f"chroma_db_{db_name}")

