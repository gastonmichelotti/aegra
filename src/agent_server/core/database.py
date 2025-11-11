"""Database manager with LangGraph integration"""

import os
from typing import Any, Dict, List, Optional

import structlog
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from langgraph.store.postgres.aio import AsyncPostgresStore
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine

logger = structlog.get_logger(__name__)


class DatabaseManager:
    """Manages database connections and LangGraph persistence components"""

    def __init__(self) -> None:
        self.engine: AsyncEngine | None = None
        self._checkpointer: AsyncPostgresSaver | None = None
        self._checkpointer_cm: Any = None  # holds the contextmanager so we can close it
        self._store: AsyncPostgresStore | None = None
        self._store_cm: Any = None
        self._database_url = os.getenv(
            "DATABASE_URL", "postgresql+asyncpg://user:password@localhost:5432/aegra"
        )

    async def initialize(self) -> None:
        """Initialize database connections and LangGraph components"""
        # SQLAlchemy for our minimal Agent Protocol metadata tables
        self.engine = create_async_engine(
            self._database_url,
            echo=os.getenv("DATABASE_ECHO", "false").lower() == "true",
        )

        # Convert asyncpg URL to psycopg format for LangGraph
        # LangGraph packages require psycopg format, not asyncpg
        dsn = self._database_url.replace("postgresql+asyncpg://", "postgresql://")

        # Store connection string for creating LangGraph components on demand
        self._langgraph_dsn = dsn
        self.checkpointer = None
        self.store = None
        # Note: LangGraph components will be created as context managers when needed

        # Note: Database schema is now managed by Alembic migrations
        # Run 'alembic upgrade head' to apply migrations

        logger.info("✅ Database and LangGraph components initialized")

    async def close(self) -> None:
        """Close database connections"""
        if self.engine:
            await self.engine.dispose()

        # Close the cached checkpointer if we opened one
        if self._checkpointer_cm is not None:
            await self._checkpointer_cm.__aexit__(None, None, None)
            self._checkpointer_cm = None
            self._checkpointer = None

        if self._store_cm is not None:
            await self._store_cm.__aexit__(None, None, None)
            self._store_cm = None
            self._store = None

        logger.info("✅ Database connections closed")

    async def get_checkpointer(self) -> AsyncPostgresSaver:
        """Return a live AsyncPostgresSaver.

        We enter the async context manager once and cache the saver so that
        subsequent calls reuse the same database connection pool.  LangGraph
        expects the *real* saver object (it calls methods like
        ``get_next_version``), so returning the context manager wrapper would
        fail.
        """
        if not hasattr(self, "_langgraph_dsn"):
            raise RuntimeError("Database not initialized")
        if self._checkpointer is None:
            self._checkpointer_cm = AsyncPostgresSaver.from_conn_string(
                self._langgraph_dsn
            )
            self._checkpointer = await self._checkpointer_cm.__aenter__()
            # Ensure required tables exist (idempotent)
            await self._checkpointer.setup()
        return self._checkpointer

    async def get_store(self) -> AsyncPostgresStore:
        """Return a live AsyncPostgresStore instance (vector + KV)."""
        if not hasattr(self, "_langgraph_dsn"):
            raise RuntimeError("Database not initialized")
        if self._store is None:
            self._store_cm = AsyncPostgresStore.from_conn_string(self._langgraph_dsn)
            self._store = await self._store_cm.__aenter__()
            # ensure schema
            await self._store.setup()
        return self._store

    def get_engine(self) -> AsyncEngine:
        """Get the SQLAlchemy engine for metadata tables"""
        if not self.engine:
            raise RuntimeError("Database not initialized")
        return self.engine

    def create_external_engine(self, db_url: str, **kwargs) -> AsyncEngine:
        """
        Create an independent async engine for external database connections.

        This is useful for connecting to external databases (e.g., SQL Server, MySQL)
        that are separate from the main Aegra database.

        Args:
            db_url: Database connection URL (supports various formats)
            **kwargs: Additional engine configuration options

        Returns:
            AsyncEngine configured for the external database

        Example:
            engine = db_manager.create_external_engine(
                "mssql+aioodbc://user:pass@host/db?driver=ODBC+Driver+17+for+SQL+Server"
            )
        """
        # Handle different database URL formats
        processed_url = db_url

        # SQL Server URL conversion - ensure async driver (aioodbc)
        if "mssql" in db_url.lower() or "sqlserver" in db_url.lower():
            # Replace sync drivers with async drivers
            if "+pyodbc://" in db_url:
                # Convert pyodbc (sync) to aioodbc (async)
                processed_url = db_url.replace("+pyodbc://", "+aioodbc://")
                logger.info("Converted +pyodbc to +aioodbc for async support")
            elif "mssql://" in db_url:
                # Add aioodbc driver
                processed_url = db_url.replace("mssql://", "mssql+aioodbc://")
                logger.info("Added aioodbc driver to mssql URL")
            elif "sqlserver://" in db_url:
                # Convert sqlserver to mssql+aioodbc
                processed_url = db_url.replace("sqlserver://", "mssql+aioodbc://")
                logger.info("Converted sqlserver to mssql+aioodbc")
            # If it already has +aioodbc, leave it as is

        # Default engine configuration optimized for external connections
        engine_config = {
            "echo": False,
            "pool_pre_ping": True,  # Verify connections before using
            "pool_recycle": 3600,   # Recycle connections after 1 hour
            "pool_size": 2,         # Small pool for external connections
            "max_overflow": 3,      # Maximum 5 total connections
        }

        # Override with user-provided kwargs
        engine_config.update(kwargs)

        logger.info(f"Creating external engine for: {processed_url.split('@')[0]}@...")

        return create_async_engine(processed_url, **engine_config)

    async def execute_external_query(
        self,
        db_url: str,
        query: str,
        params: Optional[Dict[str, Any]] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Execute a query on an external database and return the first result as a dict.

        This method creates a temporary engine, executes the query, and properly
        disposes of the engine afterward. Ideal for one-off queries to external databases.

        Args:
            db_url: Database connection URL
            query: SQL query to execute (can use :param_name for parameters)
            params: Optional dictionary of parameters for the query

        Returns:
            Dict with column names as keys, or None if no results

        Raises:
            Exception: If query execution fails

        Example:
            result = await db_manager.execute_external_query(
                db_url="mssql+aioodbc://...",
                query="EXEC sp_GetData @id = :id",
                params={"id": 123}
            )
        """
        engine: Optional[AsyncEngine] = None

        try:
            # Create engine for this query
            engine = self.create_external_engine(db_url)

            # Execute query
            async with engine.begin() as conn:
                result = await conn.execute(
                    text(query),
                    params or {}
                )
                row = result.fetchone()

                if not row:
                    return None

                # Convert SQLAlchemy Row to dict
                if hasattr(row, "_mapping"):
                    return dict(row._mapping)
                elif hasattr(row, "_asdict"):
                    return row._asdict()
                else:
                    # Fallback: try to convert manually
                    return {key: getattr(row, key) for key in row._fields}

        except Exception as e:
            logger.error(f"Error executing external query: {e}", exc_info=True)
            raise
        finally:
            # Always dispose of the engine
            if engine:
                await engine.dispose()
                logger.debug("External engine disposed")

    async def execute_external_query_all(
        self,
        db_url: str,
        query: str,
        params: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Execute a query on an external database and return ALL results as a list of dicts.

        This method creates a temporary engine, executes the query, and properly
        disposes of the engine afterward. Ideal for queries that return multiple rows.

        Args:
            db_url: Database connection URL
            query: SQL query to execute (can use :param_name for parameters)
            params: Optional dictionary of parameters for the query

        Returns:
            List of dicts with column names as keys, empty list if no results

        Raises:
            Exception: If query execution fails

        Example:
            results = await db_manager.execute_external_query_all(
                db_url="mssql+aioodbc://...",
                query="EXEC sp_GetAllData @filter = :filter",
                params={"filter": "active"}
            )
        """
        engine: Optional[AsyncEngine] = None

        try:
            # Create engine for this query
            engine = self.create_external_engine(db_url)

            # Execute query
            async with engine.begin() as conn:
                result = await conn.execute(
                    text(query),
                    params or {}
                )
                rows = result.fetchall()

                if not rows:
                    return []

                # Convert all SQLAlchemy Rows to dicts
                results = []
                for row in rows:
                    if hasattr(row, "_mapping"):
                        results.append(dict(row._mapping))
                    elif hasattr(row, "_asdict"):
                        results.append(row._asdict())
                    else:
                        # Fallback: try to convert manually
                        results.append({key: getattr(row, key) for key in row._fields})

                return results

        except Exception as e:
            logger.error(f"Error executing external query (all): {e}", exc_info=True)
            raise
        finally:
            # Always dispose of the engine
            if engine:
                await engine.dispose()
                logger.debug("External engine disposed")


# Global database manager instance
db_manager = DatabaseManager()
