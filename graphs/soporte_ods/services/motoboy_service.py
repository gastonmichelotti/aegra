"""Motoboy Service - Business logic for motoboy operations"""

import random
import logging
from typing import Dict, Any, Optional

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
            # TODO: Implement actual database query using Aegra's database manager
            # For now, return error to indicate implementation needed
            logger.warning(
                f"Database query not yet implemented for mode {mode}. "
                f"Using mock data temporarily."
            )
            return {
                "success": True,
                "data": MotoboyService._generate_mock_motoboy(id_motoboy),
                "error": None,
                "message": "Motoboy encontrado (temporary mock - DB implementation pending)"
            }

            # Future implementation:
            # db_url = mode_config["db_url"]
            # query = f"EXEC sp_ChatBotODs_GetMotoboyInfo_By_Id @IdMotoboy = {id_motoboy}"
            # result = await execute_db_query(db_url, query)
            #
            # if not result:
            #     return {
            #         "success": False,
            #         "data": None,
            #         "error": "Motoboy no encontrado",
            #         "message": f"No se encontró motoboy con ID {id_motoboy}"
            #     }
            #
            # return {
            #     "success": True,
            #     "data": MotoboyModel(
            #         id_motoboy=result["id_motoboy"],
            #         nombre_completo=result["nombre_completo"],
            #         # ... map all fields
            #     ),
            #     "error": None,
            #     "message": "Motoboy encontrado correctamente"
            # }

        except Exception as e:
            logger.error(f"Error obteniendo motoboy {id_motoboy}: {e}")
            return {
                "success": False,
                "data": None,
                "error": str(e),
                "message": f"Error al obtener motoboy: {e}"
            }

    @staticmethod
    def _generate_mock_motoboy(id_motoboy: int) -> MotoboyModel:
        """Generate deterministic mock motoboy for testing

        Args:
            id_motoboy: Motoboy ID (used as seed for determinism)

        Returns:
            MotoboyModel with mock data
        """
        random.seed(id_motoboy)

        id_vehiculo = random.choice([1, 4])
        condicion_iva = random.choice([0, 1, 2])
        latitud = random.uniform(-34.7056, -34.5265)
        longitud = random.uniform(-58.5315, -58.3314)

        return MotoboyModel(
            id_motoboy=id_motoboy,
            nombre_completo="Juan Pérez",
            id_vehiculo=id_vehiculo,
            nombre_vehiculo="Moto" if id_vehiculo == 1 else "Bici",
            id_condicion_iva=condicion_iva,
            nombre_condicion_iva=(
                "NN" if condicion_iva == 0
                else "Monotributista" if condicion_iva == 1
                else "Responsable Inscripto"
            ),
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
