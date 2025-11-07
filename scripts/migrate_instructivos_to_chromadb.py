#!/usr/bin/env python3
"""Migrate instructivos to ChromaDB

This script:
1. Reads instructivo files from graphs/soporte_ods/instructivos/
2. Creates ChromaDB vector database with proper chunking
3. Uses MarkdownHeaderTextSplitter for hierarchical chunking

Usage:
    uv run python3 scripts/migrate_instructivos_to_chromadb.py
"""

import asyncio
import os
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Load environment variables from .env file
from dotenv import load_dotenv

load_dotenv()

from graphs.soporte_ods.core.rag_core import create_embeddings_from_markdown


def main():
    """Main migration function"""
    print("=" * 60)
    print("📚 Instructivos Migration to ChromaDB")
    print("=" * 60)

    # Get project root (parent of scripts directory)
    project_root = Path(__file__).parent.parent.resolve()
    
    # Load instructivos
    instructivos_dir = project_root / "graphs/soporte_ods/instructivos"
    
    if not instructivos_dir.exists():
        print(f"\n⚠️  Directory not found: {instructivos_dir}")
        print(f"   Creating directory...")
        instructivos_dir.mkdir(parents=True, exist_ok=True)
        print(f"   ℹ️  Please add instructivo files to: {instructivos_dir}")
        return

    # Read all .txt and .md files
    file_patterns = ["*.txt", "*.md"]
    files = []
    for pattern in file_patterns:
        files.extend(instructivos_dir.glob(pattern))

    if not files:
        print(f"\n⚠️  No instructivo files found in {instructivos_dir}")
        print(f"   Supported formats: .txt, .md")
        return

    print(f"\n📁 Found {len(files)} instructivo files")

    # Check for OpenAI API key
    if not os.getenv("OPENAI_API_KEY"):
        print("\n❌ OPENAI_API_KEY environment variable not set.")
        print("   Set it to generate embeddings.")
        return

    # Process each file
    for file_path in files:
        try:
            file_path = file_path.resolve()
            
            # Extract database name from filename
            # e.g., "4_Instructivo_General.md" -> "Instructivo_General"
            db_name = file_path.stem
            # Remove leading numbers and underscores if present
            if "_" in db_name:
                parts = db_name.split("_", 1)
                if parts[0].isdigit():
                    db_name = parts[1]
            
            print(f"\n📄 Processing: {file_path.name}")
            print(f"   Database name: {db_name}")
            
            # Create ChromaDB database from markdown file
            create_embeddings_from_markdown(str(file_path), db_name)
            
            print(f"   ✓ Created ChromaDB database: chroma_db_{db_name}")

        except Exception as e:
            print(f"   ✗ Error processing {file_path.name}: {e}")

    print("\n" + "=" * 60)
    print("✅ Migration complete!")
    print("=" * 60)
    print("\n💡 ChromaDB databases are stored in: RAG_resources/vector_databases/")


if __name__ == "__main__":
    main()

