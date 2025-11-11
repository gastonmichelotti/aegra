"""Handler Tools - Tools for escalating to human support"""

import logging
from typing import Optional
from langgraph.prebuilt import InjectedState

logger = logging.getLogger(__name__)


async def derive_to_human(
    motivo: str,
    state: InjectedState,
) -> str:
    """Derivar la conversación a soporte humano

    Usar esta tool cuando:
    - El usuario solicita explícitamente hablar con un humano
    - La consulta está fuera del alcance del bot
    - Se requiere intervención manual
    - Hay un problema que no se puede resolver automáticamente

    Args:
        motivo: Razón por la que se deriva a humano
        state: Graph state (auto-injected by LangGraph)

    Returns:
        str: Mensaje confirmando la derivación

    Example:
        >>> await derive_to_human("Usuario solicita información que no está en la documentación")
    """
    # TODO: Implement actual escalation logic
    # This should:
    # 1. Mark the thread/session for human takeover
    # 2. Log the escalation reason
    # 3. Notify the support team
    # 4. Potentially pause the bot until human takes over

    logger.info(f"Derivando a humano - Motivo: {motivo}")

    # Get thread_id from state if available
    thread_id = "unknown"
    if state:
        # Extract thread_id from config if available
        # In Aegra, this will be in config["configurable"]["thread_id"]
        pass

    logger.warning("derive_to_human not yet fully implemented")

    return f"""
    ✅ He derivado tu consulta a un agente humano.

    Motivo: {motivo}

    Un miembro de nuestro equipo de soporte se pondrá en contacto contigo a la brevedad.

    ⚠️  TODO: Implementar lógica de escalación real:
    - Marcar thread para takeover humano
    - Notificar al equipo de soporte
    - Registrar motivo de escalación
    - Thread ID: {thread_id}
    """
