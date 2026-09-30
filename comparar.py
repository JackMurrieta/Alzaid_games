# -*- coding: utf-8 -*-
"""
comparar.py — Varios fantasmas corriendo al mismo tiempo
=========================================================

Carga 2 o mas sesiones grabadas y las reproduce EN PARALELO, sincronizadas
desde el momento en que cada paciente pico "Inicio". Es la vista que le
sirve al terapeuta: ver la sesion de enero y la de marzo corriendo juntas y
notar, sin leer un solo numero, que el trayecto se hizo mas directo o que
los titubeos frente al objetivo desaparecieron.

    python comparar.py replays/enero.jsonl replays/marzo.jsonl
    python comparar.py replays/            # toma las 4 mas recientes

Controles:  ESPACIO pausa   < > salta 1s   + - velocidad   R reinicia   ESC sale

OJO: comparar solo tiene sentido si las dos sesiones usaron la MISMA
secuencia de objetivos (misma semilla). El programa te avisa si no.
"""

import glob
import os
import sys

import pygame

from fantasma import Fantasma

PALETA = [
    (80, 170, 255),    # azul
    (255, 170, 60),    # ambar
    (120, 220, 130),   # verde
    (235, 110, 190),   # rosa
]

FONDO = (34, 36, 42)
PISTA = (44, 47, 55)
OBJETIVO = (86, 92, 108)
HUD_TX = (232, 234, 238)
HUD_DIM = (140, 146, 158)
ALTO_HUD = 40


def cargar(args):
    rutas = []
    for a in args:
        if os.path.isdir(a):
            rutas += sorted(glob.glob(os.path.join(a, "*.jsonl")), reverse=True)[:4]
        else:
            rutas += sorted(glob.glob(a))
    fantasmas = []
    for i, r in enumerate(rutas[:4]):
        try:
            fantasmas.append(Fantasma(r, color=PALETA[i % len(PALETA)]))
        except Exception as e:
            print(f"[error] {r}: {e}")
    return fantasmas


def main():
    args = sys.argv[1:] or ["replays"]
    fantasmas = cargar(args)
    if len(fantasmas) < 1:
        print(__doc__)
        return

    semillas = {f.seed for f in fantasmas}
    if len(semillas) > 1:
        print("[aviso] Estas sesiones NO usan la misma secuencia de objetivos.")
        print("        Se pueden ver juntas, pero la comparacion no es valida.")
        print("        Fija SEMILLA_PROTOCOLO en la actividad para que lo sean.\n")

    ancho, alto = fantasmas[0].screen
    escala = min(1.0, 1200 / ancho)
    vw, vh = int(ancho * escala), int(alto * escala)
    alto_hud = ALTO_HUD + 26 * len(fantasmas)

    pygame.init()
    pantalla = pygame.display.set_mode((vw, vh + alto_hud))
    pygame.display.set_caption("Comparacion de sesiones")
    f_tit = pygame.font.Font(None, 26)
    f_fila = pygame.font.Font(None, 22)
    f_min = pygame.font.Font(None, 18)
    reloj = pygame.time.Clock()

    duracion = max(f.duracion_ronda_ms for f in fantasmas)
    t = 0.0
    vel = 1.0
    pausado = False
    corriendo = True

    def e(v):
        return int(v * escala)

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

        pantalla.fill(FONDO)
        pantalla.fill(PISTA, pygame.Rect(0, 0, vw, vh))

        # Los objetivos de la primera sesion sirven de referencia de "pista"
        ref = fantasmas[0]
        for tg in ref.targets:
            if tg["ms"] <= t + ref.offset_ms:
                pygame.draw.circle(pantalla, OBJETIVO, (e(tg["x"]), e(tg["y"])),
                                   e(tg.get("r", 50)), 2)

        capa = pygame.Surface((vw, vh), pygame.SRCALPHA)
        for f in fantasmas:
            estela = f.rastro(t, ventana_ms=1200)
            if len(estela) > 1:
                pygame.draw.lines(capa, (*f.color, 110), False,
                                  [(e(x), e(y)) for x, y in estela], 3)
            pos = f.posicion(t)
            if pos is not None:
                pygame.draw.circle(capa, (*f.color, 235), (e(pos[0]), e(pos[1])), 11)
                pygame.draw.circle(capa, (255, 255, 255, 200),
                                   (e(pos[0]), e(pos[1])), 11, 2)
        pantalla.blit(capa, (0, 0))

        # -------------------------------------------------------------- HUD
        cab = f"{t/1000:6.2f}s / {duracion/1000:.2f}s    x{vel:g}    {'PAUSA' if pausado else ''}"
        pantalla.blit(f_tit.render(cab, True, HUD_TX), (14, vh + 10))
        pantalla.blit(
            f_min.render("ESPACIO pausa   < > 1s   + - velocidad   R reinicia   ESC sale",
                         True, HUD_DIM),
            (vw - 430, vh + 14),
        )

        for i, f in enumerate(fantasmas):
            y = vh + ALTO_HUD + i * 26
            pygame.draw.rect(pantalla, f.color, (14, y + 4, 12, 12), border_radius=3)
            if f.termino(t):
                estado = f"TERMINO {f.duracion_ronda_ms/1000:.2f}s"
            else:
                estado = f"{f.aciertos_hasta(t)} aciertos / {f.clicks_hasta(t)} toques"
            linea = f"{f.participante[:14]:14} {f.etiqueta[:11]:11}  {estado}"
            pantalla.blit(f_fila.render(linea, True, HUD_TX), (36, y))

            # Barra de avance de cada sesion
            x0, ancho_barra = vw - 250, 230
            pygame.draw.rect(pantalla, (58, 62, 72), (x0, y + 6, ancho_barra, 8),
                             border_radius=4)
            prog = min(1.0, t / f.duracion_ronda_ms) if f.duracion_ronda_ms else 0
            pygame.draw.rect(pantalla, f.color,
                             (x0, y + 6, int(ancho_barra * prog), 8), border_radius=4)

        pygame.display.flip()

    pygame.quit()


if __name__ == "__main__":
    main()
