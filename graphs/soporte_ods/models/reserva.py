"""Modelo de datos para Reserva"""

from datetime import datetime
from pydantic import BaseModel, Field
from typing import Optional


class ReservaModel(BaseModel):
    """Modelo de datos para reserva - solo estructura"""
    id_reserva: int = Field(..., description="ID de la reserva")
    fecha_desde: datetime = Field(..., description="Fecha de inicio de la reserva")
    fecha_hasta: datetime = Field(..., description="Fecha de fin de la reserva")
    fecha_llego: datetime = Field(..., description="Fecha de llegada del motoboy")
    id_vehiculo: int = Field(..., description="ID del vehiculo")
    nombre_vehiculo: str = Field(..., description="Nombre del vehiculo")
    tiene_autoaceptacion: bool = Field(..., description="Tiene autoaceptacion")
    repartidor_disponible: bool = Field(..., description="Repartidor disponible")
    cantidad_viajes_entregados: int = Field(..., description="Cantidad de viajes entregados")
    cantidad_rechazos: int = Field(..., description="Cantidad de rechazos")
    cantidad_rechazos_maxima: Optional[int] = Field(None, description="Cantidad de rechazos máxima")
    cantidad_viajes_minimo_asegurado: Optional[int] = Field(None, description="Cantidad de viajes mínimo asegurado")
    cumple_condicion_minimo_viajes: bool = Field(..., description="Cumple condición de mínimo de viajes")
    cumple_condicion_cantidad_rechazos: bool = Field(..., description="Cumple condición de cantidad de rechazos")
    cumple_condicion_puntualidad: bool = Field(..., description="Cumple condición de puntualidad")
    minutos_no_disponible: int = Field(..., description="Minutos no disponibles")
    cantidad_maxima_minutos_no_conectado: Optional[float] = Field(None, description="Cantidad máxima de minutos no conectado")
    cumple_condicion_conexion: bool = Field(..., description="Cumple condición de conexión")
    ganancia_minima_asegurada_correspondiente: int = Field(..., description="Ganancia mínima asegurada correspondiente")
    message: Optional[str] = Field(None, description="Mensaje de la respuesta")
