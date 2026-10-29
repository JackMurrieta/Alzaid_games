# -*- coding: utf-8 -*-
"""
objetivo.py - Entidad Objetivo (círculo target)
================================================
"""

from dataclasses import dataclass


@dataclass
class Objetivo:
    """
    Representa un objetivo (círculo) que el usuario debe tocar.

    RESPONSABILIDADES:
      - Almacenar posición y tamaño del objetivo
      - Tener un ID único para tracking
      - Proveer información para validación de acierto
    """

    id: int
    x: int
    y: int
    radio: int
    timestamp_aparicion_ms: float

    def to_dict(self) -> dict:
        """Convierte a formato JSONL"""
        return {
            "i": self.id,
            "x": self.x,
            "y": self.y,
            "r": self.radio,
        }

    def __repr__(self) -> str:
        return f"Objetivo(id={self.id}, pos=({self.x}, {self.y}), r={self.radio})"
