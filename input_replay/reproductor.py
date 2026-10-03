# -*- coding: utf-8 -*-
"""
reproductor.py — Reproduce visualmente un replay grabado
=========================================================

Punto clave de diseno: este reproductor RE-DIBUJA a partir del log.
NO vuelve a ejecutar la logica del juego.

Es la diferencia entre "replay determinista" (volver a correr el juego con
la misma semilla y rezar que todo salga igual) y "replay por renderizado"
(leer que paso y pintarlo). El segundo es el que aguanta: no se rompe
cuando cambies el juego, ni cuando cambie la version de pygame, ni cuando
el monitor tenga otra resolucion.

    python reproductor.py replays/20260925T...jsonl

Controles:  ESPACIO pausa   <- -> salta 2s   + - velocidad   ESC sale
"""

import sys

import pygame

from input_replay.replay import leer

FONDO = (169, 169, 169)
OBJETIVO = (100, 149, 237)
RASTRO = (70, 70, 90)
CURSOR = (255, 255, 255)
ACIERTO = (0, 200, 110)
FALLO = (220, 70, 70)
HUD_BG = (24, 26, 30)
HUD_TX = (235, 235, 235)

ALTO_HUD = 64


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


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        return
    meta, eventos = leer(sys.argv[1])

    ancho, alto = meta["screen"]
    escala = min(1.0, 1280 / ancho)           # cabe en pantallas chicas
    vw, vh = int(ancho * escala), int(alto * escala)

    moves = [e for e in eventos if e["t"] == "move"]
    targets = [e for e in eventos if e["t"] == "target"]
    downs = [e for e in eventos if e["t"] == "down"]
    duracion = max((e["ms"] for e in eventos), default=0)

    pygame.init()
    pantalla = pygame.display.set_mode((vw, vh + ALTO_HUD))
    pygame.display.set_caption(f"Replay — {meta['actividad']} — {meta.get('participante','')}")
    fuente = pygame.font.Font(None, 24)
    fuente_chica = pygame.font.Font(None, 20)
    reloj = pygame.time.Clock()

    t = 0.0
    velocidad = 1.0
    pausado = False
    corriendo = True

    def e(v):
        return int(v * escala)

    while corriendo:
        dt = reloj.tick(60)
        if not pausado:
            t += dt * velocidad
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
                elif ev.key == pygame.K_RIGHT:
                    t = min(duracion, t + 2000)
                elif ev.key == pygame.K_LEFT:
                    t = max(0, t - 2000)
                elif ev.key in (pygame.K_PLUS, pygame.K_EQUALS, pygame.K_KP_PLUS):
                    velocidad = min(8.0, velocidad * 2)
                elif ev.key in (pygame.K_MINUS, pygame.K_KP_MINUS):
                    velocidad = max(0.125, velocidad / 2)

        pantalla.fill(FONDO, pygame.Rect(0, 0, vw, vh))

        # Objetivo vigente en este instante
        actual = None
        for tg in targets:
            if tg["ms"] <= t:
                actual = tg
            else:
                break
        if actual:
            pygame.draw.circle(
                pantalla, OBJETIVO, (e(actual["x"]), e(actual["y"])), e(actual.get("r", 50))
            )

        # Rastro del cursor (ultimos 1.5 s)
        rastro = [(e(m["x"]), e(m["y"])) for m in moves if t - 1500 <= m["ms"] <= t]
        if len(rastro) > 1:
            pygame.draw.lines(pantalla, RASTRO, False, rastro, 2)

        # Clicks ya ocurridos
        for d in downs:
            if d["ms"] > t:
                break
            color = ACIERTO if d.get("hit") else FALLO
            pygame.draw.circle(pantalla, color, (e(d["x"]), e(d["y"])), 7, 2)

        # Cursor
        pos = interpolar(moves, t)
        if pos:
            pygame.draw.circle(pantalla, CURSOR, (e(pos[0]), e(pos[1])), 6)
            pygame.draw.circle(pantalla, (0, 0, 0), (e(pos[0]), e(pos[1])), 6, 1)

        # ---------------------------------------------------------------- HUD
        pantalla.fill(HUD_BG, pygame.Rect(0, vh, vw, ALTO_HUD))
        hechos = sum(1 for d in downs if d["ms"] <= t and d.get("hit"))
        errados = sum(1 for d in downs if d["ms"] <= t and not d.get("hit"))
        info = (
            f"{t/1000:6.2f}s / {duracion/1000:.2f}s    x{velocidad:g}    "
            f"aciertos {hechos}   fallos {errados}    "
            f"{'PAUSA' if pausado else 'reproduciendo'}"
        )
        pantalla.blit(fuente.render(info, True, HUD_TX), (14, vh + 12))
        pantalla.blit(
            fuente_chica.render("ESPACIO pausa   < > salta 2s   + - velocidad   ESC sale",
                                True, (140, 145, 155)),
            (14, vh + 38),
        )
        # Barra de progreso
        pygame.draw.rect(pantalla, (60, 64, 72), (vw - 260, vh + 20, 240, 8), border_radius=4)
        if duracion:
            pygame.draw.rect(
                pantalla, ACIERTO,
                (vw - 260, vh + 20, int(240 * t / duracion), 8), border_radius=4
            )

        pygame.display.flip()

    pygame.quit()


if __name__ == "__main__":
    main()
