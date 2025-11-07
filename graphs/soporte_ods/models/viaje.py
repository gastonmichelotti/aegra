"""Modelo de datos para Viaje"""

from datetime import datetime
from pydantic import BaseModel, Field
from typing import Optional


class ViajeModel(BaseModel):
    """Modelo de datos para viaje - solo estructura"""
    id_viaje: int = Field(..., description="ID del viaje")
    id_reserva: int = Field(..., description="ID de la reserva")
    id_motoboy: int = Field(..., description="ID del motoboy")
    direccion_origen: Optional[str] = Field(None, description="Direccion de origen")
    direccion_destino: Optional[str] = Field(None, description="Direccion de destino")
    latitud_origen: Optional[float] = Field(None, description="Latitud de origen")
    longitud_origen: Optional[float] = Field(None, description="Longitud de origen")
    latitud_destino: Optional[float] = Field(None, description="Latitud de destino")
    longitud_destino: Optional[float] = Field(None, description="Longitud de destino")
    distancia_pickeo: Optional[float] = Field(None, description="Distancia de pickeo")
    distancia_entrega: Optional[float] = Field(None, description="Distancia de entrega")
    id_estado: Optional[int] = Field(None, description="ID del estado")
    nombre_estado: Optional[str] = Field(None, description="Nombre del estado")
    fecha_asignacion_reserva: Optional[datetime] = Field(None, description="Fecha de asignacion de la reserva")
    fecha_llegada_local: Optional[datetime] = Field(None, description="Fecha de llegada local")
    fecha_salida_local: Optional[datetime] = Field(None, description="Fecha de salida local")
    fecha_llegada_cliente: Optional[datetime] = Field(None, description="Fecha de llegada cliente")
    fecha_entregado: Optional[datetime] = Field(None, description="Fecha de entregado")
    fecha_llegada_local_estimada: Optional[datetime] = Field(None, description="Fecha de llegada local estimada")
    fecha_salida_local_estimada: Optional[datetime] = Field(None, description="Fecha de salida local estimada")
    fecha_llegada_cliente_estimada: Optional[datetime] = Field(None, description="Fecha de llegada cliente estimada")
    fecha_entregado_estimada: Optional[datetime] = Field(None, description="Fecha de entregado estimada")
    message: Optional[str] = Field(None, description="Mensaje de la respuesta")
