# -*- coding: utf-8 -*-
"""
patron_objetivos.py - Patrones deterministas de objetivos
==========================================================

FILOSOFÍA:
  En lugar de generar posiciones aleatorias, usamos patrones predefinidos
  que se repiten de forma determinista. Esto permite:
    - Comparar sesiones del mismo paciente a lo largo del tiempo
    - Comparar diferentes pacientes bajo las mismas condiciones
    - Mediciones científicamente válidas

SECUENCIA DE PATRONES (6 escenarios):
  1. Centro
  2. Una de las 4 esquinas (aleatorio con semilla)
  3. Centro superior O centro inferior (aleatorio con semilla)
  4. Centro lateral izquierdo O derecho (aleatorio con semilla)
  5. Esquina inferior-izquierda + superior-derecha (diagonal)
  6. Esquina superior-izquierda + inferior-derecha (diagonal inversa)

Total: 6 objetivos por ciclo
El patrón se repite infinitamente: 1,2,3,4,5,6,1,2,3,4,5,6,...
"""

import random
from typing import Tuple, List
from enum import Enum


class TipoPosicion(Enum):
    """Tipos de posiciones predefinidas"""
    CENTRO = "centro"
    ESQUINA_SUP_IZQ = "esquina_superior_izquierda"
    ESQUINA_SUP_DER = "esquina_superior_derecha"
    ESQUINA_INF_IZQ = "esquina_inferior_izquierda"
    ESQUINA_INF_DER = "esquina_inferior_derecha"
    CENTRO_SUPERIOR = "centro_superior"
    CENTRO_INFERIOR = "centro_inferior"
    CENTRO_IZQUIERDO = "centro_lateral_izquierdo"
    CENTRO_DERECHO = "centro_lateral_derecho"


class PatronObjetivos:
    """
    Generador determinista de posiciones de objetivos.

    Usa una secuencia predefinida de 6 escenarios que se repite.
    La semilla controla las elecciones aleatorias DENTRO de cada escenario.
    """

    def __init__(self, ancho: int, alto: int, margen: int = 50, semilla: int = None):
        """
        Args:
            ancho: Ancho de la pantalla
            alto: Alto de la pantalla
            margen: Margen desde los bordes para las esquinas (píxeles)
            semilla: Semilla para reproducibilidad de elecciones aleatorias
        """
        self.ancho = ancho
        self.alto = alto
        self.margen = margen

        # Inicializar generador random con semilla
        self.rng = random.Random(semilla)

        # Contador de objetivos generados (para saber en qué escenario estamos)
        self.contador = 0

        # Posiciones predefinidas
        self._calcular_posiciones_base()

    def _calcular_posiciones_base(self):
        """Calcula todas las posiciones base del patrón"""

        # CENTRO
        self.pos_centro = (self.ancho // 2, self.alto // 2)

        # ESQUINAS
        self.pos_esquina_sup_izq = (self.margen, self.margen)
        self.pos_esquina_sup_der = (self.ancho - self.margen, self.margen)
        self.pos_esquina_inf_izq = (self.margen, self.alto - self.margen)
        self.pos_esquina_inf_der = (self.ancho - self.margen, self.alto - self.margen)

        # CENTROS DE BORDES
        self.pos_centro_superior = (self.ancho // 2, self.margen)
        self.pos_centro_inferior = (self.ancho // 2, self.alto - self.margen)
        self.pos_centro_izquierdo = (self.margen, self.alto // 2)
        self.pos_centro_derecho = (self.ancho - self.margen, self.alto // 2)

    def siguiente_posicion(self) -> Tuple[int, int, str]:
        """
        Genera la siguiente posición del patrón.

        Returns:
            Tupla (x, y, descripcion)
              - x, y: coordenadas del objetivo
              - descripcion: texto descriptivo de la posición
        """
        # Determinar escenario según el contador (ciclo de 6)
        escenario = self.contador % 6

        if escenario == 0:
            # ESCENARIO 1: Centro
            pos = self.pos_centro
            desc = "centro"

        elif escenario == 1:
            # ESCENARIO 2: Una esquina aleatoria (determinista con semilla)
            esquinas = [
                (self.pos_esquina_sup_izq, "esquina_superior_izquierda"),
                (self.pos_esquina_sup_der, "esquina_superior_derecha"),
                (self.pos_esquina_inf_izq, "esquina_inferior_izquierda"),
                (self.pos_esquina_inf_der, "esquina_inferior_derecha"),
            ]
            pos, desc = self.rng.choice(esquinas)

        elif escenario == 2:
            # ESCENARIO 3: Centro superior O inferior (determinista con semilla)
            opciones = [
                (self.pos_centro_superior, "centro_superior"),
                (self.pos_centro_inferior, "centro_inferior"),
            ]
            pos, desc = self.rng.choice(opciones)

        elif escenario == 3:
            # ESCENARIO 4: Centro lateral izquierdo O derecho (determinista con semilla)
            opciones = [
                (self.pos_centro_izquierdo, "centro_lateral_izquierdo"),
                (self.pos_centro_derecho, "centro_lateral_derecho"),
            ]
            pos, desc = self.rng.choice(opciones)

        elif escenario == 4:
            # ESCENARIO 5: Diagonal (inferior-izquierda + superior-derecha)
            # Alternamos entre las dos posiciones de la diagonal
            if (self.contador // 6) % 2 == 0:
                pos = self.pos_esquina_inf_izq
                desc = "diagonal_1_inf_izq"
            else:
                pos = self.pos_esquina_sup_der
                desc = "diagonal_1_sup_der"

        else:  # escenario == 5
            # ESCENARIO 6: Diagonal inversa (superior-izquierda + inferior-derecha)
            if (self.contador // 6) % 2 == 0:
                pos = self.pos_esquina_sup_izq
                desc = "diagonal_2_sup_izq"
            else:
                pos = self.pos_esquina_inf_der
                desc = "diagonal_2_inf_der"

        self.contador += 1
        return pos[0], pos[1], desc

    def reiniciar(self):
        """Reinicia el patrón desde el principio"""
        self.contador = 0

    def obtener_escenario_actual(self) -> int:
        """Retorna el número de escenario actual (1-6)"""
        return (self.contador % 6) + 1

    def obtener_ciclo_actual(self) -> int:
        """Retorna el número de ciclo actual (cuántas veces se repitió el patrón)"""
        return self.contador // 6

    # ============================================================================
    # MODO ALTERNATIVO: PATRÓN COMPLETAMENTE FIJO (sin elecciones aleatorias)
    # ============================================================================

    def siguiente_posicion_fija(self) -> Tuple[int, int, str]:
        """
        Versión completamente determinista sin elecciones aleatorias.

        Secuencia exacta de 12 posiciones que se repite:
          1. Centro
          2. Esquina superior izquierda
          3. Centro superior
          4. Centro lateral izquierdo
          5. Esquina inferior izquierda
          6. Esquina superior derecha
          7. Centro
          8. Esquina superior derecha
          9. Centro inferior
          10. Centro lateral derecho
          11. Esquina superior izquierda
          12. Esquina inferior derecha
        """
        secuencia_fija = [
            # Ciclo 1
            (self.pos_centro, "centro"),
            (self.pos_esquina_sup_izq, "esquina_superior_izquierda"),
            (self.pos_centro_superior, "centro_superior"),
            (self.pos_centro_izquierdo, "centro_lateral_izquierdo"),
            (self.pos_esquina_inf_izq, "diagonal_1_inf_izq"),
            (self.pos_esquina_sup_der, "diagonal_2_sup_der"),

            # Ciclo 2 (variación)
            (self.pos_centro, "centro"),
            (self.pos_esquina_sup_der, "esquina_superior_derecha"),
            (self.pos_centro_inferior, "centro_inferior"),
            (self.pos_centro_derecho, "centro_lateral_derecho"),
            (self.pos_esquina_sup_izq, "diagonal_2_sup_izq"),
            (self.pos_esquina_inf_der, "diagonal_1_inf_der"),
        ]

        idx = self.contador % len(secuencia_fija)
        pos, desc = secuencia_fija[idx]

        self.contador += 1
        return pos[0], pos[1], desc

    # ============================================================================
    # VISUALIZACIÓN Y DEBUG
    # ============================================================================

    def obtener_todas_posiciones_unicas(self) -> List[Tuple[int, int, str]]:
        """
        Retorna todas las posiciones únicas que el patrón puede generar.
        Útil para visualizar el patrón completo.
        """
        return [
            (*self.pos_centro, "centro"),
            (*self.pos_esquina_sup_izq, "esquina_superior_izquierda"),
            (*self.pos_esquina_sup_der, "esquina_superior_derecha"),
            (*self.pos_esquina_inf_izq, "esquina_inferior_izquierda"),
            (*self.pos_esquina_inf_der, "esquina_inferior_derecha"),
            (*self.pos_centro_superior, "centro_superior"),
            (*self.pos_centro_inferior, "centro_inferior"),
            (*self.pos_centro_izquierdo, "centro_lateral_izquierdo"),
            (*self.pos_centro_derecho, "centro_lateral_derecho"),
        ]

    def previsualizar_secuencia(self, n_objetivos: int = 12) -> List[Tuple[int, int, str]]:
        """
        Genera una previsualización de los próximos N objetivos.

        Args:
            n_objetivos: Cuántos objetivos generar

        Returns:
            Lista de tuplas (x, y, descripcion)
        """
        # Guardar estado actual
        contador_guardado = self.contador
        rng_state_guardado = self.rng.getstate()

        # Generar secuencia
        secuencia = []
        for _ in range(n_objetivos):
            secuencia.append(self.siguiente_posicion())

        # Restaurar estado
        self.contador = contador_guardado
        self.rng.setstate(rng_state_guardado)

        return secuencia

    def __repr__(self) -> str:
        return (f"PatronObjetivos(escenario={self.obtener_escenario_actual()}, "
                f"ciclo={self.obtener_ciclo_actual()}, "
                f"contador={self.contador})")
