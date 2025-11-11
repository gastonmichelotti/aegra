"""Viaje Service - Business logic for viaje (trip) operations"""

import random
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional

from src.agent_server.core.database import db_manager
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
            db_url = mode_config.get("db_url")

            if not db_url:
                logger.error(f"db_url not configured for mode {mode}")
                return {
                    "success": False,
                    "data": None,
                    "error": "Database URL not configured",
                    "message": f"Database URL no está configurada para mode {mode}"
                }

            # Execute stored procedure to get active viaje info
            result = await ViajeService._execute_db_query_by_motoboy(db_url, id_motoboy)

            if not result:
                return {
                    "success": False,
                    "data": None,
                    "error": "Viaje no encontrado",
                    "message": f"No se encontró viaje activo para motoboy {id_motoboy}"
                }

            # Map database result to ViajeModel
            viaje = ViajeService._map_result_to_viaje(result)

            return {
                "success": True,
                "data": viaje,
                "error": None,
                "message": "Viaje activo encontrado correctamente"
            }

        except Exception as e:
            logger.error(f"Error obteniendo viaje para motoboy {id_motoboy}: {e}", exc_info=True)
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
            db_url = mode_config.get("db_url")

            if not db_url:
                logger.error(f"db_url not configured for mode {mode}")
                return {
                    "success": False,
                    "data": None,
                    "error": "Database URL not configured",
                    "message": f"Database URL no está configurada para mode {mode}"
                }

            # Execute stored procedure to get all viajes for reserva
            results = await ViajeService._execute_db_query_by_reserva(db_url, id_reserva)

            if not results:
                return {
                    "success": False,
                    "data": None,
                    "error": "Viajes no encontrados",
                    "message": f"No se encontraron viajes para reserva {id_reserva}"
                }

            # Map database results to ViajeModel list
            viajes = [ViajeService._map_result_to_viaje(result) for result in results]

            return {
                "success": True,
                "data": viajes,
                "error": None,
                "message": f"Se encontraron {len(viajes)} viajes correctamente"
            }

        except Exception as e:
            logger.error(f"Error obteniendo viajes para reserva {id_reserva}: {e}", exc_info=True)
            return {
                "success": False,
                "data": None,
                "error": str(e),
                "message": f"Error al obtener viajes: {e}"
            }

    @staticmethod
    async def _execute_db_query_by_motoboy(db_url: str, id_motoboy: int) -> Optional[Dict[str, Any]]:
        """Execute database query to get active viaje for a motoboy using DatabaseManager

        Args:
            db_url: Database connection URL
            id_motoboy: Motoboy ID to query

        Returns:
            Dict with viaje data or None if not found

        Raises:
            Exception: If database query fails
        """
        query = "EXEC sp_ChatBotODS_GetViajesActivos_By_IdMotoboy @IdMotoboy = :id_motoboy"

        # DatabaseManager handles engine creation/disposal and error logging automatically
        return await db_manager.execute_external_query(
            db_url=db_url,
            query=query,
            params={"id_motoboy": id_motoboy}
        )

    @staticmethod
    async def _execute_db_query_by_reserva(db_url: str, id_reserva: int) -> List[Dict[str, Any]]:
        """Execute database query to get all viajes for a reserva using DatabaseManager

        Args:
            db_url: Database connection URL
            id_reserva: Reserva ID to query

        Returns:
            List of dicts with viaje data, empty list if not found

        Raises:
            Exception: If database query fails
        """
        query = "EXEC sp_ChatBotODs_GetViajes_By_IdReserva @IdReserva = :id_reserva"

        # DatabaseManager handles engine creation/disposal and error logging automatically
        return await db_manager.execute_external_query_all(
            db_url=db_url,
            query=query,
            params={"id_reserva": id_reserva}
        )

    @staticmethod
    def _map_result_to_viaje(result: Dict[str, Any]) -> ViajeModel:
        """Map database result dictionary to ViajeModel

        Args:
            result: Dictionary with viaje data from database

        Returns:
            ViajeModel instance
        """
        return ViajeModel(
            id_viaje=result.get("id_viaje"),
            id_reserva=result.get("id_reserva"),
            id_motoboy=result.get("id_motoboy"),
            direccion_origen=result.get("direccion_origen"),
            direccion_destino=result.get("direccion_destino"),
            latitud_origen=result.get("latitud_origen"),
            longitud_origen=result.get("longitud_origen"),
            latitud_destino=result.get("latitud_destino"),
            longitud_destino=result.get("longitud_destino"),
            distancia_pickeo=result.get("distancia_pickeo"),
            distancia_entrega=result.get("distancia_entrega"),
            id_estado=result.get("id_estado"),
            nombre_estado=result.get("nombre_estado"),
            fecha_asignacion_reserva=result.get("fecha_asignacion_reserva"),
            fecha_llegada_local=result.get("fecha_llegada_local"),
            fecha_salida_local=result.get("fecha_salida_local"),
            fecha_llegada_cliente=result.get("fecha_llegada_cliente"),
            fecha_entregado=result.get("fecha_entregado"),
            fecha_llegada_local_estimada=result.get("fecha_llegada_local_estimada"),
            fecha_salida_local_estimada=result.get("fecha_salida_local_estimada"),
            fecha_llegada_cliente_estimada=result.get("fecha_llegada_cliente_estimada"),
            fecha_entregado_estimada=result.get("fecha_entregado_estimada"),
            message="Viaje encontrado correctamente"
        )

    @staticmethod
    def _generate_mock_viaje(seed: int) -> ViajeModel:
        """Generate deterministic mock viaje for testing

        Uses seed as random seed to ensure deterministic results.
        Same seed will always generate the same mock data.

        Args:
            seed: Random seed for determinism

        Returns:
            ViajeModel with mock data
        """
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
