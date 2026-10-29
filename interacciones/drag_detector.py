# -*- coding: utf-8 -*-
"""
drag_detector.py - Detector de gestos de arrastre
==================================================
"""

from typing import Dict, Optional, Any
from .base import InteractionDetector


class DragDetector(InteractionDetector):
    """
    Detecta gestos de ARRASTRE (drag).

    Un DRAG consiste en:
      1. DOWN en posición inicial
      2. MOVE por una distancia significativa (umbral)
      3. UP en posición final

    CARACTERÍSTICAS DETECTADAS:
      - Posición inicial y final
      - Trayectoria completa (lista de puntos)
      - Distancia total recorrida
      - Dirección principal
      - Velocidad promedio

    DIFERENCIA CON TAP:
      - TAP: DOWN + UP en el mismo lugar (movimiento mínimo)
      - DRAG: DOWN + MOVE significativo + UP
    """

    def __init__(self, screen_width: int, screen_height: int, umbral_px: float = 10.0):
        """
        Args:
            screen_width: Ancho de la pantalla
            screen_height: Alto de la pantalla
            umbral_px: Distancia mínima en píxeles para considerar que comenzó un drag
        """
        super().__init__(screen_width, screen_height)
        self.umbral_px = umbral_px
        self.drag_activo: Optional[Dict[str, Any]] = None

    def procesar_evento(self, event, tiempo_ms: float) -> Optional[Dict[str, Any]]:
        """
        Procesa eventos de drag.

        Returns:
            Dict con información:
              - tipo: "drag_start" | "drag_move" | "drag_end"
              - x_inicio, y_inicio: posición donde comenzó
              - x_actual, y_actual: posición actual
              - distancia_total: píxeles recorridos acumulados
              - trayectoria: lista de (x, y) puntos
              - input_type: "touch" | "mouse"
        """
        # TO-DO: Implementación completa en futuras versiones
        return None
