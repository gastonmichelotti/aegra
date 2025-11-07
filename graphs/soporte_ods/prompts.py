"""System prompts for Soporte ODS agent"""

from typing import Optional, List, Dict, Any
from datetime import datetime

from .models import MotoboyModel, ViajeModel, ReservaModel


SYSTEM_PROMPT_TEMPLATE = """
Eres un asistente de soporte para repartidores de Pedidos Ya en Argentina.

ESPECIALIZACIÓN POR DOMINIO:
- **VIAJES/ENTREGAS**: Usa `gestionar_estado_viaje` para liberar, cancelar o marcar viajes
- **DOCUMENTACIÓN/POLÍTICAS**: Usa `search_instructivo_general` para buscar en instructivos
- **BONOS/DESAFÍOS**: Usa `obtener_desafios` para consultar desafíos activos
- **UBICACIÓN**: Usa `get_motoboy_location` para obtener ubicación en tiempo real
- **ESCALACIÓN**: Usa `derive_to_human` cuando necesites derivar a soporte humano

CONFIRMACIONES OBLIGATORIAS:
- SIEMPRE pide confirmación explícita antes de ejecutar cambios de estado en viajes
- Deduce el motivo del cambio desde la conversación (no lo preguntes explícitamente)
- Usa la información de contexto para entender la situación del motoboy

REGLAS IMPORTANTES:
1. Responde en español argentino, de forma clara y amigable
2. Usa la tool de RAG UNA SOLA VEZ por query, luego sintetiza la respuesta
3. Si no sabes algo, admítelo y ofrece derivar a humano
4. Prioriza la experiencia del usuario - sé conciso pero completo

CONTEXTO DEL MOTOBOY:
{motoboy_context}

VIAJE ACTUAL:
{viaje_context}

RESERVA ACTIVA:
{reserva_context}

UBICACIÓN:
{location_context}

---
Fecha y hora actual: {current_datetime}
"""


def build_system_prompt(
    motoboy: Optional[MotoboyModel] = None,
    viaje: Optional[ViajeModel | List[ViajeModel]] = None,
    reserva: Optional[ReservaModel] = None,
    location: Optional[Dict[str, Any]] = None,
) -> str:
    """Build system prompt with current context

    Args:
        motoboy: Motoboy model instance
        viaje: Viaje model instance or list of instances
        reserva: Reserva model instance
        location: Location dict from Firebase

    Returns:
        Complete system prompt with context injected
    """
    return SYSTEM_PROMPT_TEMPLATE.format(
        motoboy_context=_format_motoboy(motoboy),
        viaje_context=_format_viaje(viaje),
        reserva_context=_format_reserva(reserva),
        location_context=_format_location(location),
        current_datetime=datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    )


def _format_motoboy(motoboy: Optional[MotoboyModel]) -> str:
    """Format motoboy context for prompt"""
    if not motoboy:
        return "No disponible"

    return f"""
- ID: {motoboy.id_motoboy}
- Nombre: {motoboy.nombre_completo or 'N/A'}
- Vehículo: {motoboy.nombre_vehiculo or 'N/A'}
- Condición IVA: {motoboy.nombre_condicion_iva or 'N/A'}
- Modalidad: {motoboy.modalidad_rapiboy or 'N/A'}
""".strip()


def _format_viaje(viaje: Optional[ViajeModel | List[ViajeModel]]) -> str:
    """Format viaje context for prompt"""
    if not viaje:
        return "Sin viajes activos"

    # Handle single viaje
    if isinstance(viaje, ViajeModel):
        return f"""
- ID Viaje: {viaje.id_viaje}
- Estado: {viaje.nombre_estado}
- Origen: {viaje.direccion_origen or 'N/A'}
- Destino: {viaje.direccion_destino or 'N/A'}
- Distancia entrega: {viaje.distancia_entrega:.2f} km
""".strip()

    # Handle multiple viajes
    if isinstance(viaje, list) and viaje:
        formatted = "\n\n".join([
            f"**Viaje {i+1}** (ID: {v.id_viaje})\n- Estado: {v.nombre_estado}\n- Destino: {v.direccion_destino or 'N/A'}"
            for i, v in enumerate(viaje)
        ])
        return formatted

    return "Sin viajes activos"


def _format_reserva(reserva: Optional[ReservaModel]) -> str:
    """Format reserva context for prompt"""
    if not reserva:
        return "Sin reserva activa"

    return f"""
- ID Reserva: {reserva.id_reserva}
- Horario: {reserva.fecha_desde.strftime("%H:%M")} - {reserva.fecha_hasta.strftime("%H:%M")}
- Vehículo: {reserva.nombre_vehiculo}
- Viajes entregados: {reserva.cantidad_viajes_entregados}
- Rechazos: {reserva.cantidad_rechazos}/{reserva.cantidad_rechazos_maxima or '?'}
- Cumple condiciones: Viajes={reserva.cumple_condicion_minimo_viajes}, Rechazos={reserva.cumple_condicion_cantidad_rechazos}, Puntualidad={reserva.cumple_condicion_puntualidad}
""".strip()


def _format_location(location: Optional[Dict[str, Any]]) -> str:
    """Format location context for prompt"""
    if not location:
        return "Ubicación no disponible"

    lat = location.get("latitude")
    lng = location.get("longitude")

    if lat and lng:
        return f"Lat: {lat:.6f}, Lng: {lng:.6f}"

    return "Ubicación no disponible"
