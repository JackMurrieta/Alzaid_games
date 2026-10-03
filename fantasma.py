# -*- coding: utf-8 -*-
"""
fantasma.py — Fantasmas al estilo juegos de carreras
=====================================================

QUE ES UN FANTASMA, TECNICAMENTE
--------------------------------
En Gran Turismo, Trackmania o Mario Kart, el "fantasma" que ves correr
junto a ti NO es un programa. Es una tabla de muestras:

    tiempo -> posicion (y a veces orientacion/velocidad)

El juego la carga, y en cada frame busca "donde estaba el fantasma en el
milisegundo 3 450" y dibuja un coche translucido ahi. Nada mas. Por eso un
archivo de fantasma de una vuelta completa pesa unos pocos KB.

Eso es EXACTAMENTE lo que ya tienes en replays/*.jsonl: los eventos "move"
son las muestras de posicion en el tiempo. Este modulo solo les pone una
interfaz comoda: "dame donde estaba el paciente en el ms N".

    f = Fantasma("replays/sesion_anterior.jsonl")
    x, y = f.posicion(3450)      # donde iba su dedo a los 3.45 s
    f.clicks_hasta(3450)         # que toques llevaba
"""

import glob
import os

from input_replay.replay import leer


class Fantasma:
    """Una sesion grabada, lista para dibujarse encima de otra."""

    def __init__(self, ruta, color=(255, 190, 60), etiqueta=None):
        self.ruta = ruta
        self.color = color
        self.meta, eventos = leer(ruta)

        self.moves = [e for e in eventos if e["t"] == "move"]
        self.downs = [e for e in eventos if e["t"] == "down"]
        self.targets = [e for e in eventos if e["t"] == "target"]
        fin = next((e for e in eventos if e["t"] == "end"), None)
        rondas = [e for e in eventos if e["t"] == "round_end"]

        self.duracion_ms = max((e["ms"] for e in eventos), default=0.0)
        self.completada = (fin or {}).get("motivo") == "completed"
        self.duracion_ronda_ms = rondas[0]["duracion_ms"] if rondas else self.duracion_ms
        self.seed = self.meta.get("seed")
        self.screen = tuple(self.meta.get("screen", (1500, 800)))
        self.etiqueta = etiqueta or os.path.basename(ruta)[:19]
        self.participante = self.meta.get("participante", "?")

        # Desfase: el cronometro real empieza cuando el paciente pica "Inicio",
        # no cuando abre el programa. Alineamos ahi para que dos sesiones
        # distintas se puedan comparar de tu a tu.
        inicio = next((e for e in eventos if e["t"] == "round_start"), None)
        self.offset_ms = inicio["ms"] if inicio else 0.0

    # ------------------------------------------------------------------
    def posicion(self, ms):
        """Posicion interpolada del cursor en ese instante (ms desde 'Inicio').

        Busqueda binaria + interpolacion lineal: es lo mismo que hace un
        juego de carreras para que el fantasma se vea fluido aunque las
        muestras vengan a 60 Hz.
        """
        t = ms + self.offset_ms
        m = self.moves
        if not m:
            return None
        if t <= m[0]["ms"]:
            return m[0]["x"], m[0]["y"]
        if t >= m[-1]["ms"]:
            return None  # el fantasma ya termino: deja de dibujarse
        lo, hi = 0, len(m) - 1
        while lo < hi - 1:
            mid = (lo + hi) // 2
            if m[mid]["ms"] <= t:
                lo = mid
            else:
                hi = mid
        a, b = m[lo], m[hi]
        span = b["ms"] - a["ms"]
        k = 0.0 if span == 0 else (t - a["ms"]) / span
        return a["x"] + (b["x"] - a["x"]) * k, a["y"] + (b["y"] - a["y"]) * k

    def rastro(self, ms, ventana_ms=900):
        """Puntos recorridos en la ultima ventana, para dibujar la estela."""
        t = ms + self.offset_ms
        return [(m["x"], m["y"]) for m in self.moves if t - ventana_ms <= m["ms"] <= t]

    def clicks_hasta(self, ms):
        t = ms + self.offset_ms
        return sum(1 for d in self.downs if d["ms"] <= t)

    def aciertos_hasta(self, ms):
        t = ms + self.offset_ms
        return sum(1 for d in self.downs if d["ms"] <= t and d.get("hit"))

    def termino(self, ms):
        return ms + self.offset_ms >= (self.moves[-1]["ms"] if self.moves else 0)


# ----------------------------------------------------------------------
def listar_sesiones(carpeta="replays", actividad=None, participante=None):
    """Sesiones disponibles, de la mas nueva a la mas vieja."""
    salida = []
    for r in sorted(glob.glob(os.path.join(carpeta, "*.jsonl")), reverse=True):
        try:
            meta, _ = leer(r)
        except Exception:
            continue
        if actividad and meta.get("actividad") != actividad:
            continue
        if participante and meta.get("participante") != participante:
            continue
        salida.append((r, meta))
    return salida


def mejor_sesion(carpeta="replays", actividad=None, participante=None, criterio="rapida"):
    """Elige el fantasma contra el cual competir.

    criterio:
      "rapida"  -> la sesion completada mas rapida (como el record de pista)
      "ultima"  -> la sesion mas reciente (comparar contra uno mismo de ayer)
    """
    candidatos = []
    for ruta, _meta in listar_sesiones(carpeta, actividad, participante):
        try:
            f = Fantasma(ruta)
        except Exception:
            continue
        if not f.moves:
            continue
        candidatos.append(f)

    if not candidatos:
        return None
    if criterio == "ultima":
        return candidatos[0]

    completas = [f for f in candidatos if f.completada]
    pool = completas or candidatos
    return min(pool, key=lambda f: f.duracion_ronda_ms)


if __name__ == "__main__":
    import sys

    carpeta = sys.argv[1] if len(sys.argv) > 1 else "replays"
    sesiones = listar_sesiones(carpeta)
    if not sesiones:
        print(f"No hay sesiones en {carpeta}/")
    for ruta, meta in sesiones:
        f = Fantasma(ruta)
        estado = "completada" if f.completada else "incompleta"
        print(f"{os.path.basename(ruta):48}  {meta.get('participante','?'):12} "
              f"{f.duracion_ronda_ms/1000:7.2f}s  {len(f.moves):5} muestras  {estado}")
