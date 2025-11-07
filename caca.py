#!/usr/bin/env python3
"""Test script for RAG search functionality"""

import asyncio
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

from src.agent_server.core.database import db_manager
from graphs.soporte_ods.tools.rag_tools import search_instructivo_general


async def main():
    """Test the RAG search functionality"""
    print("🔧 Initializing database...")
    await db_manager.initialize()
    
    print("\n🔍 Testing search_instructivo_general...")
    result = await search_instructivo_general(
        query="¿Cómo actualizo mi CBU? quiero cobrar en la cuenta de mi novia en vez de la mia",
        k=2
    )
    print("\n" + "="*60)
    print(result)
    print("="*60)
    
    print("\n✅ Test completed!")


if __name__ == "__main__":
    asyncio.run(main())