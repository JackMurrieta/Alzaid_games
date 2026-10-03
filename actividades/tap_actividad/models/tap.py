# -*- coding: utf-8 -*-
"""
tap.py - Entidad de dominio Tap
================================

Un TAP es la unidad básica de interacción en esta actividad.
Consiste en:
  - EventoPresionar (DOWN): Cuando el usuario toca/clickea
  - EventoSoltar (UP): Cuando el usuario suelta

REGLAS DE NEGOCIO:
  - Un tap está "completo" solo si tiene presionar Y soltar
  - La duración se calcula como: soltar.timestamp - presionar.timestamp
  - Un tap puede clasificarse como: rápido, normal, prolongado
"""

from dataclasses import dataclass
from typing import Optional
import math


@dataclass
class EventoPresionar:
    """
    Representa el momento en que el usuario presiona (DOWN).

    Este evento marca el INICIO de un tap.
    """

    x: int
    y: int
    timestamp_ms: float
    input_type: str  # "touch" | "mouse"
    finger_id: Optional[int]
    pressure: Optional[float]
    n_dedos: int


@dataclass
class EventoSoltar:
    """
    Representa el momento en que el usuario suelta (UP).

    Este evento marca el FIN de un tap.
    """

    x: int
    y: int
    timestamp_ms: float
    duracion_ms: float
    input_type: str
    finger_id: Optional[int]


class Tap:
    """
    Entidad de dominio que representa un TAP completo.

    Un TAP es una interacción completa: presionar → soltar

    RESPONSABILIDADES:
      - Almacenar información de presionar y soltar
      - Calcular si acertó al objetivo (regla de negocio)
      - Clasificar el tipo de tap (rápido/normal/prolongado)
      - Validar que el tap esté completo

    NO ES RESPONSABLE DE:
      - Registrar eventos en JSONL (eso lo hace el Controller)
      - Dibujar en pantalla (eso lo hace la Vista)
    """

    def __init__(self, evento_down: dict, objetivo_x: int, objetivo_y: int, objetivo_radio: int, objetivo_id: int = 0):
        """
        Crea un nuevo Tap a partir de un evento DOWN.

        Args:
            evento_down: Diccionario retornado por TapDetector con info del DOWN
            objetivo_x: Posición X del objetivo
            objetivo_y: Posición Y del objetivo
            objetivo_radio: Radio del objetivo
            objetivo_id: ID del objetivo (para tracking)
        """

        # Crear evento presionar
        self.presionar = EventoPresionar(
            x=evento_down["x"],
            y=evento_down["y"],
            timestamp_ms=evento_down["timestamp_ms"],
            input_type=evento_down["input_type"],
            finger_id=evento_down.get("finger_id"),
            pressure=evento_down.get("pressure"),
            n_dedos=evento_down.get("n_dedos", 1)
        )

        self.soltar: Optional[EventoSoltar] = None

        # Información del objetivo
        self.objetivo_x = objetivo_x
        self.objetivo_y = objetivo_y
        self.objetivo_radio = objetivo_radio
        self.objetivo_id = objetivo_id

        # Métricas calculadas (REGLAS DE NEGOCIO)
        self.distancia_al_objetivo = self._calcular_distancia()
        self.acerto = self.distancia_al_objetivo < objetivo_radio

    def _calcular_distancia(self) -> float:
        """Calcula distancia euclidiana al objetivo"""
        return math.hypot(
            self.presionar.x - self.objetivo_x,
            self.presionar.y - self.objetivo_y
        )

    def completar_con_soltar(self, evento_up: dict):
        """
        Completa el tap con el evento UP.

        Args:
            evento_up: Diccionario retornado por TapDetector con info del UP
        """
        self.soltar = EventoSoltar(
            x=evento_up["x"],
            y=evento_up["y"],
            timestamp_ms=evento_up["timestamp_ms"],
            duracion_ms=evento_up.get("duracion_ms", 0),
            input_type=evento_up["input_type"],
            finger_id=evento_up.get("finger_id")
        )

    @property
    def esta_completo(self) -> bool:
        """Retorna True si el tap tiene presionar Y soltar"""
        return self.soltar is not None

    @property
    def duracion_ms(self) -> Optional[float]:
        """Retorna la duración del tap en milisegundos"""
        if not self.esta_completo:
            return None
        return self.soltar.duracion_ms

    # ============================================================================
    # CLASIFICACIÓN POR DURACIÓN (REGLAS DE NEGOCIO)
    # ============================================================================

    def es_tap_rapido(self) -> bool:
        """
        Regla de negocio: tap < 100ms = rápido

        Indica: respuesta impulsiva, buena velocidad motora
        """
        if not self.esta_completo:
            return False
        return self.duracion_ms < 100

    def es_tap_normal(self) -> bool:
        """
        Regla de negocio: 100ms <= tap <= 500ms = normal

        Indica: respuesta controlada normal
        """
        if not self.esta_completo:
            return False
        return 100 <= self.duracion_ms <= 500

    def es_tap_prolongado(self) -> bool:
        """
        Regla de negocio: tap > 500ms = prolongado

        Indica: posible dificultad para liberar, vacilación
        """
        if not self.esta_completo:
            return False
        return self.duracion_ms > 500

    def clasificacion_duracion(self) -> str:
        """Retorna clasificación textual del tap"""
        if not self.esta_completo:
            return "incompleto"
        if self.es_tap_rapido():
            return "rapido"
        elif self.es_tap_normal():
            return "normal"
        else:
            return "prolongado"

    # ============================================================================
    # MULTI-TOUCH (REGLAS DE NEGOCIO)
    # ============================================================================

    def es_multitouch_involuntario(self) -> bool:
        """
        Regla de negocio: Más de 1 dedo = multitouch involuntario

        Indica: posible falta de control motor fino
        """
        return self.presionar.n_dedos > 1

    # ============================================================================
    # CONVERSIÓN A JSONL
    # ============================================================================

    def to_dict_presionar(self) -> dict:
        """Convierte el evento DOWN a formato JSONL"""
        return {
            "x": self.presionar.x,
            "y": self.presionar.y,
            "hit": self.acerto,
            "target": self.objetivo_id,
            "dist": round(self.distancia_al_objetivo, 1),
            "input_type": self.presionar.input_type,
            "finger_id": self.presionar.finger_id,
            "pressure": self.presionar.pressure,
            "n_dedos": self.presionar.n_dedos,
        }

    def to_dict_soltar(self) -> Optional[dict]:
        """Convierte el evento UP a formato JSONL"""
        if not self.esta_completo:
            return None

        return {
            "x": self.soltar.x,
            "y": self.soltar.y,
            "finger_id": self.soltar.finger_id,
            "duracion_ms": self.soltar.duracion_ms,
            "input_type": self.soltar.input_type,
        }

    def __repr__(self) -> str:
        estado = "completo" if self.esta_completo else "incompleto"
        acerto_str = "ACIERTO" if self.acerto else "FALLO"
        duracion_str = f"{self.duracion_ms:.1f}ms" if self.esta_completo else "N/A"
        return f"Tap({acerto_str}, {duracion_str}, {estado})"
