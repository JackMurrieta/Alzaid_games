# -*- coding: utf-8 -*-
"""
ronda.py - Entidad Ronda
=========================
"""

from dataclasses import dataclass, field
from typing import Optional
from .tap import Tap


@dataclass
class Ronda:
    """
    Representa una ronda completa del juego TAP.

    Una ronda va desde que el usuario presiona "Inicio" hasta
    que completa todos los objetivos.

    RESPONSABILIDADES:
      - Trackear score y número de ronda
      - Almacenar todos los taps de la ronda
      - Calcular métricas de la ronda
    """

    numero: int
    max_score: int
    tiempo_inicio_ms: Optional[float] = None
    tiempo_fin_ms: Optional[float] = None

    # Estado
    score: int = 0
    total_taps: int = 0  # Incluye aciertos y fallos
    taps: list[Tap] = field(default_factory=list)

    @property
    def esta_activa(self) -> bool:
        """Retorna True si la ronda está en progreso"""
        return self.tiempo_inicio_ms is not None and self.tiempo_fin_ms is None

    @property
    def esta_completa(self) -> bool:
        """Retorna True si la ronda terminó"""
        return self.score >= self.max_score

    @property
    def duracion_ms(self) -> Optional[float]:
        """Retorna la duración de la ronda en milisegundos"""
        if self.tiempo_inicio_ms is None or self.tiempo_fin_ms is None:
            return None
        return self.tiempo_fin_ms - self.tiempo_inicio_ms

    def iniciar(self, tiempo_ms: float):
        """Inicia la ronda"""
        self.tiempo_inicio_ms = tiempo_ms
        self.score = 0
        self.total_taps = 0
        self.taps.clear()

    def finalizar(self, tiempo_ms: float):
        """Finaliza la ronda"""
        self.tiempo_fin_ms = tiempo_ms

    def registrar_tap(self, tap: Tap):
        """Registra un tap en la ronda"""
        self.taps.append(tap)
        self.total_taps += 1
        if tap.acerto:
            self.score += 1

    @property
    def fallos(self) -> int:
        """Retorna el número de fallos"""
        return self.total_taps - self.score

    @property
    def tasa_acierto(self) -> float:
        """Retorna la tasa de acierto (0.0 - 1.0)"""
        if self.total_taps == 0:
            return 0.0
        return self.score / self.total_taps

    def to_dict(self) -> dict:
        """Convierte a formato JSONL"""
        return {
            "ronda": self.numero,
            "score": self.score,
            "taps": self.total_taps,
            "duracion_ms": round(self.duracion_ms, 1) if self.duracion_ms else None,
        }

    def __repr__(self) -> str:
        estado = "activa" if self.esta_activa else ("completa" if self.esta_completa else "pendiente")
        return f"Ronda(#{self.numero}, {self.score}/{self.max_score}, {estado})"
