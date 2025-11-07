"""Desafio Service - Business logic for desafio (challenges/bonuses) operations"""

import random
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List
import httpx

from ..models.desafio import DesafioModel, DetalleDesafioModel, DesafioResponseModel
from ..config.mode_config import get_mode_config

logger = logging.getLogger(__name__)


class DesafioService:
    """Service for desafio-related business operations"""

    @staticmethod
    async def get_by_id_motoboy(id_motoboy: int, mode: int = 1) -> Dict[str, Any]:
        """Get active challenges/bonuses for a motoboy

        Args:
            id_motoboy: Motoboy ID
            mode: MODE (1=prod, 2=staging, 3=eval)

        Returns:
            Dict with structure:
            {
                "success": bool,
                "data": DesafioResponseModel | None,
                "error": str | None,
                "message": str
            }
        """
        if not id_motoboy or id_motoboy <= 0:
            raise ValueError("ID de motoboy debe ser un número positivo")

        mode_config = get_mode_config(mode)

        # MODE 3: Return mock data
        if mode_config["use_mock_data"]:
            random.seed(id_motoboy)
            # 70% chance of having active challenges
            has_desafios = random.random() > 0.3

            if has_desafios:
                desafios = DesafioService._generate_mock_desafios(id_motoboy)
                return {
                    "success": True,
                    "data": DesafioResponseModel(
                        desafios=desafios,
                        message=f"Se encontraron {len(desafios)} desafíos activos (mock data)"
                    ),
                    "error": None,
                    "message": f"Se encontraron {len(desafios)} desafíos activos"
                }
            else:
                return {
                    "success": True,
                    "data": DesafioResponseModel(
                        desafios=[],
                        message="No hay desafíos activos en este momento"
                    ),
                    "error": None,
                    "message": "No hay desafíos activos"
                }

        # MODE 1 & 2: Call external API
        try:
            api_base_url = mode_config["api_base_url"]
            url = f"{api_base_url}/v7/Rapiboy/BonoSemanal"

            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.put(
                    url,
                    headers={
                        "Content-Type": "application/json",
                        "Accept": "application/json"
                    },
                    json={"IdMotoboy": id_motoboy}
                )

            if response.status_code == 200:
                data = response.json()
                bonos = data.get("Bonos", [])

                if not bonos:
                    return {
                        "success": True,
                        "data": DesafioResponseModel(
                            desafios=[],
                            message="No hay desafíos activos en este momento"
                        ),
                        "error": None,
                        "message": "No hay desafíos activos"
                    }

                # Map API response to our models
                desafios = []
                for bono in bonos:
                    detalles = [
                        DetalleDesafioModel(
                            id_desafio=detalle.get("IdDesafio"),
                            cantidad_viajes=detalle.get("CantidadViajes"),
                            monto_premio=detalle.get("MontoPremio")
                        )
                        for detalle in bono.get("Detalles", [])
                    ]

                    desafio = DesafioModel(
                        id_desafio=bono.get("IdDesafio"),
                        id_tipo=bono.get("IdTipo"),
                        nombre_tipo=bono.get("NombreTipo"),
                        nombre_desafio=bono.get("NombreDesafio"),
                        condiciones=bono.get("Condiciones"),
                        monto_ganado_al_momento=bono.get("MontoGanadoAlMomento"),
                        descripcion=bono.get("Descripcion"),
                        fecha_inicio=bono.get("FechaInicio"),
                        fecha_fin=bono.get("FechaFin"),
                        viajes_realizados=bono.get("ViajesRealizados"),
                        detalles=detalles if detalles else None,
                        message=None
                    )
                    desafios.append(desafio)

                return {
                    "success": True,
                    "data": DesafioResponseModel(
                        desafios=desafios,
                        message=f"Se encontraron {len(desafios)} desafíos activos"
                    ),
                    "error": None,
                    "message": f"Se encontraron {len(desafios)} desafíos activos"
                }
            else:
                logger.error(f"API returned status {response.status_code}")
                return {
                    "success": False,
                    "data": None,
                    "error": f"API error: status {response.status_code}",
                    "message": "Error al obtener desafíos de la API"
                }

        except Exception as e:
            logger.error(f"Error obteniendo desafíos para motoboy {id_motoboy}: {e}")
            # Fallback to mock data on error
            logger.warning("Falling back to mock data due to API error")
            desafios = DesafioService._generate_mock_desafios(id_motoboy)
            return {
                "success": True,
                "data": DesafioResponseModel(
                    desafios=desafios,
                    message=f"Se encontraron {len(desafios)} desafíos (fallback mock)"
                ),
                "error": None,
                "message": f"Se encontraron {len(desafios)} desafíos (fallback debido a error de API)"
            }

    @staticmethod
    def _generate_mock_desafios(id_motoboy: int) -> List[DesafioModel]:
        """Generate deterministic mock challenges for testing"""
        random.seed(id_motoboy)

        num_desafios = random.randint(1, 3)
        desafios = []

        now = datetime.now()

        for i in range(num_desafios):
            random.seed(id_motoboy + i)

            # Challenge types
            tipos = [
                (1, "Bono Semanal"),
                (2, "Desafío Diario"),
                (3, "Bono Especial")
            ]
            id_tipo, nombre_tipo = random.choice(tipos)

            # Generate detalles (tiers)
            num_detalles = random.randint(2, 4)
            detalles = []
            for j in range(num_detalles):
                cantidad_viajes = (j + 1) * 10  # 10, 20, 30, 40
                monto_premio = (j + 1) * 500   # 500, 1000, 1500, 2000

                detalles.append(DetalleDesafioModel(
                    id_desafio=1000 + i,
                    cantidad_viajes=cantidad_viajes,
                    monto_premio=float(monto_premio)
                ))

            viajes_realizados = random.randint(0, 35)
            monto_ganado = sum(
                d.monto_premio for d in detalles
                if viajes_realizados >= d.cantidad_viajes
            )

            desafio = DesafioModel(
                id_desafio=1000 + i,
                id_tipo=id_tipo,
                nombre_tipo=nombre_tipo,
                nombre_desafio=f"{nombre_tipo} {now.strftime('%B')}",
                condiciones="Completa la cantidad de viajes indicada para ganar el bono",
                monto_ganado_al_momento=float(monto_ganado),
                descripcion=f"Desafío de {nombre_tipo.lower()} - múltiples niveles de premio",
                fecha_inicio=now - timedelta(days=random.randint(1, 7)),
                fecha_fin=now + timedelta(days=random.randint(1, 7)),
                viajes_realizados=viajes_realizados,
                detalles=detalles,
                message=None
            )
            desafios.append(desafio)

        return desafios
