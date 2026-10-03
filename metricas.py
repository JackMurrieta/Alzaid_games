# -*- coding: utf-8 -*-
"""
metricas.py — Deriva metricas a partir de un log de replay
===========================================================

El log JSONL es la fuente de verdad. Este modulo NO guarda nada nuevo:
lee el log y calcula. Si manana se te ocurre una metrica nueva, la
recalculas sobre los logs viejos sin haber perdido nada.

Eso es la ventaja grande de guardar el evento crudo en vez de nada mas
el "tiempo total": el tiempo total no se puede des-agregar, el log si.

    python metricas.py replays/*.jsonl
    python metricas.py replays/ --csv metricas.csv
"""

import csv
import glob
import json
import math
import os
import sys

from input_replay.replay import leer


def _dist(a, b):
    return math.hypot(a[0] - b[0], a[1] - b[1])


def metricas_de_sesion(ruta):
    """Regresa un dict con las metricas de una sesion."""
    meta, eventos = leer(ruta)

    targets = [e for e in eventos if e["t"] == "target"]
    downs = [e for e in eventos if e["t"] == "down"]
    ups = [e for e in eventos if e["t"] == "up"]
    moves = [e for e in eventos if e["t"] == "move"]
    fin = next((e for e in eventos if e["t"] == "end"), None)
    rondas = [e for e in eventos if e["t"] == "round_end"]

    aciertos = [d for d in downs if d.get("hit")]
    fallos = [d for d in downs if not d.get("hit")]

    # ---- Tiempo de reaccion: de que aparece el objetivo a que le atinan ----
    reacciones = []
    for tg in targets:
        siguiente = next(
            (d for d in aciertos if d["ms"] >= tg["ms"] and d.get("target") == tg.get("i")),
            None,
        )
        if siguiente:
            reacciones.append(siguiente["ms"] - tg["ms"])

    # ---- Precision: que tan al centro del objetivo pegan ----
    dispersion = [d["dist"] for d in aciertos if "dist" in d]

    # ---- Cinematica del movimiento (de aqui salen los indicadores motores) ----
    largo_recorrido = 0.0
    velocidades = []
    cambios_direccion = 0
    dir_previa = None
    for i in range(1, len(moves)):
        p0 = (moves[i - 1]["x"], moves[i - 1]["y"])
        p1 = (moves[i]["x"], moves[i]["y"])
        d = _dist(p0, p1)
        dt = (moves[i]["ms"] - moves[i - 1]["ms"]) / 1000.0
        largo_recorrido += d
        if dt > 0:
            velocidades.append(d / dt)
        if d > 0:
            ang = math.atan2(p1[1] - p0[1], p1[0] - p0[0])
            if dir_previa is not None:
                delta = abs(ang - dir_previa)
                delta = min(delta, 2 * math.pi - delta)
                if delta > math.pi / 2:          # giro brusco = titubeo o temblor
                    cambios_direccion += 1
            dir_previa = ang

    duracion_ms = fin["ms"] if fin else (eventos[-1]["ms"] if eventos else 0)
    segundos = duracion_ms / 1000.0 if duracion_ms else 0

    # ---- Nuevas metricas (schema v2): duracion, presion, multi-touch ----
    duraciones = [u.get("duracion_ms") for u in ups if u.get("duracion_ms") is not None]
    presiones = [d.get("pressure") for d in downs if d.get("pressure") is not None]

    # Conteo por tipo de input
    touch_events = [d for d in downs if d.get("input_type") == "touch"]
    mouse_events = [d for d in downs if d.get("input_type") == "mouse"]

    # Multi-touch
    multitouch_events = [d for d in downs if d.get("n_dedos", 1) > 1]
    max_dedos = max((d.get("n_dedos", 1) for d in downs), default=1) if downs else 0

    # Clasificacion de toques por duracion
    toques_prolongados = [d for d in duraciones if d > 500]   # > 500ms
    toques_rapidos = [d for d in duraciones if d < 100]        # < 100ms

    def prom(xs):
        return round(sum(xs) / len(xs), 1) if xs else None

    def desv(xs):
        if len(xs) < 2:
            return None
        m = sum(xs) / len(xs)
        return round(math.sqrt(sum((x - m) ** 2 for x in xs) / (len(xs) - 1)), 1)

    return {
        "session_id": meta["session_id"],
        "actividad": meta["actividad"],
        "participante": meta.get("participante"),
        "started_at": meta.get("started_at"),
        "completada": (fin or {}).get("motivo") == "completed",
        "duracion_s": round(segundos, 2),
        "rondas": len(rondas),
        "objetivos": len(targets),
        "aciertos": len(aciertos),
        "fallos": len(fallos),
        # tasa de error: fundamental, el "tiempo total" solo no la captura
        "tasa_error": round(len(fallos) / len(downs), 3) if downs else None,
        "reaccion_media_ms": prom(reacciones),
        "reaccion_desv_ms": desv(reacciones),          # variabilidad = fatiga / atencion
        "reaccion_peor_ms": round(max(reacciones), 1) if reacciones else None,
        "precision_media_px": prom(dispersion),        # que tan fino es el toque
        "recorrido_px": round(largo_recorrido, 1),
        "velocidad_media_px_s": prom(velocidades),
        "velocidad_pico_px_s": round(max(velocidades), 1) if velocidades else None,
        # proxy de temblor / titubeo: giros bruscos por segundo de movimiento
        "cambios_direccion_por_s": round(cambios_direccion / segundos, 2) if segundos else None,

        # ===== NUEVAS METRICAS (SCHEMA V2) =====
        # Duracion de toques
        "duracion_toque_media_ms": prom(duraciones),
        "duracion_toque_desv_ms": desv(duraciones),
        "duracion_toque_max_ms": round(max(duraciones), 1) if duraciones else None,
        "duracion_toque_min_ms": round(min(duraciones), 1) if duraciones else None,

        # Presion (si disponible)
        "pressure_media": prom(presiones) if presiones else None,
        "pressure_desv": desv(presiones) if presiones else None,
        "pressure_max": round(max(presiones), 3) if presiones else None,
        "pressure_disponible": len(presiones) > 0,

        # Multi-touch
        "multitouch_count": len(multitouch_events),
        "multitouch_max_dedos": max_dedos,
        "multitouch_ratio": round(len(multitouch_events) / len(downs), 3) if downs else None,

        # Tipo de input
        "touch_events": len(touch_events),
        "mouse_events": len(mouse_events),
        "input_type_dominante": "touch" if len(touch_events) > len(mouse_events) else "mouse" if mouse_events else None,

        # Clasificacion por duracion (indicadores cognitivos)
        "toques_prolongados": len(toques_prolongados),
        "toques_rapidos": len(toques_rapidos),
        "ratio_prolongados": round(len(toques_prolongados) / len(duraciones), 3) if duraciones else None,
        "ratio_rapidos": round(len(toques_rapidos) / len(duraciones), 3) if duraciones else None,

        "replay_uri": os.path.abspath(ruta),
        "schema": meta["schema"],
    }


def _expandir(argumentos):
    rutas = []
    for a in argumentos:
        if os.path.isdir(a):
            rutas += sorted(glob.glob(os.path.join(a, "*.jsonl")))
        else:
            rutas += sorted(glob.glob(a))
    return rutas


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    salida_csv = None
    if "--csv" in sys.argv:
        salida_csv = sys.argv[sys.argv.index("--csv") + 1]
        args = [a for a in args if a != salida_csv]

    rutas = _expandir(args or ["replays"])
    if not rutas:
        print("No encontre archivos .jsonl. Corre primero una actividad.")
        return

    filas = []
    for r in rutas:
        try:
            filas.append(metricas_de_sesion(r))
        except Exception as e:
            print(f"[error] {r}: {e}")

    for f in filas:
        print(json.dumps(f, ensure_ascii=False, indent=2))

    if salida_csv and filas:
        with open(salida_csv, "w", newline="", encoding="utf-8") as fh:
            w = csv.DictWriter(fh, fieldnames=list(filas[0].keys()))
            w.writeheader()
            w.writerows(filas)
        print(f"\n{len(filas)} sesiones -> {salida_csv}")


if __name__ == "__main__":
    main()
