# -*- coding: utf-8 -*-
"""
zoom_detector.py - Detector de gestos de pinch-zoom
====================================================
"""

from typing import Dict, Optional, Any
from .base import InteractionDetector


class ZoomDetector(InteractionDetector):
    """
    Detecta gestos de PINCH-ZOOM (dos dedos).

    Un PINCH consiste en:
      1. Dos dedos tocan simult�neamente
      2. Se mueven acerc�ndose (zoom out) o alej�ndose (zoom in)
      3. Se sueltan

    CARACTER�STICAS DETECTADAS:
      - Distancia inicial entre dedos
      - Distancia actual
      - Factor de escala (scale = dist_actual / dist_inicial)
      - Centro del pinch (punto medio entre dedos)

    SOLO FUNCIONA EN PANTALLAS T�CTILES con multi-touch.
    """

    def __init__(self, screen_width: int, screen_height: int):
        super().__init__(screen_width, screen_height)

        # Estado del pinch actual
        self.pinch_activo: Optional[Dict[str, Any]] = None

    def procesar_evento(self, event, tiempo_ms: float) -> Optional[Dict[str, Any]]:
        """
        Procesa eventos de pinch-zoom.

        Returns:
            Dict con informaci�n:
              - tipo: "pinch_start" | "pinch_move" | "pinch_end"
              - scale: factor de escala (1.0 = sin cambio, >1 = zoom in, <1 = zoom out)
              - center_x, center_y: punto medio entre dedos
              - distancia: p�xeles entre dedos
        """
        # TO-DO: Implementaci�n completa en futuras versiones
        return None
