# -*- coding: utf-8 -*-
"""
Modelos de dominio para la actividad TAP
=========================================
"""

from .configuracion import Configuracion
from .tap import Tap, EventoPresionar, EventoSoltar
from .objetivo import Objetivo
from .ronda import Ronda
from .patron_objetivos import PatronObjetivos

__all__ = [
    "Configuracion",
    "Tap",
    "EventoPresionar",
    "EventoSoltar",
    "Objetivo",
    "Ronda",
    "PatronObjetivos",
]
