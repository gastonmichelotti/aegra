"""Modelos de dominio para Soporte ODS"""

from .motoboy import MotoboyModel
from .viaje import ViajeModel
from .reserva import ReservaModel
from .desafio import DetalleDesafioModel, DesafioModel, DesafioResponseModel

__all__ = [
    "MotoboyModel",
    "ViajeModel",
    "ReservaModel",
    "DetalleDesafioModel",
    "DesafioModel",
    "DesafioResponseModel",
]
