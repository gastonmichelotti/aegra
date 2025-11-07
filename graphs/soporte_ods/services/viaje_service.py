"""Viaje Service - Business logic for viaje (trip) operations"""

import random
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional

from ..models.viaje import ViajeModel
from ..config.mode_config import get_mode_config

logger = logging.getLogger(__name__)


class ViajeService:
    """Service for viaje-related business operations"""

    @staticmethod
    async def get_by_id_motoboy(id_motoboy: int, mode: int = 1) -> Dict[str, Any]:
        """Get active trip for a motoboy

        Args:
            id_motoboy: Motoboy ID
            mode: MODE (1=prod, 2=staging, 3=eval)

        Returns:
            Dict with structure:
            {
                "success": bool,
                "data": ViajeModel | None,
                "error": str | None,
                "message": str
            }
        """
        if not id_motoboy or id_motoboy <= 0:
            raise ValueError("ID de motoboy debe ser un número positivo")

        mode_config = get_mode_config(mode)

        # MODE 3: Return mock data
        if mode_config["use_mock_data"]:
            # 50% chance of having an active trip
            random.seed(id_motoboy)
            has_trip = random.random() > 0.5

            if has_trip:
                return {
                    "success": True,
                    "data": ViajeService._generate_mock_viaje(id_motoboy),
                    "error": None,
                    "message": "Viaje activo encontrado (mock data)"
                }
            else:
                return {
                    "success": False,
                    "data": None,
                    "error": "Viaje no encontrado",
                    "message": f"No se encontró viaje activo para motoboy {id_motoboy}"
                }

        # MODE 1 & 2: Query database
        try:
            # TODO: Implement database query
            logger.warning(
                f"Database query not yet implemented for mode {mode}. "
                f"Using mock data temporarily."
            )
            return {
                "success": True,
                "data": ViajeService._generate_mock_viaje(id_motoboy),
                "error": None,
                "message": "Viaje encontrado (temporary mock - DB implementation pending)"
            }

        except Exception as e:
            logger.error(f"Error obteniendo viaje para motoboy {id_motoboy}: {e}")
            return {
                "success": False,
                "data": None,
                "error": str(e),
                "message": f"Error al obtener viaje: {e}"
            }

    @staticmethod
    async def get_by_id_reserva(id_reserva: int, mode: int = 1) -> Dict[str, Any]:
        """Get all trips for a reservation

        Args:
            id_reserva: Reservation ID
            mode: MODE (1=prod, 2=staging, 3=eval)

        Returns:
            Dict with structure:
            {
                "success": bool,
                "data": List[ViajeModel] | None,
                "error": str | None,
                "message": str
            }
        """
        if not id_reserva or id_reserva <= 0:
            raise ValueError("ID de reserva debe ser un número positivo")

        mode_config = get_mode_config(mode)

        # MODE 3: Return mock data
        if mode_config["use_mock_data"]:
            random.seed(id_reserva)
            num_trips = random.randint(0, 3)

            if num_trips == 0:
                return {
                    "success": False,
                    "data": None,
                    "error": "Viajes no encontrados",
                    "message": f"No se encontraron viajes para reserva {id_reserva}"
                }

            trips = [
                ViajeService._generate_mock_viaje(id_reserva + i)
                for i in range(num_trips)
            ]

            return {
                "success": True,
                "data": trips,
                "error": None,
                "message": f"Se encontraron {num_trips} viajes (mock data)"
            }

        # MODE 1 & 2: Query database
        try:
            # TODO: Implement database query
            logger.warning(
                f"Database query not yet implemented for mode {mode}. "
                f"Using mock data temporarily."
            )
            return {
                "success": True,
                "data": [ViajeService._generate_mock_viaje(id_reserva)],
                "error": None,
                "message": "Viajes encontrados (temporary mock - DB implementation pending)"
            }

        except Exception as e:
            logger.error(f"Error obteniendo viajes para reserva {id_reserva}: {e}")
            return {
                "success": False,
                "data": None,
                "error": str(e),
                "message": f"Error al obtener viajes: {e}"
            }

    @staticmethod
    def _generate_mock_viaje(seed: int) -> ViajeModel:
        """Generate deterministic mock viaje for testing"""
        random.seed(seed)

        now = datetime.now()
        estados = [
            (1, "En camino a retirar"),
            (2, "En local"),
            (3, "Retirado"),
            (4, "En domicilio cliente"),
            (5, "Entregado")
        ]
        id_estado, nombre_estado = random.choice(estados[:3])  # Only active states

        return ViajeModel(
            id_viaje=seed * 100,
            id_reserva=seed,
            id_motoboy=seed,
            direccion_origen="Av. Corrientes 1234, CABA",
            direccion_destino="Av. Santa Fe 5678, CABA",
            latitud_origen=-34.603722,
            longitud_origen=-58.381592,
            latitud_destino=-34.594822,
            longitud_destino=-58.373451,
            distancia_pickeo=random.uniform(0.5, 3.0),
            distancia_entrega=random.uniform(1.0, 5.0),
            id_estado=id_estado,
            nombre_estado=nombre_estado,
            fecha_asignacion_reserva=now - timedelta(minutes=random.randint(5, 30)),
            fecha_llegada_local=now - timedelta(minutes=random.randint(0, 10)) if id_estado >= 2 else None,
            fecha_salida_local=now - timedelta(minutes=random.randint(0, 5)) if id_estado >= 3 else None,
            fecha_llegada_cliente=None,
            fecha_entregado=None,
            fecha_llegada_local_estimada=now + timedelta(minutes=random.randint(5, 15)),
            fecha_salida_local_estimada=now + timedelta(minutes=random.randint(10, 20)),
            fecha_llegada_cliente_estimada=now + timedelta(minutes=random.randint(20, 40)),
            fecha_entregado_estimada=now + timedelta(minutes=random.randint(25, 45)),
            message="Viaje encontrado correctamente"
        )
