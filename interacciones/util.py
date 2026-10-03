# -*- coding: utf-8 -*-
"""
util.py - Funciones utilitarias para cálculos geométricos
==========================================================
"""

import math


def distancia_euclidiana(x1: float, y1: float, x2: float, y2: float) -> float:
    """
    Calcula la distancia euclidiana entre dos puntos.

    Args:
        x1, y1: Coordenadas del primer punto
        x2, y2: Coordenadas del segundo punto

    Returns:
        Distancia en p�xeles
    """
    return math.hypot(x2 - x1, y2 - y1)


def angulo_entre_puntos(x1: float, y1: float, x2: float, y2: float) -> float:
    """
    Calcula el �ngulo en radianes entre dos puntos.

    Args:
        x1, y1: Punto inicial
        x2, y2: Punto final

    Returns:
        �ngulo en radianes (-� a �)
    """
    return math.atan2(y2 - y1, x2 - x1)


def direccion_desde_angulo(angulo_rad: float) -> str:
    """
    Convierte un �ngulo en radianes a una direcci�n cardinal.

    Args:
        angulo_rad: �ngulo en radianes

    Returns:
        "right" | "up" | "left" | "down"
    """
    angulo_deg = math.degrees(angulo_rad)

    if -45 <= angulo_deg < 45:
        return "right"
    elif 45 <= angulo_deg < 135:
        return "down"
    elif -135 <= angulo_deg < -45:
        return "up"
    else:
        return "left"
