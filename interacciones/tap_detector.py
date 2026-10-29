# -*- coding: utf-8 -*-
"""
tap_detector.py - Detector de interacciones TAP
================================================
"""

import pygame
from typing import Dict, Optional, Any
from .base import InteractionDetector


class TapDetector(InteractionDetector):
    """
    Detecta interacciones de tipo TAP (toque simple).

    Un TAP consiste en:
      1. DOWN: Usuario presiona (dedo o mouse)
      2. (podria implementarse????) Micro-movimientos durante el toque
      3. UP: Usuario suelta

    CARACTERISTICAS DETECTADAS:
      - Posicion (x, y)
      - Tipo de input (touch vs mouse)
      - Duracion (DOWN o UP)
      - Multi-touch (cuantos dedos simultaneos)
      - Presion (si hardware lo soporta)
      - Finger ID (para distinguir multiples dedos)

    ESTADO INTERNO:
      Mantiene un diccionario de toques activos para poder calcular
      duracion cuando se suelta.
    """

    def __init__(self, screen_width: int, screen_height: int):
        super().__init__(screen_width, screen_height)

        # Estado de toques activos
        # Estructura: {finger_id: {"t_inicio": ms, "x": x, "y": y, "input_type": "touch"}}
        # Para mouse usamos la clave "mouse" en vez de finger_id
        self.toques_activos: Dict[Any, Dict[str, Any]] = {}

    def procesar_evento(self, event, tiempo_ms: float) -> Optional[Dict[str, Any]]:

        # ======================= EVENTOS TACTILES =======================
        if event.type == pygame.FINGERDOWN:
            return self._procesar_finger_down(event, tiempo_ms)

        elif event.type == pygame.FINGERUP:
            return self._procesar_finger_up(event, tiempo_ms)

        elif event.type == pygame.FINGERMOTION:
            return self._procesar_finger_motion(event, tiempo_ms)

        # ======================= EVENTOS MOUSE =======================
        elif event.type == pygame.MOUSEBUTTONDOWN:
            return self._procesar_mouse_down(event, tiempo_ms)

        elif event.type == pygame.MOUSEBUTTONUP:
            return self._procesar_mouse_up(event, tiempo_ms)

        elif event.type == pygame.MOUSEMOTION:
            return self._procesar_mouse_motion(event, tiempo_ms)

        return None

    # METODOS PRIVADOS SI ES TACTIL EL EVNTO

    def _procesar_finger_down(self, event, tiempo_ms: float) -> Dict[str, Any]:
        """Procesa evento FINGERDOWN"""
        x_px, y_px = self._normalizar_coordenadas_touch(event)

        self.toques_activos[event.finger_id] = {
            "t_inicio": tiempo_ms,
            "x": x_px,
            "y": y_px,
            "input_type": "touch"
        }

        pressure = self._extraer_presion(event)

        return {
            "tipo": "down",
            "x": x_px,
            "y": y_px,
            "input_type": "touch",
            "finger_id": event.finger_id,
            "pressure": pressure,
            "n_dedos": len(self.toques_activos),
            "timestamp_ms": tiempo_ms
        }

    def _procesar_finger_up(self, event, tiempo_ms: float) -> Optional[Dict[str, Any]]:
        """Procesa evento FINGERUP"""
        x_px, y_px = self._normalizar_coordenadas_touch(event)

        # Calcular duraci�n si el toque estaba registrado
        duracion_ms = None
        if event.finger_id in self.toques_activos:
            info_down = self.toques_activos.pop(event.finger_id)
            duracion_ms = tiempo_ms - info_down["t_inicio"]

        return {
            "tipo": "up",
            "x": x_px,
            "y": y_px,
            "input_type": "touch",
            "finger_id": event.finger_id,
            "duracion_ms": duracion_ms,
            "timestamp_ms": tiempo_ms
        }

    def _procesar_finger_motion(self, event, tiempo_ms: float) -> Dict[str, Any]:
        """Procesa evento FINGERMOTION"""
        x_px, y_px = self._normalizar_coordenadas_touch(event)

        return {
            "tipo": "move",
            "x": x_px,
            "y": y_px,
            "input_type": "touch",
            "finger_id": event.finger_id,
            "timestamp_ms": tiempo_ms
        }

    # METODOS PRIVADOS - MOUSE

    def _procesar_mouse_down(self, event, tiempo_ms: float) -> Dict[str, Any]:
        """Procesa evento MOUSEBUTTONDOWN"""
        x, y = event.pos

        # Registrar toque activo (usando clave "mouse")
        self.toques_activos["mouse"] = {
            "t_inicio": tiempo_ms,
            "x": x,
            "y": y,
            "input_type": "mouse"
        }

        return {
            "tipo": "down",
            "x": x,
            "y": y,
            "input_type": "mouse",
            "finger_id": None,
            "pressure": None,
            "n_dedos": 1,
            "timestamp_ms": tiempo_ms
        }

    def _procesar_mouse_up(self, event, tiempo_ms: float) -> Optional[Dict[str, Any]]:
        """Procesa evento MOUSEBUTTONUP"""
        x, y = event.pos

        # Calcular duracion si el click estaba registrado
        duracion_ms = None
        if "mouse" in self.toques_activos:
            info_down = self.toques_activos.pop("mouse")
            duracion_ms = tiempo_ms - info_down["t_inicio"]

        return {
            "tipo": "up",
            "x": x,
            "y": y,
            "input_type": "mouse",
            "finger_id": None,
            "duracion_ms": duracion_ms,
            "timestamp_ms": tiempo_ms
        }

    def _procesar_mouse_motion(self, event, tiempo_ms: float) -> Optional[Dict[str, Any]]:

        if any(info["input_type"] == "touch" for info in self.toques_activos.values()):
            return None

        x, y = event.pos

        return {
            "tipo": "move",
            "x": x,
            "y": y,
            "input_type": "mouse",
            "finger_id": None,
            "timestamp_ms": tiempo_ms
        }

    # ----------------------------------------------------------------
    # M�TODOS P�BLICOS - UTILIDADES
    # ----------------------------------------------------------------

    def limpiar_toques(self):
        """
        Limpia todos los toques activos.
        util para resetear el estado entre rondas.
        """
        self.toques_activos.clear()

    def hay_toques_activos(self) -> bool:
        """Retorna True si hay toques actualmente presionados"""
        return len(self.toques_activos) > 0

    def contar_dedos_activos(self) -> int:
        """Retorna el numero de dedos actualmente tocando la pantalla"""
        return sum(1 for info in self.toques_activos.values() if info["input_type"] == "touch")
