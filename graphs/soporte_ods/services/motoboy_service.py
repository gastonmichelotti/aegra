"""Motoboy Service - Business logic for motoboy operations"""

import random
import logging
from typing import Dict, Any, Optional

from src.agent_server.core.database import db_manager
from ..models.motoboy import MotoboyModel
from ..config.mode_config import get_mode_config

logger = logging.getLogger(__name__)


class MotoboyService:
    """Service for motoboy-related business operations"""

    @staticmethod
    async def get_by_id(id_motoboy: int, mode: int = 1) -> Dict[str, Any]:
        """Get motoboy by ID

        Args:
            id_motoboy: Motoboy ID
            mode: MODE (1=prod, 2=staging, 3=eval)

        Returns:
            Dict with structure:
            {
                "success": bool,
                "data": MotoboyModel | None,
                "error": str | None,
                "message": str
            }

        Raises:
            ValueError: If id_motoboy is invalid
        """
        if not id_motoboy or id_motoboy <= 0:
            raise ValueError("ID de motoboy debe ser un número positivo")

        mode_config = get_mode_config(mode)

        # MODE 3: Return mock data
        if mode_config["use_mock_data"]:
            return {
                "success": True,
                "data": MotoboyService._generate_mock_motoboy(id_motoboy),
                "error": None,
                "message": "Motoboy encontrado (mock data)"
            }

        # MODE 1 & 2: Query database
        try:
            db_url = mode_config.get("db_url")

            if not db_url:
                logger.error(f"db_url not configured for mode {mode}")
                return {
                    "success": False,
                    "data": None,
                    "error": "Database URL not configured",
                    "message": f"Database URL no está configurada para mode {mode}"
                }

            # Execute stored procedure to get motoboy info
            result = await MotoboyService._execute_db_query(db_url, id_motoboy)

            if not result:
                return {
                    "success": False,
                    "data": None,
                    "error": "Motoboy no encontrado",
                    "message": f"No se encontró motoboy con ID {id_motoboy}"
                }

            # Map database result to MotoboyModel
            motoboy = MotoboyModel(
                id_motoboy=result.get("id_motoboy", id_motoboy),
                nombre_completo=result.get("nombre_completo"),
                id_vehiculo=result.get("id_vehiculo"),
                nombre_vehiculo=result.get("nombre_vehiculo"),
                id_condicion_iva=result.get("id_condicion_iva"),
                nombre_condicion_iva=result.get("nombre_condicion_iva"),
                cuit=result.get("cuit"),
                cbu=result.get("cbu"),
                latitud_motoboy=result.get("latitud_motoboy"),
                longitud_motoboy=result.get("longitud_motoboy"),
                modalidad_rapiboy=result.get("modalidad_rapiboy"),
                message="Motoboy encontrado correctamente"
            )

            return {
                "success": True,
                "data": motoboy,
                "error": None,
                "message": "Motoboy encontrado correctamente"
            }

        except Exception as e:
            logger.error(f"Error obteniendo motoboy {id_motoboy}: {e}", exc_info=True)
            return {
                "success": False,
                "data": None,
                "error": str(e),
                "message": f"Error al obtener motoboy: {e}"
            }

    @staticmethod
    async def _execute_db_query(db_url: str, id_motoboy: int) -> Optional[Dict[str, Any]]:
        """Execute database query to get motoboy information using DatabaseManager

        Args:
            db_url: Database connection URL
            id_motoboy: Motoboy ID to query

        Returns:
            Dict with motoboy data or None if not found

        Raises:
            Exception: If database query fails
        """
        query = "EXEC sp_ChatBotODs_GetMotoboyInfo_By_Id @IdMotoboy = :id_motoboy"

        # DatabaseManager handles engine creation/disposal and error logging automatically
        return await db_manager.execute_external_query(
            db_url=db_url,
            query=query,
            params={"id_motoboy": id_motoboy}
        )

    @staticmethod
    def _generate_mock_motoboy(id_motoboy: int) -> MotoboyModel:
        """Generate deterministic mock motoboy for testing

        Uses id_motoboy as random seed to ensure deterministic results.
        Same ID will always generate the same mock data.

        Args:
            id_motoboy: Motoboy ID (used as seed for determinism)

        Returns:
            MotoboyModel with mock data
        """
        random.seed(id_motoboy)

        # Generate deterministic random values
        id_vehiculo = random.choice([1, 4])
        condicion_iva = random.choice([0, 1, 2])
        latitud = random.uniform(-34.7056, -34.5265)  # Buenos Aires area
        longitud = random.uniform(-58.5315, -58.3314)

        # Map condicion_iva to name
        condicion_iva_map = {
            0: "NN",
            1: "Monotributista",
            2: "Responsable Inscripto"
        }

        return MotoboyModel(
            id_motoboy=id_motoboy,
            nombre_completo="Juan Pérez",
            id_vehiculo=id_vehiculo,
            nombre_vehiculo="Moto" if id_vehiculo == 1 else "Bici",
            id_condicion_iva=condicion_iva,
            nombre_condicion_iva=condicion_iva_map[condicion_iva],
            cuit="12345678901",
            cbu="1234567890123456789012",
            latitud_motoboy=latitud,
            longitud_motoboy=longitud,
            modalidad_rapiboy=random.choice([
                "Rapiboy Clasico y Rapiboy Envíos Sueltos",
                "Envíos Sueltos"
            ]),
            message="Motoboy encontrado correctamente"
        )
