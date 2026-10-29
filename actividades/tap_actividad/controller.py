# -*- coding: utf-8 -*-
"""
controller.py - Controlador de la actividad TAP (MVC)
======================================================

El controlador coordina el flujo de la actividad:
  - Gestiona el estado del juego
  - Procesa eventos de interacción
  - Aplica reglas de negocio
  - Registra en JSONL
  - Notifica a la vista para actualizar

NO maneja:
  - Rendering (eso es responsabilidad de la Vista)
  - Detección raw de eventos (eso es responsabilidad de TapDetector)
"""

import random
from typing import Optional
from .models import Configuracion, Tap, Objetivo, Ronda
from .models.patron_objetivos import PatronObjetivos


class TapController:
    """
    Controlador principal de la actividad TAP.

    Implementa el patrón MVC como intermediario entre:
      - Modelo (entidades de dominio)
      - Vista (Pygame)
      - Servicios externos (TapDetector, Recorder)
    """

    def __init__(self, configuracion: Configuracion, recorder=None):
        """
        Args:
            configuracion: Configuración de la actividad
            recorder: Instancia de Recorder para grabar JSONL (opcional)
        """
        self.config = configuracion
        self.recorder = recorder

        # Inicializar generador de patrones con semilla
        self.patron = PatronObjetivos(
            ancho=configuracion.ancho_pantalla,
            alto=configuracion.alto_pantalla,
            margen=configuracion.radio_objetivo,
            semilla=configuracion.semilla
        )

        # Estado del juego
        self.objetivo_actual: Optional[Objetivo] = None
        self.tap_en_progreso: Optional[Tap] = None
        self.ronda_actual: Optional[Ronda] = None
        self.rondas_completadas: list[Ronda] = []

        # Contadores
        self.n_objetivo = 0  # Índice incremental de objetivos
        self.n_ronda = 1

        # Estado UI
        self.juego_terminado = False
        self.esperando_inicio = True

        # Generar primer objetivo
        self.objetivo_actual = self._generar_nuevo_objetivo()

    def _generar_nuevo_objetivo(self) -> Objetivo:
        """
        Genera un nuevo objetivo usando el patrón determinista.

        NOTA: Ya no usa posiciones aleatorias. Usa PatronObjetivos para
        generar secuencias reproducibles y comparables científicamente.
        """
        # Obtener siguiente posición del patrón
        x, y, descripcion = self.patron.siguiente_posicion()

        objetivo = Objetivo(
            id=self.n_objetivo,
            x=x,
            y=y,
            radio=self.config.radio_objetivo,
            timestamp_aparicion_ms=self.ms()
        )

        # Registrar en JSONL (ahora incluye la descripción del patrón)
        if self.recorder:
            self.recorder.event(
                "target",
                i=objetivo.id,
                x=objetivo.x,
                y=objetivo.y,
                r=objetivo.radio,
                patron=descripcion,  # NUEVO: identifica el tipo de posición
                escenario=self.patron.obtener_escenario_actual(),
                ciclo=self.patron.obtener_ciclo_actual()
            )

        self.n_objetivo += 1
        return objetivo

    def ms(self) -> float:
        """Retorna timestamp actual en milisegundos (delegado al recorder)"""
        if self.recorder:
            return self.recorder.ms()
        return 0.0

    # ============================================================================
    # ACCIONES DEL USUARIO
    # ============================================================================

    def iniciar_ronda(self):
        """Inicia una nueva ronda"""
        self.esperando_inicio = False
        self.ronda_actual = Ronda(numero=self.n_ronda, max_score=self.config.max_score)
        self.ronda_actual.iniciar(self.ms())

        # Registrar en JSONL
        if self.recorder:
            self.recorder.event("round_start", ronda=self.n_ronda)

    def procesar_tap_down(self, info_down: dict):
        """
        Procesa un evento DOWN (presionar).

        Args:
            info_down: Información del tap retornada por TapDetector
        """
        if self.objetivo_actual is None:
            return

        # Crear objeto Tap (entidad de dominio)
        self.tap_en_progreso = Tap(
            evento_down=info_down,
            objetivo_x=self.objetivo_actual.x,
            objetivo_y=self.objetivo_actual.y,
            objetivo_radio=self.objetivo_actual.radio,
            objetivo_id=self.objetivo_actual.id
        )

        # Registrar evento DOWN en JSONL
        if self.recorder:
            self.recorder.event("down", **self.tap_en_progreso.to_dict_presionar())

        # Aplicar reglas de negocio
        if self.tap_en_progreso.acerto and self.ronda_actual:
            self.ronda_actual.registrar_tap(self.tap_en_progreso)

            # Generar nuevo objetivo
            self.objetivo_actual = self._generar_nuevo_objetivo()

            # Verificar si completó la ronda
            if self.ronda_actual.esta_completa:
                self._finalizar_ronda()

    def procesar_tap_up(self, info_up: dict):
        """
        Procesa un evento UP (soltar).

        Args:
            info_up: Información del tap retornada por TapDetector
        """
        if self.tap_en_progreso:
            # Completar el tap
            self.tap_en_progreso.completar_con_soltar(info_up)

            # Registrar evento UP en JSONL
            if self.recorder:
                datos_up = self.tap_en_progreso.to_dict_soltar()
                if datos_up:
                    self.recorder.event("up", **datos_up)

            # Limpiar tap en progreso
            self.tap_en_progreso = None

    def procesar_movimiento(self, info_move: dict):
        """
        Procesa un evento MOVE.

        Args:
            info_move: Información del movimiento retornada por TapDetector
        """
        if self.recorder:
            self.recorder.move(
                info_move["x"],
                info_move["y"],
                input_type=info_move.get("input_type"),
                finger_id=info_move.get("finger_id")
            )

    def reiniciar_juego(self):
        """Reinicia el juego para una nueva ronda"""
        self.juego_terminado = False
        self.esperando_inicio = True
        self.tap_en_progreso = None

        if self.recorder:
            self.recorder.event("restart", ronda=self.n_ronda)

    def _finalizar_ronda(self):
        """Finaliza la ronda actual"""
        if self.ronda_actual:
            self.ronda_actual.finalizar(self.ms())

            # Registrar en JSONL
            if self.recorder:
                self.recorder.event("round_end", **self.ronda_actual.to_dict())

            # Marcar juego como terminado
            self.juego_terminado = True

            # Guardar ronda completada
            self.rondas_completadas.append(self.ronda_actual)
            self.n_ronda += 1

    # ============================================================================
    # ESTADO DEL JUEGO (para la Vista)
    # ============================================================================

    def obtener_score(self) -> int:
        """Retorna el score actual"""
        if self.ronda_actual:
            return self.ronda_actual.score
        return 0

    def obtener_max_score(self) -> int:
        """Retorna el score máximo"""
        return self.config.max_score

    def obtener_objetivo(self) -> Optional[Objetivo]:
        """Retorna el objetivo actual"""
        return self.objetivo_actual

    def obtener_numero_ronda(self) -> int:
        """Retorna el número de ronda actual"""
        return self.n_ronda

    def obtener_total_rondas_completadas(self) -> int:
        """Retorna cuántas rondas se han completado"""
        return len(self.rondas_completadas)

    def esta_juego_terminado(self) -> bool:
        """Retorna True si el juego terminó"""
        return self.juego_terminado

    def esta_esperando_inicio(self) -> bool:
        """Retorna True si está esperando que presionen Inicio"""
        return self.esperando_inicio

    # ============================================================================
    # FINALIZACIÓN
    # ============================================================================

    def finalizar(self, motivo="completed") -> Optional[str]:
        """
        Finaliza la actividad y cierra el recorder.

        Args:
            motivo: "completed" | "quit" | "error"

        Returns:
            Ruta del archivo JSONL generado (si hay recorder)
        """
        if self.recorder:
            return self.recorder.close(
                motivo=motivo,
                rondas=len(self.rondas_completadas)
            )
        return None
