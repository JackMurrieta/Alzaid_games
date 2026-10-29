# -*- coding: utf-8 -*-
"""
pygame_view.py - Vista Pygame para la actividad TAP (MVC)
==========================================================

La Vista es responsable SOLO de:
  - Renderizar elementos en pantalla
  - Capturar eventos de Pygame
  - Notificar al Controlador de interacciones del usuario

NO es responsable de:
  - Lógica de negocio (eso lo hace el Controller)
  - Gestión de estado del juego (eso lo hace el Controller)
  - Registrar en JSONL (eso lo hace el Controller)
"""

import pygame
import sys
from typing import Optional


class PygameView:
    """
    Vista Pygame para la actividad TAP.

    Implementa el patrón MVC como capa de presentación.
    Se comunica con el Controller para obtener estado y notificar eventos.
    """

    def __init__(self, configuracion):
        """
        Args:
            configuracion: Instancia de Configuracion con parámetros visuales
        """
        self.config = configuracion

        # Inicializar Pygame
        pygame.init()

        # Crear ventana
        self.window = pygame.display.set_mode(
            (self.config.ancho_pantalla, self.config.alto_pantalla)
        )
        pygame.display.set_caption("Actividad TAP")

        # Reloj para controlar FPS
        self.reloj = pygame.time.Clock()

        # Fuente para texto
        self.font = pygame.font.Font(None, 36)
        self.font_grande = pygame.font.Font(None, 48)

        # Estado de la vista
        self.running = True

    # ============================================================================
    # RENDERIZADO
    # ============================================================================

    def renderizar(self, controller):
        """
        Renderiza el estado actual del juego.

        Args:
            controller: Instancia de TapController con el estado del juego
        """
        # Limpiar pantalla
        self.window.fill(self.config.color_fondo)

        # Obtener estado del controller
        objetivo = controller.obtener_objetivo()
        score = controller.obtener_score()
        max_score = controller.obtener_max_score()
        juego_terminado = controller.esta_juego_terminado()
        esperando_inicio = controller.esta_esperando_inicio()

        # Dibujar objetivo (círculo)
        if objetivo:
            self._dibujar_objetivo(objetivo)

        # Dibujar score
        self._dibujar_score(score, max_score)

        # Dibujar botón de inicio
        color_boton = self.config.color_texto if not esperando_inicio else self.config.color_boton_inicio
        self._dibujar_boton_inicio(color_boton, esperando_inicio)

        # Dibujar pantalla de fin de juego
        if juego_terminado:
            self._dibujar_pantalla_fin()

        # Actualizar display
        pygame.display.flip()

        # Controlar FPS (60 FPS para movimiento suave del cursor)
        self.reloj.tick(60)

    def _dibujar_objetivo(self, objetivo):
        """Dibuja el círculo objetivo"""
        pygame.draw.circle(
            self.window,
            self.config.color_objetivo,
            (objetivo.x, objetivo.y),
            objetivo.radio
        )

    def _dibujar_score(self, score: int, max_score: int):
        """Dibuja el puntaje actual"""
        texto_score = self.font.render(f"Aciertos: {score}/{max_score}", True, self.config.color_texto)
        self.window.blit(texto_score, (10, 10))

    def _dibujar_boton_inicio(self, color_texto, activo: bool):
        """Dibuja el botón de inicio"""
        ancho_boton = 150
        alto_boton = 50
        x_boton = self.config.ancho_pantalla - 160
        y_boton = self.config.alto_pantalla - 60

        # Fondo del botón
        color_fondo_boton = self.config.color_boton_inicio if activo else (100, 100, 100)
        pygame.draw.rect(
            self.window,
            color_fondo_boton,
            (x_boton, y_boton, ancho_boton, alto_boton)
        )

        # Texto del botón
        texto_inicio = self.font.render("Inicio", True, color_texto)
        texto_rect = texto_inicio.get_rect(center=(x_boton + ancho_boton // 2, y_boton + alto_boton // 2))
        self.window.blit(texto_inicio, texto_rect)

    def _dibujar_pantalla_fin(self):
        """Dibuja la pantalla de fin de ronda"""
        # Fondo semi-transparente (opcional, se puede omitir en Pygame básico)

        # Botón de reinicio
        ancho_boton = 150
        alto_boton = 50
        x_boton = self.config.ancho_pantalla // 2 - ancho_boton // 2
        y_boton = self.config.alto_pantalla // 2 + 20

        pygame.draw.rect(
            self.window,
            self.config.color_texto,
            (x_boton, y_boton, ancho_boton, alto_boton)
        )

        texto_reiniciar = self.font.render("Reiniciar", True, (233, 233, 233))
        texto_rect = texto_reiniciar.get_rect(center=(x_boton + ancho_boton // 2, y_boton + alto_boton // 2))
        self.window.blit(texto_reiniciar, texto_rect)

    # ============================================================================
    # MANEJO DE EVENTOS
    # ============================================================================

    def procesar_eventos(self) -> dict:
        """
        Procesa eventos de Pygame y retorna información para el Controller.

        Returns:
            dict con:
              - 'tipo': 'quit' | 'boton_inicio' | 'boton_reiniciar' | 'evento_raw'
              - 'evento': evento raw de Pygame (si aplica)
        """
        eventos_procesados = []

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
                eventos_procesados.append({'tipo': 'quit'})

            # Detectar clicks en botones (simplificado, el Controller decide)
            elif event.type == pygame.MOUSEBUTTONDOWN or event.type == pygame.FINGERDOWN:
                # Obtener posición
                if event.type == pygame.MOUSEBUTTONDOWN:
                    x, y = event.pos
                else:  # FINGERDOWN
                    x = int(event.x * self.config.ancho_pantalla)
                    y = int(event.y * self.config.alto_pantalla)

                # Verificar si clickeó en botón de inicio
                if self._click_en_boton_inicio(x, y):
                    eventos_procesados.append({'tipo': 'boton_inicio'})

                # Verificar si clickeó en botón de reiniciar
                elif self._click_en_boton_reiniciar(x, y):
                    eventos_procesados.append({'tipo': 'boton_reiniciar'})

            # Pasar todos los eventos raw al Controller (para TapDetector)
            eventos_procesados.append({
                'tipo': 'evento_raw',
                'evento': event
            })

        return eventos_procesados

    def _click_en_boton_inicio(self, x: int, y: int) -> bool:
        """Verifica si el click fue en el botón de inicio"""
        x_boton = self.config.ancho_pantalla - 160
        y_boton = self.config.alto_pantalla - 60
        return x_boton <= x <= x_boton + 150 and y_boton <= y <= y_boton + 50

    def _click_en_boton_reiniciar(self, x: int, y: int) -> bool:
        """Verifica si el click fue en el botón de reiniciar"""
        x_boton = self.config.ancho_pantalla // 2 - 75
        y_boton = self.config.alto_pantalla // 2 + 20
        return x_boton <= x <= x_boton + 150 and y_boton <= y <= y_boton + 50

    # ============================================================================
    # CONTROL DEL LOOP
    # ============================================================================

    def esta_corriendo(self) -> bool:
        """Retorna True si la vista debe seguir corriendo"""
        return self.running

    def cerrar(self):
        """Cierra la ventana de Pygame"""
        pygame.quit()

    # ============================================================================
    # MÉTODOS OPCIONALES PARA EXTENSIÓN FUTURA
    # ============================================================================

    def mostrar_mensaje(self, mensaje: str, duracion_ms: int = 2000):
        """
        Muestra un mensaje temporal en pantalla.

        Args:
            mensaje: Texto a mostrar
            duracion_ms: Duración en milisegundos
        """
        # TO-DO: Implementar si se necesita feedback visual adicional
        pass

    def cambiar_color_objetivo(self, nuevo_color: tuple):
        """
        Cambia el color del objetivo dinámicamente.

        Args:
            nuevo_color: Tupla RGB (r, g, b)
        """
        self.config.color_objetivo = nuevo_color

    def obtener_fps_actual(self) -> float:
        """Retorna los FPS actuales"""
        return self.reloj.get_fps()
