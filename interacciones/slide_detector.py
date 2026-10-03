# -*- coding: utf-8 -*-
"""
slide_detector.py - Detector de gestos de deslizamiento
========================================================
"""

from typing import Dict, Optional, Any
from .base import InteractionDetector


class SlideDetector(InteractionDetector):
    """
    Detecta gestos de DESLIZAMIENTO r�pido (swipe).

    Un SWIPE consiste en:
      1. DOWN
      2. MOVE r�pido en una direcci�n principal
      3. UP

    CARACTER�STICAS DETECTADAS:
      - Direcci�n: "left", "right", "up", "down"
      - Velocidad (p�xeles/segundo)
      - Distancia recorrida

    DIFERENCIA CON DRAG:
      - DRAG: Movimiento controlado, puede ser lento
      - SWIPE: Movimiento r�pido, tiene inercia
    """

    def __init__(self, screen_width: int, screen_height: int,
                 umbral_velocidad: float = 500.0, umbral_distancia: float = 100.0):
        """
        Args:
            screen_width: Ancho de la pantalla
            screen_height: Alto de la pantalla
            umbral_velocidad: Velocidad m�nima en px/s para considerar swipe
            umbral_distancia: Distancia m�nima en px para considerar swipe
        """
        super().__init__(screen_width, screen_height)
        self.umbral_velocidad = umbral_velocidad
        self.umbral_distancia = umbral_distancia

        # Estado del swipe
        self.swipe_activo: Optional[Dict[str, Any]] = None

    def procesar_evento(self, event, tiempo_ms: float) -> Optional[Dict[str, Any]]:
        """
        Procesa eventos de swipe.

        Returns:
            Dict con informaci�n:
              - tipo: "swipe"
              - direccion: "left" | "right" | "up" | "down"
              - velocidad: p�xeles por segundo
              - distancia: p�xeles recorridos
        """
        # TO-DO: Implementaci�n completa en futuras versiones
        return None
