# -*- coding: utf-8 -*-
"""
replay.py — Grabador de sesiones (event sourcing)
=================================================

Graba TODO lo que pasa en una actividad como un log de eventos en JSONL
(un objeto JSON por linea). Ese archivo es la FUENTE DE VERDAD: de ahi
salen las metricas y de ahi se reconstruye el replay visual.

Por que JSONL y no un .py ni un video:
  - Es DATO, no codigo. Nunca ejecutas nada que venga de un archivo guardado.
  - Append-only: si el programa se cae a media sesion, lo grabado sigue valido.
  - Pesa kilobytes, no megabytes.
  - Se puede consultar, agregar y versionar.

Uso minimo:

    from replay import Recorder

    rec = Recorder(actividad="tap", participante="ana", screen=(1500, 800),
                   config={"max_score": 5, "circle_radius": 50})
    random.seed(rec.seed)          # <- para que el replay sea reproducible

    rec.event("target", i=0, x=300, y=400, r=50)
    rec.move(x, y)                 # se auto-limita a ~60 Hz
    rec.event("down", x=x, y=y, hit=True, target=0, dist=12.4,
              input_type="touch", finger_id=0, pressure=0.75, n_dedos=1)
    rec.event("up", x=x, y=y, finger_id=0, duracion_ms=145.3)
    ...
    ruta = rec.close("completed")

SCHEMA V2 - Nuevos campos opcionales (retrocompatibles):
    Evento "down":
      - input_type: "touch" | "mouse" (tipo de entrada)
      - finger_id: 0-N si touch, None si mouse (ID del dedo)
      - pressure: 0.0-1.0 si disponible, None si no (presion del toque)
      - n_dedos: int, cuantos dedos tocaron simultaneamente

    Evento "up" (NUEVO):
      - x, y: posicion donde se solto
      - finger_id: ID del dedo
      - duracion_ms: tiempo que mantuvo presionado (DOWN → UP)
      - input_type: "touch" | "mouse"

    Evento "move":
      - input_type: "touch" | "mouse" (NUEVO)
      - finger_id: 0-N si touch, None si mouse (NUEVO)
"""

import json
import os
import platform
import random
import sys
import time
import uuid
from datetime import datetime, timezone

SCHEMA_VERSION = 2
APP_VERSION = "1.1.0"

# Muestreo del movimiento: sin esto el log se llena de miles de eventos inutiles
INTERVALO_MIN_MS = 16.0   # ~60 Hz maximo
DISTANCIA_MIN_PX = 2      # ignora micro-movimientos del mouse


class Recorder:
    """Escribe un log de eventos JSONL, una linea por evento."""

    def __init__(
        self,
        actividad,
        participante,
        screen,
        config=None,
        carpeta="replays",
        seed=None,
        activo=True,
    ):
        self.activo = activo
        self.actividad = actividad
        self.session_id = str(uuid.uuid4())
        self.seed = seed if seed is not None else random.randrange(2 ** 31)

        self._t0 = time.perf_counter()
        self._ultimo_move_ms = -9999.0
        self._ultimo_xy = (None, None)
        self._n_eventos = 0
        self._f = None
        self.ruta = None

        if not self.activo:
            return

        os.makedirs(carpeta, exist_ok=True)
        sello = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        nombre = f"{sello}_{actividad}_{self.session_id[:8]}.jsonl"
        self.ruta = os.path.join(carpeta, nombre)
        self._f = open(self.ruta, "w", encoding="utf-8")

        # La PRIMERA linea es siempre la cabecera: sin ella el log no se puede leer
        self._escribir({
            "t": "meta",
            "schema": SCHEMA_VERSION,
            "app_version": APP_VERSION,
            "session_id": self.session_id,
            "actividad": actividad,
            "participante": participante,
            "started_at": datetime.now(timezone.utc).isoformat(),
            "seed": self.seed,
            "screen": list(screen),
            "config": config or {},
            "runtime": {
                "python": platform.python_version(),
                "so": f"{platform.system()} {platform.release()}",
            },
        })
        self._f.flush()

    # ---------------------------------------------------------------- interno
    def _escribir(self, obj):
        self._f.write(json.dumps(obj, ensure_ascii=False, separators=(",", ":")) + "\n")
        self._n_eventos += 1

    def ms(self):
        """Milisegundos desde que arranco la sesion. Monotonico: no se ve afectado
        si cambia la hora del sistema a media prueba."""
        return round((time.perf_counter() - self._t0) * 1000.0, 1)

    # ---------------------------------------------------------------- publico
    def event(self, tipo, **campos):
        """Evento discreto (click, cambio de ronda, fin). Se hace flush enseguida
        para que sobreviva a un cierre abrupto."""
        if not self.activo:
            return
        campos["t"] = tipo
        campos["ms"] = self.ms()
        self._escribir(campos)
        self._f.flush()

    def move(self, x, y, input_type=None, finger_id=None):
        """Movimiento del cursor/dedo. Se limita en frecuencia y en distancia,
        y NO hace flush (seria carisimo a 60 Hz)."""
        if not self.activo:
            return
        ahora = self.ms()
        if ahora - self._ultimo_move_ms < INTERVALO_MIN_MS:
            return
        ux, uy = self._ultimo_xy
        if ux is not None and abs(x - ux) < DISTANCIA_MIN_PX and abs(y - uy) < DISTANCIA_MIN_PX:
            return
        self._ultimo_move_ms = ahora
        self._ultimo_xy = (x, y)

        # Evento base
        evt = {"t": "move", "ms": ahora, "x": int(x), "y": int(y)}

        # Agregar campos opcionales (schema v2)
        if input_type is not None:
            evt["input_type"] = input_type
        if finger_id is not None:
            evt["finger_id"] = finger_id

        self._escribir(evt)

    def close(self, motivo="completed", **campos):
        """Cierra la sesion. motivo: completed | quit | error"""
        if not self.activo or self._f is None:
            return None
        campos["motivo"] = motivo
        campos["n_eventos"] = self._n_eventos
        self.event("end", **campos)
        self._f.close()
        self._f = None
        return self.ruta


def leer(ruta):
    """Lee un .jsonl y regresa (meta, lista_de_eventos).

    Tolera la ultima linea truncada: si el programa se murio a media escritura,
    esa linea se descarta y el resto sigue siendo util.
    """
    meta = None
    eventos = []
    with open(ruta, encoding="utf-8") as f:
        for i, linea in enumerate(f):
            linea = linea.strip()
            if not linea:
                continue
            try:
                obj = json.loads(linea)
            except json.JSONDecodeError:
                print(f"[aviso] linea {i + 1} corrupta, se ignora (sesion incompleta)")
                continue
            if obj.get("t") == "meta":
                meta = obj
            else:
                eventos.append(obj)
    if meta is None:
        raise ValueError(f"{ruta} no tiene cabecera 'meta', no se puede interpretar")
    return meta, eventos
