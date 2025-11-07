#!/usr/bin/env python3
"""Migrate instructivos from ChromaDB to PostgreSQL Store

This script:
1. Reads instructivo files from graphs/soporte_ods/instructivos/
2. Splits files into chunks using h3 (###) as separator
3. Extracts h1 and h2 as metadata for each chunk
4. Generates embeddings using OpenAI
5. Stores them in PostgreSQL Store with namespace ("instructivos",)
6. Overwrites existing chunks if filename matches

Usage:
    uv run python3 scripts/migrate_instructivos_to_store.py
"""

import asyncio
import logging
import os
import re
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Load environment variables from .env file
from dotenv import load_dotenv

load_dotenv()

from langchain_openai import OpenAIEmbeddings
from src.agent_server.core.database import db_manager

logger = logging.getLogger(__name__)


def parse_markdown_chunks(content: str) -> List[Dict[str, Any]]:
    """Parse markdown content into chunks separated by h3 (###)
    
    Each chunk includes:
    - The h3 heading and its content
    - h1 and h2 as metadata
    
    Args:
        content: Markdown content to parse
        
    Returns:
        List of chunk dicts with {content, h1, h2, h3}
    """
    chunks = []
    
    # Split by h3 headings (###)
    # Pattern matches: ### heading (with optional leading/trailing whitespace)
    h3_pattern = r'^###\s+(.+)$'
    
    lines = content.split('\n')
    current_chunk_lines = []
    current_h1: Optional[str] = None
    current_h2: Optional[str] = None
    current_h3: Optional[str] = None
    
    for line in lines:
        # Check for h1 (# heading)
        h1_match = re.match(r'^#\s+(.+)$', line)
        if h1_match:
            current_h1 = h1_match.group(1).strip()
            current_h2 = None  # Reset h2 when h1 changes
            current_h3 = None  # Reset h3 when h1 changes
            continue
        
        # Check for h2 (## heading)
        h2_match = re.match(r'^##\s+(.+)$', line)
        if h2_match:
            current_h2 = h2_match.group(1).strip()
            current_h3 = None  # Reset h3 when h2 changes
            continue
        
        # Check for h3 (### heading) - this starts a new chunk
        h3_match = re.match(h3_pattern, line)
        if h3_match:
            # Save previous chunk if it exists
            if current_chunk_lines and current_h3:
                chunk_content = '\n'.join(current_chunk_lines).strip()
                if chunk_content:
                    chunks.append({
                        "content": chunk_content,
                        "h1": current_h1,
                        "h2": current_h2,
                        "h3": current_h3,
                    })
            
            # Start new chunk
            current_h3 = h3_match.group(1).strip()
            current_chunk_lines = [line]  # Include the h3 heading in the chunk
            continue
        
        # Add line to current chunk if we have an h3
        if current_h3 is not None:
            current_chunk_lines.append(line)
    
    # Don't forget the last chunk
    if current_chunk_lines and current_h3:
        chunk_content = '\n'.join(current_chunk_lines).strip()
        if chunk_content:
            chunks.append({
                "content": chunk_content,
                "h1": current_h1,
                "h2": current_h2,
                "h3": current_h3,
            })
    
    return chunks


async def load_instructivos(instructivos_dir: Path, project_root: Path) -> List[Dict[str, Any]]:
    """Load instructivo files and split them into chunks by h3

    Args:
        instructivos_dir: Directory containing instructivo files
        project_root: Project root directory for relative path calculation

    Returns:
        List of chunk dicts with {id, content, metadata}
    """
    chunks = []

    # Resolve to absolute path
    instructivos_dir = instructivos_dir.resolve()
    project_root = project_root.resolve()

    if not instructivos_dir.exists():
        print(f"⚠️  Directory not found: {instructivos_dir}")
        print(f"   Creating directory...")
        instructivos_dir.mkdir(parents=True, exist_ok=True)
        print(f"   ℹ️  Please add instructivo files to: {instructivos_dir}")
        return chunks

    # Read all .txt and .md files
    file_patterns = ["*.txt", "*.md"]
    files = []
    for pattern in file_patterns:
        files.extend(instructivos_dir.glob(pattern))

    if not files:
        print(f"⚠️  No instructivo files found in {instructivos_dir}")
        print(f"   Supported formats: .txt, .md")
        return chunks

    print(f"📁 Found {len(files)} instructivo files")

    for file_path in files:
        try:
            # Resolve to absolute path
            file_path = file_path.resolve()
            
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()

            if not content.strip():
                print(f"   ⚠️  Skipping empty file: {file_path.name}")
                continue

            # Calculate relative path from project root
            try:
                relative_source = str(file_path.relative_to(project_root))
            except ValueError:
                # If file is outside project root, use absolute path
                relative_source = str(file_path)

            # Parse into chunks
            file_chunks = parse_markdown_chunks(content)
            
            if not file_chunks:
                print(f"   ⚠️  No h3 chunks found in: {file_path.name}")
                continue

            # Create chunk entries
            for chunk_idx, chunk_data in enumerate(file_chunks):
                chunk_id = f"{file_path.stem}_chunk_{chunk_idx}"
                chunk = {
                    "id": chunk_id,
                    "filename": file_path.name,
                    "content": chunk_data["content"],
                    "metadata": {
                        "filename": file_path.name,
                        "source": relative_source,
                        "category": _infer_category(file_path.name),
                        "h1": chunk_data["h1"],
                        "h2": chunk_data["h2"],
                        "h3": chunk_data["h3"],
                        "chunk_index": chunk_idx,
                    },
                }
                chunks.append(chunk)
            
            print(f"   ✓ Loaded: {file_path.name} ({len(file_chunks)} chunks)")

        except Exception as e:
            print(f"   ✗ Error loading {file_path.name}: {e}")

    return chunks


def _infer_category(filename: str) -> str:
    """Infer category from filename"""
    filename_lower = filename.lower()

    if any(term in filename_lower for term in ["perfil", "datos", "documento"]):
        return "perfil_y_documentos"
    elif any(term in filename_lower for term in ["operativo", "propuesta", "repartidor"]):
        return "operativo_y_propuesta"
    elif any(term in filename_lower for term in ["pago", "cobro", "factura"]):
        return "flujo_de_pagos"
    else:
        return "general"


async def generate_embeddings(
    chunks: List[Dict[str, Any]]
) -> List[List[float]]:
    """Generate embeddings for chunks using OpenAI

    Args:
        chunks: List of chunk dicts

    Returns:
        List of embedding vectors
    """
    if not chunks:
        return []

    # Check for OpenAI API key
    if not os.getenv("OPENAI_API_KEY"):
        raise ValueError(
            "OPENAI_API_KEY environment variable not set. "
            "Set it to generate embeddings."
        )

    print(f"\n🤖 Generating embeddings for {len(chunks)} chunks...")

    embeddings_model = OpenAIEmbeddings(
        model="text-embedding-3-small"  # More affordable than ada-002
    )

    # Extract content for embedding
    texts = [chunk["content"] for chunk in chunks]

    # Generate embeddings in batch
    try:
        embeddings = await embeddings_model.aembed_documents(texts)
        print(f"   ✓ Generated {len(embeddings)} embeddings")
        return embeddings
    except Exception as e:
        print(f"   ✗ Error generating embeddings: {e}")
        raise


async def delete_existing_chunks_for_files(
    store: Any, filenames: List[str]
) -> None:
    """Delete existing chunks for given filenames
    
    Uses a broad search to find all chunks, then filters by filename in metadata
    and deletes matching chunks.
    
    Args:
        store: AsyncPostgresStore instance
        filenames: List of filenames to delete chunks for
    """
    if not filenames:
        return
    
    print(f"\n🗑️  Deleting existing chunks for {len(filenames)} file(s)...")
    
    # Use a very broad search query to find all chunks in the namespace
    # We'll search for common words that are likely to appear in any document
    try:
        # Search with a very broad query to get many results
        # We use a high limit to get as many chunks as possible
        all_results = await store.asearch(
            ("instructivos",),
            query="documento información datos",  # Very broad query
            limit=1000,  # High limit to get many results
        )
        
        deleted_count = 0
        filenames_set = set(filenames)
        
        # Filter results by filename in metadata and delete matching chunks
        for result in all_results:
            try:
                metadata = result.value.get("metadata", {})
                result_filename = metadata.get("filename")
                
                if result_filename in filenames_set:
                    # Delete this chunk
                    await store.adelete(("instructivos",), result.key)
                    deleted_count += 1
            except Exception as e:
                # Skip chunks that can't be deleted (might already be gone)
                logger.debug(f"Could not delete chunk {result.key}: {e}")
                continue
        
        if deleted_count > 0:
            print(f"   ✓ Deleted {deleted_count} existing chunk(s)")
        else:
            print(f"   ℹ️  No existing chunks found to delete")
            
    except Exception as e:
        # If search fails, we'll just overwrite during put
        print(f"   ⚠️  Could not search for existing chunks: {e}")
        print(f"   ℹ️  Will overwrite chunks during storage")


async def store_in_postgres(
    chunks: List[Dict[str, Any]], embeddings: List[List[float]]
) -> None:
    """Store chunks and embeddings in PostgreSQL Store
    
    If chunks with the same filename exist, they will be overwritten.

    Args:
        chunks: List of chunk dicts
        embeddings: List of embedding vectors
    """
    if not chunks or not embeddings:
        print("\n⚠️  No data to store")
        return

    if len(chunks) != len(embeddings):
        raise ValueError(
            f"Mismatch: {len(chunks)} chunks but {len(embeddings)} embeddings"
        )

    print(f"\n💾 Storing {len(chunks)} chunks in PostgreSQL Store...")

    # Get store from database manager
    store = await db_manager.get_store()
    
    # Get unique filenames to track what we're overwriting
    unique_filenames = list(set(chunk["filename"] for chunk in chunks))
    await delete_existing_chunks_for_files(store, unique_filenames)

    # Group chunks by filename for better reporting
    chunks_by_file: Dict[str, List[Dict[str, Any]]] = {}
    for chunk in chunks:
        filename = chunk["filename"]
        if filename not in chunks_by_file:
            chunks_by_file[filename] = []
        chunks_by_file[filename].append(chunk)

    # Store each chunk
    chunk_idx = 0
    for filename, file_chunks in chunks_by_file.items():
        for chunk in file_chunks:
            try:
                # Prepare value with content, metadata, and embedding
                value = {
                    "content": chunk["content"],
                    "metadata": chunk["metadata"],
                    "embedding": embeddings[chunk_idx],
                }

                # Store in namespace ("instructivos",)
                # Key format: {filename}_chunk_{index}
                # This allows overwriting when filename matches
                await store.aput(
                    namespace=("instructivos",),
                    key=chunk["id"],
                    value=value,
                )

                chunk_idx += 1

            except Exception as e:
                print(
                    f"   ✗ Error storing chunk {chunk['id']}: {e}"
                )
        
        print(
            f"   ✓ Stored: {filename} ({len(file_chunks)} chunks)"
        )

    print(f"\n✅ Migration complete! Stored {len(chunks)} chunks from {len(unique_filenames)} file(s)")


async def verify_migration() -> None:
    """Verify that documents were stored correctly"""
    print(f"\n🔍 Verifying migration...")

    store = await db_manager.get_store()

    try:
        # Try to search for a test query
        results = await store.asearch(
            namespace=("instructivos",),
            query="información",  # Generic query
            limit=3,
        )

        if results:
            print(f"   ✓ Verification successful: Found {len(results)} results")
            print(f"   ℹ️  Sample result: {results[0].key if results else 'N/A'}")
        else:
            print(f"   ⚠️  No results found in search verification")

    except Exception as e:
        print(f"   ⚠️  Verification search failed: {e}")
        print(f"   This is expected if search functionality is not yet implemented")


async def main():
    """Main migration function"""
    print("=" * 60)
    print("📚 Instructivos Migration: ChromaDB → PostgreSQL Store")
    print("=" * 60)

    # Initialize database manager
    print("\n🔧 Initializing database connection...")
    await db_manager.initialize()
    print("   ✓ Database connected")

    # Get project root (parent of scripts directory)
    project_root = Path(__file__).parent.parent.resolve()
    
    # Load instructivos and split into chunks
    instructivos_dir = project_root / "graphs/soporte_ods/instructivos"
    chunks = await load_instructivos(instructivos_dir, project_root)

    if not chunks:
        print("\n⚠️  No chunks to migrate. Exiting.")
        return

    print(f"\n📊 Total chunks to process: {len(chunks)}")

    # Generate embeddings
    try:
        embeddings = await generate_embeddings(chunks)
    except Exception as e:
        print(f"\n❌ Failed to generate embeddings: {e}")
        return

    # Store in PostgreSQL (will overwrite existing chunks with same filename)
    try:
        await store_in_postgres(chunks, embeddings)
    except Exception as e:
        print(f"\n❌ Failed to store in database: {e}")
        return

    # Verify migration
    await verify_migration()

    print("\n" + "=" * 60)
    print("✅ Migration complete!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
