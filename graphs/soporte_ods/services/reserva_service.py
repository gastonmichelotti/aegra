"""Reserva Service - Business logic for reserva (shift/reservation) operations"""

import random
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, Optional

from src.agent_server.core.database import db_manager
from ..models.reserva import ReservaModel
from ..config.mode_config import get_mode_config

logger = logging.getLogger(__name__)


class ReservaService:
    """Service for reserva-related business operations"""

    @staticmethod
    async def get_by_id_motoboy(id_motoboy: int, mode: int = 1) -> Dict[str, Any]:
        """Get active reservation for a motoboy

        Args:
            id_motoboy: Motoboy ID
            mode: MODE (1=prod, 2=staging, 3=eval)

        Returns:
            Dict with structure:
            {
                "success": bool,
                "data": ReservaModel | None,
                "error": str | None,
                "message": str
            }
        """
        if not id_motoboy or id_motoboy <= 0:
            raise ValueError("ID de motoboy debe ser un número positivo")

        mode_config = get_mode_config(mode)

        # MODE 3: Return mock data
        if mode_config["use_mock_data"]:
            # 80% chance of having an active reservation
            random.seed(id_motoboy)
            has_reserva = random.random() > 0.2

            if has_reserva:
                return {
                    "success": True,
                    "data": ReservaService._generate_mock_reserva(id_motoboy),
                    "error": None,
                    "message": "Reserva activa encontrada (mock data)"
                }
            else:
                return {
                    "success": False,
                    "data": None,
                    "error": "Reserva no encontrada",
                    "message": f"No se encontró reserva activa para motoboy {id_motoboy}"
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

            # Execute stored procedure to get reserva info
            result = await ReservaService._execute_db_query(db_url, id_motoboy)

            if not result:
                return {
                    "success": False,
                    "data": None,
                    "error": "Reserva no encontrada",
                    "message": f"No se encontró reserva activa para motoboy {id_motoboy}"
                }

            # Map database result to ReservaModel
            reserva = ReservaModel(
                id_reserva=result.get("id_reserva"),
                fecha_desde=result.get("fecha_desde"),
                fecha_hasta=result.get("fecha_hasta"),
                fecha_llego=result.get("fecha_llego"),
                id_vehiculo=result.get("id_vehiculo"),
                nombre_vehiculo=result.get("nombre_vehiculo"),
                tiene_autoaceptacion=result.get("tiene_autoaceptacion"),
                repartidor_disponible=result.get("repartidor_disponible"),
                cantidad_viajes_entregados=result.get("cantidad_viajes_entregados"),
                cantidad_rechazos=result.get("cantidad_rechazos"),
                cantidad_rechazos_maxima=result.get("cantidad_rechazos_maxima"),
                cantidad_viajes_minimo_asegurado=result.get("cantidad_viajes_minimo_asegurado"),
                cumple_condicion_minimo_viajes=result.get("cumple_condicion_minimo_viajes"),
                cumple_condicion_cantidad_rechazos=result.get("cumple_condicion_cantidad_rechazos"),
                cumple_condicion_puntualidad=result.get("cumple_condicion_puntualidad"),
                minutos_no_disponible=result.get("minutos_no_disponible"),
                cantidad_maxima_minutos_no_conectado=result.get("cantidad_maxima_minutos_no_conectado"),
                cumple_condicion_conexion=result.get("cumple_condicion_conexion"),
                ganancia_minima_asegurada_correspondiente=result.get("ganancia_minima_asegurada_correspondiente"),
                message="Reserva encontrada correctamente"
            )

            return {
                "success": True,
                "data": reserva,
                "error": None,
                "message": "Reserva encontrada correctamente"
            }

        except Exception as e:
            logger.error(f"Error obteniendo reserva para motoboy {id_motoboy}: {e}", exc_info=True)
            return {
                "success": False,
                "data": None,
                "error": str(e),
                "message": f"Error al obtener reserva: {e}"
            }

    @staticmethod
    async def _execute_db_query(db_url: str, id_motoboy: int) -> Optional[Dict[str, Any]]:
        """Execute database query to get reserva information using DatabaseManager

        Args:
            db_url: Database connection URL
            id_motoboy: Motoboy ID to query

        Returns:
            Dict with reserva data or None if not found

        Raises:
            Exception: If database query fails
        """
        query = "EXEC sp_ChatBotODs_GetReservaActiva_By_IdMotoboy @IdMotoboy = :id_motoboy"

        # DatabaseManager handles engine creation/disposal and error logging automatically
        return await db_manager.execute_external_query(
            db_url=db_url,
            query=query,
            params={"id_motoboy": id_motoboy}
        )

    @staticmethod
    def _generate_mock_reserva(id_motoboy: int) -> ReservaModel:
        """Generate deterministic mock reserva for testing

        Uses id_motoboy as random seed to ensure deterministic results.
        Same ID will always generate the same mock data.

        Args:
            id_motoboy: Motoboy ID (used as seed for determinism)

        Returns:
            ReservaModel with mock data
        """
        random.seed(id_motoboy)

        now = datetime.now()
        # Typical shift: 4-6 hours
        shift_duration = random.randint(4, 6)

        # Shift started 1-2 hours ago
        shift_start = now - timedelta(hours=random.randint(1, 2))
        shift_end = shift_start + timedelta(hours=shift_duration)

        # Motoboy arrived on time or slightly late
        arrived = shift_start + timedelta(minutes=random.randint(-5, 15))

        # Performance metrics
        viajes_entregados = random.randint(0, 8)
        rechazos = random.randint(0, 3)
        minutos_no_disponible = random.randint(0, 30)

        # Targets
        viajes_minimo = random.randint(5, 10)
        rechazos_maximos = random.randint(3, 5)
        minutos_max_no_conectado = random.uniform(30, 60)

        # Compliance
        cumple_viajes = viajes_entregados >= viajes_minimo
        cumple_rechazos = rechazos <= rechazos_maximos
        cumple_puntualidad = (arrived - shift_start).total_seconds() <= 600  # 10 min grace
        cumple_conexion = minutos_no_disponible <= minutos_max_no_conectado

        # Vehicle type
        id_vehiculo = random.choice([1, 4])

        return ReservaModel(
            id_reserva=id_motoboy * 1000,
            fecha_desde=shift_start,
            fecha_hasta=shift_end,
            fecha_llego=arrived,
            id_vehiculo=id_vehiculo,
            nombre_vehiculo="Moto" if id_vehiculo == 1 else "Bici",
            tiene_autoaceptacion=random.choice([True, False]),
            repartidor_disponible=True,
            cantidad_viajes_entregados=viajes_entregados,
            cantidad_rechazos=rechazos,
            cantidad_rechazos_maxima=rechazos_maximos,
            cantidad_viajes_minimo_asegurado=viajes_minimo,
            cumple_condicion_minimo_viajes=cumple_viajes,
            cumple_condicion_cantidad_rechazos=cumple_rechazos,
            cumple_condicion_puntualidad=cumple_puntualidad,
            minutos_no_disponible=minutos_no_disponible,
            cantidad_maxima_minutos_no_conectado=minutos_max_no_conectado,
            cumple_condicion_conexion=cumple_conexion,
            ganancia_minima_asegurada_correspondiente=random.randint(1000, 3000),
            message="Reserva encontrada correctamente"
        )
