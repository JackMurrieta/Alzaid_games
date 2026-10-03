# -*- coding: utf-8 -*-
"""
tap_actividad - Actividad TAP con Arquitectura MVC
===================================================

Estructura:
  - models/       : Entidades de dominio (Tap, Objetivo, Ronda, Configuracion)
  - controller.py : Logica de negocio
  - views/        : Vista Pygame
  - main.py       : Punto de entrada

Ejecutar:
    python -m actividades.tap_actividad.main
"""

from .models import Configuracion, Tap, Objetivo, Ronda, PatronObjetivos
from .controller import TapController
from .views import PygameView

__all__ = [
    "Configuracion",
    "Tap",
    "Objetivo",
    "Ronda",
    "PatronObjetivos",
    "TapController",
    "PygameView",
]

__version__ = "1.0.0"
__author__ = "Alzaid Games"
