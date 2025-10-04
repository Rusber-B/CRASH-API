from pydantic import BaseModel, Field
from typing import List

# -------------------------------------------------------------------
# Texto que describe la estructura de un único asteroide.
# -------------------------------------------------------------------
class Asteroide(BaseModel):
    nombre: str = Field(..., description="El nombre oficial del asteroide.")
    diametro_promedio_km: float = Field(..., description="El diámetro promedio del asteroide en kilómetros.")

    class Config:
        orm_mode = True

# -------------------------------------------------------------------
# Texto que describe la respuesta completa y final de la API.
# -------------------------------------------------------------------
class RespuestaAsteroides(BaseModel):
    fecha_consultada: str = Field(..., description="La fecha utilizada para la consulta, en formato YYYY-MM-DD.")
    cantidad: int = Field(..., description="El número total de asteroides encontrados para esa fecha.")
    asteroides: List[Asteroide] = Field(..., description="Una lista que contiene la información de cada asteroide.")

    class Config:
        orm_mode = True