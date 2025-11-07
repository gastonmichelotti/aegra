"""Modelo de datos para Motoboy"""

from pydantic import BaseModel, Field
from typing import Optional


class MotoboyModel(BaseModel):
    """Modelo de datos para motoboy - solo estructura"""
    id_motoboy: int = Field(..., description="ID del motoboy")
    nombre_completo: Optional[str] = Field(None, description="Nombre completo del motoboy")
    id_vehiculo: Optional[int] = Field(None, description="ID del vehiculo del motoboy")
    nombre_vehiculo: Optional[str] = Field(None, description="Nombre del vehiculo del motoboy")
    id_condicion_iva: Optional[int] = Field(None, description="ID de la condicion IVA del motoboy")
    nombre_condicion_iva: Optional[str] = Field(None, description="Nombre de la condicion IVA del motoboy")
    cuit: Optional[str] = Field(None, description="CUIT del motoboy", max_length=11)
    cbu: Optional[str] = Field(None, description="CBU del motoboy", max_length=22)
    latitud_motoboy: Optional[float] = Field(None, description="Latitud del motoboy")
    longitud_motoboy: Optional[float] = Field(None, description="Longitud del motoboy")
    modalidad_rapiboy: Optional[str] = Field(None, description="Modalidades de Rapiboy del motoboy")
    message: Optional[str] = Field(None, description="Mensaje de la respuesta")
