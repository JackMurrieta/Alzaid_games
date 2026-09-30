# -*- coding: utf-8 -*-
"""
reproductor_avanzado.py — Visualizador completo de replays (Schema V2)
========================================================================

Reproduce sesiones grabadas con visualizacion avanzada de todas las metricas:
  - Overlay visual: tipo de toque, duracion, presion, multi-touch
  - Panel lateral: tabla de eventos en tiempo real
  - Graficas temporales: n_dedos, duracion, presion vs tiempo
  - Mapa de calor: zonas mas tocadas

    python reproductor_avanzado.py replays/sesion.jsonl

Controles:
  ESPACIO  - pausa/resume
  ← →      - saltar 1s atras/adelante
  + -      - velocidad 2x / 0.5x
  1 2 3 4  - cambiar vista (overlay/panel/graficas/heatmap)
  TAB      - ciclar vistas
  H        - toggle heatmap
  R        - reiniciar desde el inicio
  ESC      - salir
"""

import sys
import math

import pygame

from replay import leer

# ============================= COLORES =====================================
FONDO = (24, 26, 30)
PISTA = (40, 42, 48)
OBJETIVO = (100, 149, 237)

# Toques
ACIERTO = (0, 220, 110)
FALLO = (235, 70, 70)
RASTRO = (180, 185, 195)
CURSOR = (255, 255, 255)

# Input types
COLOR_TOUCH = (80, 170, 255)
COLOR_MOUSE = (255, 180, 80)

# HUD
HUD_BG = (18, 20, 24)
HUD_TX = (235, 237, 242)
HUD_DIM = (140, 146, 158)
PANEL_BG = (32, 34, 38)
PANEL_TX = (220, 222, 228)
PANEL_HIGHLIGHT = (60, 120, 200)

# Heatmap
HEATMAP_COLD = (40, 50, 120)
HEATMAP_MID = (220, 180, 40)
HEATMAP_HOT = (240, 40, 40)

ALTO_HUD = 90
ANCHO_PANEL = 340


# ============================= UTILIDADES ==================================
def interpolar(moves, ms):
    """Posicion del cursor en el instante ms, interpolando entre muestras."""
    if not moves:
        return None
    if ms <= moves[0]["ms"]:
        return moves[0]["x"], moves[0]["y"]
    if ms >= moves[-1]["ms"]:
        return moves[-1]["x"], moves[-1]["y"]
    lo, hi = 0, len(moves) - 1
    while lo < hi - 1:
        mid = (lo + hi) // 2
        if moves[mid]["ms"] <= ms:
            lo = mid
        else:
            hi = mid
    a, b = moves[lo], moves[hi]
    span = b["ms"] - a["ms"]
    k = 0 if span == 0 else (ms - a["ms"]) / span
    return a["x"] + (b["x"] - a["x"]) * k, a["y"] + (b["y"] - a["y"]) * k


def color_presion(pressure):
    """Color degradado segun presion (None -> blanco, 0.0 -> azul, 1.0 -> rojo)."""
    if pressure is None:
        return (255, 255, 255)
    # Interpolacion azul -> amarillo -> rojo
    if pressure < 0.5:
        k = pressure * 2
        return (int(80 + 140 * k), int(170 - 70 * k), int(255 - 155 * k))
    else:
        k = (pressure - 0.5) * 2
        return (int(220 + 20 * k), int(100 - 60 * k), int(100 - 60 * k))


def radio_duracion(duracion_ms):
    """Radio del circulo proporcional a duracion del toque."""
    # 50ms -> 6px, 500ms -> 18px
    return int(6 + min(duracion_ms / 500 * 12, 12))


# ============================= VISTAS ======================================
class VistaOverlay:
    """Vista 1: Overlay visual mejorado sobre el area de juego."""

    def __init__(self, screen, meta, eventos, escala):
        self.screen = screen
        self.meta = meta
        self.eventos = eventos
        self.escala = escala
        self.ancho, self.alto = meta["screen"]
        self.vw = int(self.ancho * escala)
        self.vh = int(self.alto * escala)

        self.targets = [e for e in eventos if e["t"] == "target"]
        self.downs = [e for e in eventos if e["t"] == "down"]
        self.ups = [e for e in eventos if e["t"] == "up"]
        self.moves = [e for e in eventos if e["t"] == "move"]

        # Asociar UP con DOWN para obtener duracion
        self.down_duraciones = {}
        for up in self.ups:
            # Buscar el DOWN correspondiente (mismo finger_id, justo antes del UP)
            finger = up.get("finger_id")
            down_previo = None
            for d in reversed(self.downs):
                if d["ms"] < up["ms"] and d.get("finger_id") == finger:
                    down_previo = d
                    break
            if down_previo:
                idx = self.downs.index(down_previo)
                self.down_duraciones[idx] = up.get("duracion_ms", 0)

    def e(self, v):
        """Escalar coordenada."""
        return int(v * self.escala)

    def render(self, t):
        # Fondo
        self.screen.fill(PISTA, pygame.Rect(0, 0, self.vw, self.vh))

        # Objetivo actual
        actual = None
        for tg in self.targets:
            if tg["ms"] <= t:
                actual = tg
            else:
                break
        if actual:
            pygame.draw.circle(
                self.screen, OBJETIVO,
                (self.e(actual["x"]), self.e(actual["y"])),
                self.e(actual.get("r", 50))
            )

        # Rastro del cursor (ultimos 1.5s)
        rastro = [(self.e(m["x"]), self.e(m["y"])) for m in self.moves if t - 1500 <= m["ms"] <= t]
        if len(rastro) > 1:
            pygame.draw.lines(self.screen, RASTRO, False, rastro, 3)

        # Clicks pasados con OVERLAY AVANZADO
        for i, d in enumerate(self.downs):
            if d["ms"] > t:
                break

            x, y = self.e(d["x"]), self.e(d["y"])
            hit = d.get("hit", False)
            input_type = d.get("input_type", "mouse")
            pressure = d.get("pressure")
            n_dedos = d.get("n_dedos", 1)

            # Duracion del toque
            duracion_ms = self.down_duraciones.get(i, 100)
            radio = radio_duracion(duracion_ms)

            # Color base
            color_base = ACIERTO if hit else FALLO

            # Si hay presion, modular opacidad
            if pressure is not None:
                alpha = int(100 + 155 * pressure)
            else:
                alpha = 220

            # Dibujar circulo principal
            capa = pygame.Surface((self.vw, self.vh), pygame.SRCALPHA)
            pygame.draw.circle(capa, (*color_base, alpha), (x, y), radio)

            # Contorno multiple si multi-touch
            for j in range(n_dedos):
                pygame.draw.circle(capa, (*color_base, 180 - j * 40), (x, y), radio + j * 3, 2)

            # Indicador de tipo (touch=circulo, mouse=cuadrado)
            if input_type == "mouse":
                pygame.draw.rect(capa, (*COLOR_MOUSE, 200), (x - 4, y - 4, 8, 8))
            else:
                pygame.draw.circle(capa, (*COLOR_TOUCH, 200), (x, y), 4)

            self.screen.blit(capa, (0, 0))

            # Texto: numero de dedos si > 1
            if n_dedos > 1:
                font_dedos = pygame.font.Font(None, 18)
                txt = font_dedos.render(str(n_dedos), True, (255, 255, 255))
                self.screen.blit(txt, (x - 6, y - 8))

        # Cursor actual
        pos = interpolar(self.moves, t)
        if pos:
            px, py = self.e(pos[0]), self.e(pos[1])
            pygame.draw.circle(self.screen, CURSOR, (px, py), 8)
            pygame.draw.circle(self.screen, (0, 0, 0), (px, py), 8, 2)


class VistaPanelLateral:
    """Vista 2: Panel lateral con tabla de eventos."""

    def __init__(self, screen, meta, eventos, escala):
        self.screen = screen
        self.meta = meta
        self.eventos = eventos
        self.escala = escala
        self.ancho, self.alto = meta["screen"]
        self.vw = int(self.ancho * escala)
        self.vh = int(self.alto * escala)

        self.downs = [e for e in eventos if e["t"] == "down"]
        self.ups = [e for e in eventos if e["t"] == "up"]

        self.font = pygame.font.Font(None, 18)
        self.font_header = pygame.font.Font(None, 20)

    def render(self, t):
        # Fondo del panel
        pygame.draw.rect(self.screen, PANEL_BG, (self.vw, 0, ANCHO_PANEL, self.vh))

        # Header
        self.screen.blit(
            self.font_header.render("Eventos de Toque", True, (200, 210, 220)),
            (self.vw + 10, 10)
        )

        # Columnas
        y_offset = 40
        header = ["ms", "tipo", "x,y", "dedos", "dur", "hit"]
        col_widths = [50, 50, 70, 45, 45, 35]
        x_base = self.vw + 10

        for i, h in enumerate(header):
            x = x_base + sum(col_widths[:i])
            self.screen.blit(self.font.render(h, True, HUD_DIM), (x, y_offset))

        y_offset += 25
        pygame.draw.line(self.screen, HUD_DIM, (x_base, y_offset), (x_base + ANCHO_PANEL - 20, y_offset), 1)
        y_offset += 5

        # Eventos hasta el tiempo actual
        eventos_visibles = [d for d in self.downs if d["ms"] <= t][-15:]  # ultimos 15

        for d in eventos_visibles:
            ms = f"{int(d['ms'])}"
            tipo = d.get("input_type", "?")[:5]
            pos = f"{int(d['x'])},{int(d['y'])}"
            dedos = str(d.get("n_dedos", 1))
            hit_str = "✓" if d.get("hit") else "✗"

            # Buscar duracion desde UP
            duracion_ms = None
            for u in self.ups:
                if u["ms"] > d["ms"] and u.get("finger_id") == d.get("finger_id"):
                    duracion_ms = u.get("duracion_ms")
                    break
            dur = f"{int(duracion_ms)}" if duracion_ms else "-"

            # Resaltar el evento mas reciente
            color_txt = PANEL_HIGHLIGHT if d == eventos_visibles[-1] else PANEL_TX

            valores = [ms, tipo, pos, dedos, dur, hit_str]
            for i, val in enumerate(valores):
                x = x_base + sum(col_widths[:i])
                self.screen.blit(self.font.render(val, True, color_txt), (x, y_offset))

            y_offset += 22

            if y_offset > self.vh - 30:
                break


class VistaGraficas:
    """Vista 3: Graficas temporales (timeline)."""

    def __init__(self, screen, meta, eventos, escala):
        self.screen = screen
        self.meta = meta
        self.eventos = eventos
        self.escala = escala
        self.ancho, self.alto = meta["screen"]
        self.vw = int(self.ancho * escala)
        self.vh = int(self.alto * escala)

        self.downs = [e for e in eventos if e["t"] == "down"]
        self.ups = [e for e in eventos if e["t"] == "up"]

        self.duracion_ms = max((e["ms"] for e in eventos), default=0)
        self.font_label = pygame.font.Font(None, 20)
        self.font_val = pygame.font.Font(None, 16)

    def render(self, t):
        # Fondo
        pygame.draw.rect(self.screen, FONDO, (0, 0, self.vw, self.vh))

        # Dividir en 3 graficas horizontales
        h_grafica = (self.vh - 60) // 3
        margen = 60

        # === GRAFICA 1: Numero de dedos a lo largo del tiempo ===
        self.render_grafica_dedos(margen, h_grafica, t)

        # === GRAFICA 2: Duracion de cada toque ===
        self.render_grafica_duracion(margen + h_grafica + 10, h_grafica, t)

        # === GRAFICA 3: Presion (si disponible) ===
        self.render_grafica_presion(margen + 2 * (h_grafica + 10), h_grafica, t)

    def render_grafica_dedos(self, y_base, altura, t):
        # Label
        self.screen.blit(self.font_label.render("Número de Dedos Simultáneos", True, HUD_TX), (10, y_base - 30))

        # Fondo grafica
        pygame.draw.rect(self.screen, (30, 32, 36), (10, y_base, self.vw - 20, altura))

        # Eje X: tiempo
        ancho_grafica = self.vw - 20
        for d in self.downs:
            if d["ms"] > self.duracion_ms:
                break
            x = int(10 + (d["ms"] / self.duracion_ms) * ancho_grafica)
            n_dedos = d.get("n_dedos", 1)
            y_barra = y_base + altura - int((n_dedos / 5) * altura)  # max 5 dedos
            color = ACIERTO if d.get("hit") else FALLO
            pygame.draw.line(self.screen, color, (x, y_barra), (x, y_base + altura), 2)

        # Linea del tiempo actual
        x_actual = int(10 + (t / self.duracion_ms) * ancho_grafica)
        pygame.draw.line(self.screen, (255, 255, 100), (x_actual, y_base), (x_actual, y_base + altura), 2)

    def render_grafica_duracion(self, y_base, altura, t):
        self.screen.blit(self.font_label.render("Duración de Toques (ms)", True, HUD_TX), (10, y_base - 30))
        pygame.draw.rect(self.screen, (30, 32, 36), (10, y_base, self.vw - 20, altura))

        ancho_grafica = self.vw - 20
        max_duracion = max((u.get("duracion_ms", 0) for u in self.ups), default=500)

        for u in self.ups:
            if u["ms"] > self.duracion_ms:
                break
            x = int(10 + (u["ms"] / self.duracion_ms) * ancho_grafica)
            dur = u.get("duracion_ms", 0)
            y_barra = y_base + altura - int((dur / max_duracion) * altura)
            pygame.draw.line(self.screen, COLOR_TOUCH, (x, y_barra), (x, y_base + altura), 3)

        x_actual = int(10 + (t / self.duracion_ms) * ancho_grafica)
        pygame.draw.line(self.screen, (255, 255, 100), (x_actual, y_base), (x_actual, y_base + altura), 2)

    def render_grafica_presion(self, y_base, altura, t):
        self.screen.blit(self.font_label.render("Presión (0.0 - 1.0)", True, HUD_TX), (10, y_base - 30))
        pygame.draw.rect(self.screen, (30, 32, 36), (10, y_base, self.vw - 20, altura))

        ancho_grafica = self.vw - 20
        presiones = [(d["ms"], d.get("pressure")) for d in self.downs if d.get("pressure") is not None]

        if not presiones:
            # Sin datos de presion
            self.screen.blit(self.font_val.render("No hay datos de presión disponibles", True, HUD_DIM),
                             (20, y_base + altura // 2))
            return

        # Linea continua
        puntos = []
        for ms, p in presiones:
            if ms > self.duracion_ms:
                break
            x = int(10 + (ms / self.duracion_ms) * ancho_grafica)
            y = int(y_base + altura - (p * altura))
            puntos.append((x, y))

        if len(puntos) > 1:
            pygame.draw.lines(self.screen, COLOR_TOUCH, False, puntos, 2)

        x_actual = int(10 + (t / self.duracion_ms) * ancho_grafica)
        pygame.draw.line(self.screen, (255, 255, 100), (x_actual, y_base), (x_actual, y_base + altura), 2)


class VistaHeatmap:
    """Vista 4: Mapa de calor de zonas tocadas."""

    def __init__(self, screen, meta, eventos, escala):
        self.screen = screen
        self.meta = meta
        self.eventos = eventos
        self.escala = escala
        self.ancho, self.alto = meta["screen"]
        self.vw = int(self.ancho * escala)
        self.vh = int(self.alto * escala)

        self.downs = [e for e in eventos if e["t"] == "down"]

        # Grid de 50x50 celdas
        self.grid_size = 50
        self.celda_w = self.ancho / self.grid_size
        self.celda_h = self.alto / self.grid_size
        self.grid = [[0 for _ in range(self.grid_size)] for _ in range(self.grid_size)]

        # Llenar grid con todos los toques
        for d in self.downs:
            cx = int(d["x"] / self.celda_w)
            cy = int(d["y"] / self.celda_h)
            cx = max(0, min(cx, self.grid_size - 1))
            cy = max(0, min(cy, self.grid_size - 1))
            self.grid[cy][cx] += 1

        self.max_toques = max(max(fila) for fila in self.grid) if self.grid else 1

    def render(self, t):
        # Renderizar solo toques hasta el tiempo t
        grid_t = [[0 for _ in range(self.grid_size)] for _ in range(self.grid_size)]
        for d in self.downs:
            if d["ms"] > t:
                break
            cx = int(d["x"] / self.celda_w)
            cy = int(d["y"] / self.celda_h)
            cx = max(0, min(cx, self.grid_size - 1))
            cy = max(0, min(cy, self.grid_size - 1))
            grid_t[cy][cx] += 1

        # Dibujar heatmap
        for y in range(self.grid_size):
            for x in range(self.grid_size):
                val = grid_t[y][x]
                if val == 0:
                    continue

                # Interpolacion de color
                ratio = val / self.max_toques
                if ratio < 0.5:
                    k = ratio * 2
                    color = (
                        int(HEATMAP_COLD[0] + (HEATMAP_MID[0] - HEATMAP_COLD[0]) * k),
                        int(HEATMAP_COLD[1] + (HEATMAP_MID[1] - HEATMAP_COLD[1]) * k),
                        int(HEATMAP_COLD[2] + (HEATMAP_MID[2] - HEATMAP_COLD[2]) * k),
                    )
                else:
                    k = (ratio - 0.5) * 2
                    color = (
                        int(HEATMAP_MID[0] + (HEATMAP_HOT[0] - HEATMAP_MID[0]) * k),
                        int(HEATMAP_MID[1] + (HEATMAP_HOT[1] - HEATMAP_MID[1]) * k),
                        int(HEATMAP_MID[2] + (HEATMAP_HOT[2] - HEATMAP_MID[2]) * k),
                    )

                px = int(x * self.celda_w * self.escala)
                py = int(y * self.celda_h * self.escala)
                pw = int(self.celda_w * self.escala) + 1
                ph = int(self.celda_h * self.escala) + 1

                alpha = int(80 + 175 * ratio)
                capa = pygame.Surface((pw, ph), pygame.SRCALPHA)
                capa.fill((*color, alpha))
                self.screen.blit(capa, (px, py))


# ============================= MAIN ========================================
def main():
    if len(sys.argv) < 2:
        print(__doc__)
        return

    meta, eventos = leer(sys.argv[1])

    ancho, alto = meta["screen"]
    escala = min(1.0, 1200 / ancho)
    vw, vh = int(ancho * escala), int(alto * escala)

    pygame.init()
    pantalla = pygame.display.set_mode((vw + ANCHO_PANEL, vh + ALTO_HUD))
    pygame.display.set_caption(f"Replay Avanzado - {meta['actividad']} - {meta.get('participante', '')}")

    fuente = pygame.font.Font(None, 24)
    fuente_chica = pygame.font.Font(None, 18)
    reloj = pygame.time.Clock()

    # Crear vistas
    vistas = [
        VistaOverlay(pantalla, meta, eventos, escala),
        VistaPanelLateral(pantalla, meta, eventos, escala),
        VistaGraficas(pantalla, meta, eventos, escala),
        VistaHeatmap(pantalla, meta, eventos, escala),
    ]
    vista_actual = 0

    duracion = max((e["ms"] for e in eventos), default=0)
    t = 0.0
    vel = 1.0
    pausado = False
    corriendo = True

    while corriendo:
        dt = reloj.tick(60)
        if not pausado:
            t += dt * vel
            if t > duracion:
                t, pausado = duracion, True

        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                corriendo = False
            elif ev.type == pygame.KEYDOWN:
                if ev.key == pygame.K_ESCAPE:
                    corriendo = False
                elif ev.key == pygame.K_SPACE:
                    pausado = not pausado
                elif ev.key == pygame.K_r:
                    t, pausado = 0.0, False
                elif ev.key == pygame.K_RIGHT:
                    t = min(duracion, t + 1000)
                elif ev.key == pygame.K_LEFT:
                    t = max(0, t - 1000)
                elif ev.key in (pygame.K_PLUS, pygame.K_EQUALS, pygame.K_KP_PLUS):
                    vel = min(8.0, vel * 2)
                elif ev.key in (pygame.K_MINUS, pygame.K_KP_MINUS):
                    vel = max(0.125, vel / 2)
                elif ev.key == pygame.K_TAB:
                    vista_actual = (vista_actual + 1) % len(vistas)
                elif ev.key == pygame.K_1:
                    vista_actual = 0
                elif ev.key == pygame.K_2:
                    vista_actual = 1
                elif ev.key == pygame.K_3:
                    vista_actual = 2
                elif ev.key == pygame.K_4:
                    vista_actual = 3

        # Fondo
        pantalla.fill(FONDO)

        # Renderizar vista actual
        vistas[vista_actual].render(t)

        # HUD inferior
        pygame.draw.rect(pantalla, HUD_BG, (0, vh, vw + ANCHO_PANEL, ALTO_HUD))

        # Info principal
        info = f"{t/1000:6.2f}s / {duracion/1000:.2f}s    x{vel:g}    {'PAUSA' if pausado else 'reproduciendo'}"
        pantalla.blit(fuente.render(info, True, HUD_TX), (14, vh + 12))

        # Vista actual
        nombres_vistas = ["Overlay Visual", "Panel Lateral", "Gráficas Temporales", "Mapa de Calor"]
        pantalla.blit(fuente.render(f"Vista: {nombres_vistas[vista_actual]}", True, HUD_TX), (14, vh + 40))

        # Controles
        controles = "ESPACIO pausa   ← → 1s   + - velocidad   1-4 vistas   TAB cicla   R reinicia   ESC sale"
        pantalla.blit(fuente_chica.render(controles, True, HUD_DIM), (14, vh + 66))

        # Barra de progreso
        pygame.draw.rect(pantalla, (60, 64, 72), (vw + ANCHO_PANEL - 260, vh + 20, 240, 10), border_radius=4)
        if duracion:
            prog = int(240 * t / duracion)
            pygame.draw.rect(pantalla, ACIERTO, (vw + ANCHO_PANEL - 260, vh + 20, prog, 10), border_radius=4)

        pygame.display.flip()

    pygame.quit()


if __name__ == "__main__":
    main()
