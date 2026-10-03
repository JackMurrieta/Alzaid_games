# -*- coding: utf-8 -*-
"""
main.py - Punto de entrada de la actividad TAP (MVC)
=====================================================

Este archivo ensambla todos los componentes:
  - MODELO: Entidades de dominio (Tap, Objetivo, Ronda, etc.)
  - VISTA: PygameView (renderizado)
  - CONTROLADOR: TapController (lógica de negocio)
  - SERVICIOS: TapDetector (interacciones), Recorder (JSONL)

Ejecutar:
    python -m actividades.tap_actividad.main
"""

import sys
import os

# Agregar path raíz del proyecto para imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from actividades.tap_actividad.models import Configuracion
from actividades.tap_actividad.controller import TapController
from actividades.tap_actividad.views import PygameView
from interacciones import TapDetector
from input_replay.replay import Recorder


def main():
    """Función principal que ensambla y ejecuta la actividad TAP"""

    # ============================================================================
    # 1. CONFIGURACIÓN
    # ============================================================================

    # Solicitar nombre del participante
    participante = input("Ingrese su nombre: ")

    # Crear configuración
    config = Configuracion(
        semilla=20260101,           # Semilla fija para reproducibilidad
        ancho_pantalla=1500,
        alto_pantalla=800,
        max_score=5,
        radio_objetivo=50,
        grabar_video=False,
        guardar_csv=False,
        grabar_replay=True,
        participante=participante
    )

    # ============================================================================
    # 2. INICIALIZAR SERVICIOS
    # ============================================================================

    # Recorder para JSONL
    recorder = Recorder(
        actividad="tap",
        participante=config.participante,
        screen=(config.ancho_pantalla, config.alto_pantalla),
        config=config.to_dict(),
        seed=config.semilla,
        activo=config.grabar_replay
    )

    # Detector de interacciones TAP
    tap_detector = TapDetector(
        screen_width=config.ancho_pantalla,
        screen_height=config.alto_pantalla
    )

    # ============================================================================
    # 3. INICIALIZAR MVC
    # ============================================================================

    # CONTROLADOR (lógica de negocio)
    controller = TapController(configuracion=config, recorder=recorder)

    # VISTA (renderizado Pygame)
    view = PygameView(configuracion=config)

    # ============================================================================
    # 4. GAME LOOP PRINCIPAL
    # ============================================================================

    print("\n" + "=" * 70)
    print("ACTIVIDAD TAP - Arquitectura MVC")
    print("=" * 70)
    print(f"Participante: {participante}")
    print(f"Semilla: {config.semilla}")
    print(f"Objetivos por ronda: {config.max_score}")
    print("=" * 70 + "\n")

    motivo_cierre = "quit"

    while view.esta_corriendo():
        # ========================================================================
        # PROCESAR EVENTOS (VISTA → CONTROLADOR)
        # ========================================================================

        eventos = view.procesar_eventos()

        for evento_info in eventos:
            tipo_evento = evento_info['tipo']

            # Evento de cierre
            if tipo_evento == 'quit':
                break

            # Botón de inicio
            elif tipo_evento == 'boton_inicio':
                if controller.esta_esperando_inicio():
                    controller.iniciar_ronda()

            # Botón de reiniciar
            elif tipo_evento == 'boton_reiniciar':
                if controller.esta_juego_terminado():
                    controller.reiniciar_juego()

            # Eventos raw para TapDetector
            elif tipo_evento == 'evento_raw':
                evento_raw = evento_info['evento']

                # Procesar con TapDetector
                info_tap = tap_detector.procesar_evento(evento_raw, recorder.ms())

                if info_tap:
                    # Delegar al Controlador según tipo de evento
                    if info_tap['tipo'] == 'down':
                        # Solo procesar DOWN si NO está en menú
                        if not controller.esta_esperando_inicio() and not controller.esta_juego_terminado():
                            # Verificar que no sea click en botones
                            x, y = info_tap['x'], info_tap['y']
                            if not view._click_en_boton_inicio(x, y) and not view._click_en_boton_reiniciar(x, y):
                                controller.procesar_tap_down(info_tap)

                    elif info_tap['tipo'] == 'up':
                        controller.procesar_tap_up(info_tap)

                    elif info_tap['tipo'] == 'move':
                        controller.procesar_movimiento(info_tap)

        # ========================================================================
        # RENDERIZAR (CONTROLADOR → VISTA)
        # ========================================================================

        view.renderizar(controller)

        # Verificar si completó todas las rondas necesarias
        if controller.esta_juego_terminado():
            motivo_cierre = "completed"

    # ============================================================================
    # 5. FINALIZACIÓN
    # ============================================================================

    print("\n" + "=" * 70)
    print("FINALIZANDO ACTIVIDAD")
    print("=" * 70)

    # Cerrar vista
    view.cerrar()

    # Cerrar recorder y obtener ruta del JSONL
    ruta_replay = controller.finalizar(motivo=motivo_cierre)

    # Mostrar resumen
    print(f"Rondas completadas: {controller.obtener_total_rondas_completadas()}")

    if ruta_replay:
        print(f"\nReplay guardado: {ruta_replay}")
        print(f"  Ver replay:   python reproductor.py {ruta_replay}")
        print(f"  Ver metricas: python metricas.py {ruta_replay}")

    print("=" * 70 + "\n")

    # Salir
    sys.exit(0)


if __name__ == "__main__":
    main()
