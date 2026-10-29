# -*- coding: utf-8 -*-
"""
Módulo de interacciones - Detectores puros de eventos de usuario
================================================================

Este módulo provee detectores para diferentes tipos de interacciones
táctiles y de mouse en aplicaciones Pygame.

DETECTORES DISPONIBLES:
  - TapDetector: Taps/clicks simples (touch y mouse)
  - DragDetector: Gestos de arrastre (TO-DO: implementación futura)
  - ZoomDetector: Pinch-zoom con dos dedos (TO-DO: implementación futura)
  - SlideDetector: Swipes rápidos (TO-DO: implementación futura)

EJEMPLO DE USO:
    from interacciones import TapDetector

    detector = TapDetector(1500, 800)

    for event in pygame.event.get():
        info = detector.procesar_evento(event, tiempo_ms)
        if info and info["tipo"] == "down":
            print(f"Tap en ({info['x']}, {info['y']})")
"""

from .base import InteractionDetector
from .tap_detector import TapDetector
from .drag_detector import DragDetector
from .zoom_detector import ZoomDetector
from .slide_detector import SlideDetector
from .util import (
    distancia_euclidiana,
    angulo_entre_puntos,
    direccion_desde_angulo,
)

__all__ = [
    "InteractionDetector",
    "TapDetector",
    "DragDetector",
    "ZoomDetector",
    "SlideDetector",
    "distancia_euclidiana",
    "angulo_entre_puntos",
    "direccion_desde_angulo",
]

__version__ = "1.0.0"
__author__ = "Alzaid Games"
