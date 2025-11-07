"""Tools for Soporte ODS graph"""

from .api_tools import gestionar_estado_viaje, obtener_desafios
from .rag_tools import search_instructivo_general
from .location_tools import get_motoboy_location
from .handler_tools import derive_to_human

# All tools available to the agent
TOOLS = [
    gestionar_estado_viaje,
    obtener_desafios,
    search_instructivo_general,
    get_motoboy_location,
    derive_to_human,
]

__all__ = [
    "TOOLS",
    "gestionar_estado_viaje",
    "obtener_desafios",
    "search_instructivo_general",
    "get_motoboy_location",
    "derive_to_human",
]
