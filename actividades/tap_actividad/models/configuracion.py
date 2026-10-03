# -*- coding: utf-8 -*-
"""
configuracion.py - Configuración de la actividad TAP
=====================================================
"""

from dataclasses import dataclass
from typing import Optional


@dataclass
class Configuracion:
    """
    Configuración de la actividad TAP.

    Contiene todos los parámetros configurables de la actividad,
    incluyendo la semilla para reproducibilidad.
    """

    # Semilla para reproducibilidad
    semilla: Optional[int] = 20260101

    # Configuración de pantalla
    ancho_pantalla: int = 1500
    alto_pantalla: int = 800

    # Configuración del juego
    max_score: int = 5
    radio_objetivo: int = 50

    # Configuración visual
    color_fondo: tuple[int, int, int] = (169, 169, 169)  # Gris
    color_objetivo: tuple[int, int, int] = (100, 149, 237)  # Azul cornflower
    color_boton_inicio: tuple[int, int, int] = (0, 255, 120)  # Verde
    color_texto: tuple[int, int, int] = (0, 0, 0)  # Negro

    # Configuración de grabación
    grabar_video: bool = False
    guardar_csv: bool = False
    grabar_replay: bool = True

    # Participante
    participante: str = ""

    def __post_init__(self):
        """Validaciones después de inicialización"""
        if self.max_score <= 0:
            raise ValueError("max_score debe ser mayor a 0")
        if self.radio_objetivo <= 0:
            raise ValueError("radio_objetivo debe ser mayor a 0")
        if self.ancho_pantalla <= 0 or self.alto_pantalla <= 0:
            raise ValueError("Dimensiones de pantalla deben ser mayores a 0")

    def to_dict(self) -> dict:
        """Convierte a diccionario para replay JSONL"""
        return {
            "max_score": self.max_score,
            "circle_radius": self.radio_objetivo,
            "semilla": self.semilla,
        }
