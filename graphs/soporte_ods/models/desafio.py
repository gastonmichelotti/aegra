"""Modelo de datos para Desafio"""

from datetime import datetime
from pydantic import BaseModel, Field
from typing import Optional, List


class DetalleDesafioModel(BaseModel):
    """Modelo de datos para detalle de desafio - solo estructura"""
    id_desafio: int = Field(..., description="ID del desafio")
    cantidad_viajes: int = Field(..., description="Cantidad de viajes")
    monto_premio: float = Field(..., description="Monto del premio")


class DesafioModel(BaseModel):
    """Modelo de datos para desafio - solo estructura"""
    id_desafio: Optional[int] = Field(None, description="ID del desafio")
    id_tipo: Optional[int] = Field(None, description="ID del tipo de desafio")
    nombre_tipo: Optional[str] = Field(None, description="Nombre del tipo de desafio")
    nombre_desafio: Optional[str] = Field(None, description="Nombre del desafio")
    condiciones: Optional[str] = Field(None, description="Condiciones del desafio")
    monto_ganado_al_momento: Optional[float] = Field(None, description="Monto ganado al momento")
    descripcion: Optional[str] = Field(None, description="Descripcion del desafio")
    fecha_inicio: Optional[datetime] = Field(None, description="Fecha de inicio")
    fecha_fin: Optional[datetime] = Field(None, description="Fecha de fin")
    viajes_realizados: Optional[int] = Field(None, description="Viajes realizados")
    detalles: Optional[List[DetalleDesafioModel]] = Field(None, description="Detalles del desafio")
    message: Optional[str] = Field(None, description="Mensaje de la respuesta")


class DesafioResponseModel(BaseModel):
    """Modelo de datos para respuesta de desafio"""
    desafios: List[DesafioModel] = Field(..., description="Lista de desafios")
    message: Optional[str] = Field(None, description="Mensaje de la respuesta")
