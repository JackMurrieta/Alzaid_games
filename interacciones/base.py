# -*- coding: utf-8 -*-
"""
base.py - Clase base para detectores de interacciones
======================================================
"""

import pygame
from typing import Dict, Optional, Tuple, Any


class InteractionDetector:
    """
    Clase base para todos los detectores de interacciones.
    Provee funcionalidad común como normalización de coordenadas
    y conversión de eventos raw.
    """

    def __init__(self, screen_width: int, screen_height: int):
        """
        Args:
            screen_width: Ancho de la pantalla en píxeles
            screen_height: Alto de la pantalla en píxeles
        """
        self.screen_width = screen_width
        self.screen_height = screen_height

    def _normalizar_coordenadas_touch(self, event) -> Tuple[int, int]:
        """
        Convierte coordenadas normalizadas (0.0-1.0) de eventos táctiles
        a coordenadas de píxeles absolutas.

        Args:
            event: Evento pygame FINGER*

        Returns:
            (x_px, y_px) en coordenadas de píxeles
        """
        x_px = int(event.x * self.screen_width)
        y_px = int(event.y * self.screen_height)
        return x_px, y_px

    def _extraer_presion(self, event) -> Optional[float]:
        """
        Intenta extraer información de presión del evento táctil.

        Args:
            event: Evento pygame FINGERDOWN

        Returns:
            float entre 0.0-1.0 si disponible, None si no
        """
        return getattr(event, 'pressure', None)

    def procesar_evento(self, event, tiempo_ms: float) -> Optional[Dict[str, Any]]:
        """
        Procesa un evento de Pygame y retorna información estructurada.
        Debe ser implementado por cada detector específico.
        """
        raise NotImplementedError("Cada detector debe implementar procesar_evento()")
