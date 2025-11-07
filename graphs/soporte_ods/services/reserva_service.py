"""Reserva Service - Business logic for reserva (shift/reservation) operations"""

import random
import logging
from datetime import datetime, timedelta
from typing import Dict, Any

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
            # TODO: Implement database query
            logger.warning(
                f"Database query not yet implemented for mode {mode}. "
                f"Using mock data temporarily."
            )
            return {
                "success": True,
                "data": ReservaService._generate_mock_reserva(id_motoboy),
                "error": None,
                "message": "Reserva encontrada (temporary mock - DB implementation pending)"
            }

        except Exception as e:
            logger.error(f"Error obteniendo reserva para motoboy {id_motoboy}: {e}")
            return {
                "success": False,
                "data": None,
                "error": str(e),
                "message": f"Error al obtener reserva: {e}"
            }

    @staticmethod
    def _generate_mock_reserva(id_motoboy: int) -> ReservaModel:
        """Generate deterministic mock reserva for testing"""
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
