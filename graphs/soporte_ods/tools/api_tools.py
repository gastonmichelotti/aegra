"""API Tools - Tools for managing trips and challenges via external APIs"""

import logging
from typing import Any, Dict
from langgraph.prebuilt import InjectedState

from ..services import DesafioService

logger = logging.getLogger(__name__)


async def gestionar_estado_viaje(
    accion: str,
    id_viaje: int,
    motivo: str = "",
    state: InjectedState = None,
) -> str:
    """Gestionar el estado de un viaje (liberar, cancelar, marcar como no entregado)

    IMPORTANTE: Esta tool SIEMPRE debe pedir confirmación al usuario antes de ejecutar.
    Usar state['pending_confirmation'] para trackear confirmaciones pendientes.

    Args:
        accion: Acción a realizar ('liberar', 'cancelar', 'no_entregado')
        id_viaje: ID del viaje a gestionar
        motivo: Motivo del cambio de estado (opcional pero recomendado)
        state: Graph state (auto-injected by LangGraph)

    Returns:
        str: Resultado de la operación en formato legible

    Example:
        >>> await gestionar_estado_viaje("liberar", 12345, "Motoboy no puede completar el viaje")
    """
    # TODO: Implement actual API call to change trip state
    # This will call the external API endpoint: /v1/ChatBot/CambioEstadoViajeBot
    # with the appropriate parameters based on the action

    logger.warning("gestionar_estado_viaje not yet fully implemented")

    return f"""
    ⚠️  Tool gestionar_estado_viaje - PENDIENTE DE IMPLEMENTACIÓN

    Se solicitó: {accion} viaje {id_viaje}
    Motivo: {motivo or 'No especificado'}

    TODO: Implementar llamada a API /v1/ChatBot/CambioEstadoViajeBot
    TODO: Implementar lógica de confirmación usando state['pending_confirmation']
    TODO: Deducir código de motivo desde la conversación
    """


async def obtener_desafios(
    motoboy_id: int,
    mode: int = 1,
) -> str:
    """Obtener desafíos/bonos activos para un motoboy

    Args:
        motoboy_id: ID del motoboy
        mode: MODE de ejecución (1=prod, 2=staging, 3=eval)

    Returns:
        str: Desafíos activos en formato legible

    Example:
        >>> await obtener_desafios(12345)
    """
    try:
        result = await DesafioService.get_by_id_motoboy(motoboy_id, mode)

        if not result["success"] or not result["data"]:
            return "No hay desafíos activos en este momento."

        desafios_response = result["data"]
        desafios = desafios_response.desafios

        if not desafios:
            return "No hay desafíos activos en este momento."

        # Format desafios for display
        output = f"**Desafíos Activos ({len(desafios)})**\n\n"

        for i, desafio in enumerate(desafios, 1):
            output += f"**{i}. {desafio.nombre_desafio}**\n"
            output += f"   Tipo: {desafio.nombre_tipo}\n"

            if desafio.descripcion:
                output += f"   Descripción: {desafio.descripcion}\n"

            if desafio.fecha_inicio and desafio.fecha_fin:
                output += f"   Período: {desafio.fecha_inicio.strftime('%d/%m/%Y')} - {desafio.fecha_fin.strftime('%d/%m/%Y')}\n"

            if desafio.viajes_realizados is not None:
                output += f"   Viajes realizados: {desafio.viajes_realizados}\n"

            if desafio.monto_ganado_al_momento is not None:
                output += f"   Ganancia actual: ${desafio.monto_ganado_al_momento:.2f}\n"

            if desafio.detalles:
                output += "   Niveles de premio:\n"
                for detalle in desafio.detalles:
                    output += f"     • {detalle.cantidad_viajes} viajes → ${detalle.monto_premio:.2f}\n"

            output += "\n"

        return output.strip()

    except Exception as e:
        logger.error(f"Error en obtener_desafios: {e}")
        return f"Error al obtener desafíos: {str(e)}"
