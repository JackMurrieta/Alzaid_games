# -*- coding: utf-8 -*-
# ============================================================
# TAP - dar click en la bola que aparece
# ------------------------------------------------------------
# INTERRUPTORES  (ponlos en True cuando quieras la version real)
# ------------------------------------------------------------
GRABAR_VIDEO  = False  # False = NO abre la camara ni graba .avi
GUARDAR_CSV   = False  # False = NO escribe el archivo .csv de resultados
GRABAR_REPLAY = True   # True  = guarda el log de eventos en replays/*.jsonl

# ------------------------------------------------------------
# SEMILLA DEL PROTOCOLO  <-- lee esto, es lo mas importante del archivo
# ------------------------------------------------------------
# Para que las sesiones sean comparables entre si, TODAS deben usar la misma
# secuencia de posiciones donde aparece la bola. Con semilla aleatoria, cada
# sesion tiene objetivos distintos y comparar metricas no tiene sentido.
#
# Con una semilla fija, TODAS las sesiones usan exactamente la misma
# secuencia de objetivos -> las metricas son comparables.
#
#   None      = objetivos aleatorios (no comparable, solo para probar)
#   un numero = protocolo fijo y reproducible (usa esto en las mediciones reales)
SEMILLA_PROTOCOLO = 20260101
# ============================================================


class _CamaraFalsa:
    """Sustituto de cv2.VideoCapture cuando GRABAR_VIDEO = False."""
    def isOpened(self):
        return True

    def read(self):
        return True, None

    def release(self):
        pass


class _VideoFalso:
    """Sustituto de cv2.VideoWriter cuando GRABAR_VIDEO = False."""
    def write(self, frame):
        pass

    def release(self):
        pass


import pygame
import sys
import random
import csv
import time
import os
import cv2
import math

from replay import Recorder

# Inicializar Pygame
pygame.init()
#icon = pygame.image.load("logo.png")
#pygame.display.set_icon(icon)
participante= input ("ingrese su nombre: ")

# Configuración de la ventana
width, height = 1500, 800
window = pygame.display.set_mode((width, height))
pygame.display.set_caption("Actividad TAP")

# Colores
Color_bkg = (169, 169, 169)
Color_ball = (100, 149, 237)

# Variables
circle_radius = 50

# ----------------------------- GRABACION DE REPLAY -----------------------------
# Se crea ANTES de generar el primer objetivo, para que la semilla quede registrada.
rec = Recorder(
    actividad="tap",
    participante=participante,
    screen=(width, height),
    config={"max_score": 5, "circle_radius": circle_radius},
    seed=SEMILLA_PROTOCOLO,
    activo=GRABAR_REPLAY,
)
random.seed(rec.seed)   # misma semilla -> misma secuencia de objetivos
n_objetivo = 0          # indice incremental de cada objetivo que aparece

circle_x = random.randint(circle_radius, width - circle_radius)
circle_y = random.randint(circle_radius, height - circle_radius)
score = 0
max_score = 5  # Define el máximo de aciertos
game_over = False  # Nuevo: estado del juego
tiempo_inicio = 0
tiempo_fin = 0
tiempo_total = 0
color=[0,0,0]
color_boton_inicio = [0, 255, 120]
ronda = 1
tiempos_por_ronda = {}  # Diccionario para almacenar tiempos por ronda
tiempos_completados= []
click = 0

# ----------------------------- SISTEMA MULTI-TOUCH -----------------------------
# Estado de toques activos (para medir duracion y multi-touch)
toques_activos = {}  # {finger_id: {"t_inicio": ms, "x": x, "y": y, "input_type": "touch"}}
# Para mouse (que no tiene finger_id), usamos la clave "mouse"
# -------------------------------------------------------------------------------


# Fuente para mostrar el puntaje
font = pygame.font.Font(None, 36)

def draw_circle():
    pygame.draw.circle(window, Color_ball, (circle_x, circle_y), circle_radius)

def reset_circle():
    global circle_x, circle_y, n_objetivo
    circle_x = random.randint(circle_radius, width - circle_radius)
    circle_y = random.randint(circle_radius, height - circle_radius)
    n_objetivo += 1
    rec.event("target", i=n_objetivo, x=circle_x, y=circle_y, r=circle_radius)

def update_score():
    score_text = font.render(f"Aciertos: {score}", True, [0, 0, 0])
    window.blit(score_text, (10, 10))

def draw_restart_button():
    pygame.draw.rect(window, [0, 0, 0], (width // 2 - 75, height // 2 + 20, 150, 50))
    restart_text = font.render("Reiniciar", True, [233, 233, 233])
    window.blit(restart_text, (width // 2 - 60, height // 2 + 30))

def draw_inicio_button(color):
    pygame.draw.rect(window, color_boton_inicio, (width-160  , height-60 , 150, 50))
    restart_text = font.render("Inicio", True, color)
    window.blit(restart_text, (width - 140, height -50))


# Configuración de OpenCV para captura de video desde la cámara
cap = cv2.VideoCapture(0) if GRABAR_VIDEO else _CamaraFalsa()  # El argumento 0 indica que se usará la cámara predeterminada
if not cap.isOpened():
    print("Error al abrir la cámara.")
    pygame.quit()
    sys.exit()

# Configuración de OpenCV para grabación de video
video_width, video_height = 640, 480  # Ajusta el tamaño del video según tus preferencias
fourcc = cv2.VideoWriter_fourcc(*'XVID')
video_output = cv2.VideoWriter(f'{participante}_TAP.avi', fourcc, 20.0, (video_width, video_height)) if GRABAR_VIDEO else _VideoFalso()


# Bucle principal del juego
running = True
reloj = pygame.time.Clock()

# El primer objetivo tambien se registra
rec.event("target", i=n_objetivo, x=circle_x, y=circle_y, r=circle_radius)
motivo_cierre = "quit"

while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            tiempos_por_ronda[f"Ronda {ronda}"] = {"Nombre": participante, "Tiempo total": tiempo_total, "numero de taps": click}
            running = False

        # ======================= EVENTOS TACTILES (MULTI-TOUCH NATIVO) =======================
        elif event.type == pygame.FINGERMOTION:
            # Movimiento del dedo en pantalla tactil
            x_px = int(event.x * width)
            y_px = int(event.y * height)
            rec.move(x_px, y_px, input_type="touch", finger_id=event.finger_id)

        elif event.type == pygame.FINGERDOWN:
            x_px = int(event.x * width)
            y_px = int(event.y * height)

            # Registrar toque activo
            toques_activos[event.finger_id] = {
                "t_inicio": rec.ms(),
                "x": x_px,
                "y": y_px,
                "input_type": "touch"
            }

            # Intentar obtener presion (SDL2, si disponible)
            pressure = getattr(event, 'pressure', None)

            if game_over:
                if width // 2 - 75 < x_px < width // 2 + 75 and height // 2 + 20 < y_px < height // 2 + 70:
                    # Reiniciar el juego
                    score = 0
                    color=[0,0,0]
                    color_boton_inicio=[0, 255, 120]
                    game_over = False
                    tiempo_inicio = 0
                    tiempo_fin = 0
                    tiempo_total = 0
                    click = 0
                    toques_activos.clear()
                    rec.event("restart", ronda=ronda)
            else:
                if width - 160 <= x_px <= width - 10 and height - 60 <= y_px <= height - 10:
                    # Boton Inicio
                    color = [255,255,255]
                    color_boton_inicio = [0, 0, 0]
                    tiempo_inicio = time.time()
                    game_over = False
                    rec.event("round_start", ronda=ronda)
                else:
                    # Toque en area de juego
                    click += 1
                    distance = math.hypot(x_px - circle_x, y_px - circle_y)
                    hit = bool(distance < circle_radius)

                    # Registrar evento DOWN con nuevos atributos
                    rec.event(
                        "down",
                        x=x_px, y=y_px,
                        hit=hit,
                        target=n_objetivo,
                        dist=round(distance, 1),
                        input_type="touch",
                        finger_id=event.finger_id,
                        pressure=pressure,
                        n_dedos=len(toques_activos)
                    )

                    if hit:
                        score += 1
                        reset_circle()
                        if score >= max_score:
                            game_over = True
                            tiempo_fin = time.time()
                            if tiempo_inicio != 0 and tiempo_fin != 0:
                                tiempo_total = tiempo_fin - tiempo_inicio
                                if tiempo_total > 0:
                                    tiempos_por_ronda[f"Ronda {ronda}"] = {
                                        "Nombre": participante,
                                        "Tiempo total": tiempo_total,
                                        "numero de taps": click
                                    }
                                    rec.event("round_end", ronda=ronda, score=score,
                                              taps=click, duracion_ms=round(tiempo_total * 1000, 1))
                                    motivo_cierre = "completed"
                                    ronda += 1

        elif event.type == pygame.FINGERUP:
            x_px = int(event.x * width)
            y_px = int(event.y * height)

            # Calcular duracion del toque
            if event.finger_id in toques_activos:
                info = toques_activos.pop(event.finger_id)
                duracion_ms = rec.ms() - info["t_inicio"]

                rec.event(
                    "up",
                    x=x_px, y=y_px,
                    finger_id=event.finger_id,
                    duracion_ms=duracion_ms,
                    input_type="touch"
                )

        # ======================= EVENTOS MOUSE (FALLBACK PARA PC) =======================
        elif event.type == pygame.MOUSEMOTION:
            # Solo registrar si NO hay toques tactiles activos
            if not any(info["input_type"] == "touch" for info in toques_activos.values()):
                rec.move(*event.pos, input_type="mouse", finger_id=None)

        elif event.type == pygame.MOUSEBUTTONDOWN:
            x, y = event.pos

            # Registrar toque activo de mouse
            toques_activos["mouse"] = {
                "t_inicio": rec.ms(),
                "x": x,
                "y": y,
                "input_type": "mouse"
            }

            if game_over:
                if width // 2 - 75 < x < width // 2 + 75 and height // 2 + 20 < y < height // 2 + 70:
                    score = 0
                    color=[0,0,0]
                    color_boton_inicio=[0, 255, 120]
                    game_over = False
                    tiempo_inicio = 0
                    tiempo_fin = 0
                    tiempo_total = 0
                    click = 0
                    toques_activos.clear()
                    rec.event("restart", ronda=ronda)
            else:
                if width - 160 <= x <= width - 10 and height - 60 <= y <= height - 10:
                    color = [255,255,255]
                    color_boton_inicio = [0, 0, 0]
                    tiempo_inicio = time.time()
                    game_over = False
                    rec.event("round_start", ronda=ronda)
                else:
                    click += 1
                    distance = math.hypot(x - circle_x, y - circle_y)
                    hit = bool(distance < circle_radius)

                    rec.event(
                        "down",
                        x=x, y=y,
                        hit=hit,
                        target=n_objetivo,
                        dist=round(distance, 1),
                        input_type="mouse",
                        finger_id=None,
                        pressure=None,
                        n_dedos=1
                    )

                    if hit:
                        score += 1
                        reset_circle()
                        if score >= max_score:
                            game_over = True
                            tiempo_fin = time.time()
                            if tiempo_inicio != 0 and tiempo_fin != 0:
                                tiempo_total = tiempo_fin - tiempo_inicio
                                if tiempo_total > 0:
                                    tiempos_por_ronda[f"Ronda {ronda}"] = {
                                        "Nombre": participante,
                                        "Tiempo total": tiempo_total,
                                        "numero de taps": click
                                    }
                                    rec.event("round_end", ronda=ronda, score=score,
                                              taps=click, duracion_ms=round(tiempo_total * 1000, 1))
                                    motivo_cierre = "completed"
                                    ronda += 1

        elif event.type == pygame.MOUSEBUTTONUP:
            x, y = event.pos

            if "mouse" in toques_activos:
                info = toques_activos.pop("mouse")
                duracion_ms = rec.ms() - info["t_inicio"]

                rec.event(
                    "up",
                    x=x, y=y,
                    finger_id=None,
                    duracion_ms=duracion_ms,
                    input_type="mouse"
                )

    if tiempo_total > 0:
        tiempos_completados.append(tiempo_total)  # Guardar tiempo total al terminar el juego


     # Capturar fotograma desde la cámara
    ret, frame = cap.read()
    if not ret:
        print("Error al capturar fotograma desde la cámara.")
        break

    # Grabar el fotograma en el video
    video_output.write(frame)


    window.fill(Color_bkg)
    draw_inicio_button(color)

    draw_circle()
    update_score()

    if game_over:
        draw_restart_button()

    pygame.display.flip()
    reloj.tick(60)           # 60 FPS: sin esto el fantasma se mueve a tirones

# Finalizar Pygame


if GUARDAR_CSV:
    ###### Datos a escribir en el archivo CSV #######
    datos = tiempos_por_ronda
    # Nombre del archivo CSV
    nombre_archivo = "resultados_tap.csv"
    # Verificar si el archivo ya existe
    archivo_existente = os.path.exists(nombre_archivo)
    # Abrir el archivo CSV en modo apéndice
    with open(nombre_archivo, mode='a', newline='') as file:
        # Especificamos los nombres de las columnas
        campos = ["Ronda", "Nombre", "Tiempo total", "Número de taps"]
        # Creamos el escritor CSV
        writer = csv.DictWriter(file, fieldnames=campos)
        # Escribimos los datos
        if not archivo_existente:
            # Si el archivo no existe, escribimos los encabezados
            writer.writeheader()

        for ronda, datos_ronda in datos.items():
            writer.writerow({
                "Ronda": ronda,
                "Nombre": datos_ronda["Nombre"],
                "Tiempo total": datos_ronda["Tiempo total"],
                "Número de taps": datos_ronda["numero de taps"]
            })

else:
    # Sin guardar archivo: los resultados solo se muestran en la consola
    print("\n--- Resultados de esta sesion (NO se guardo ningun archivo) ---")
    for _r, _d in tiempos_por_ronda.items():
        print(_r, _d)
    print("-------------------------------------------------------------\n")


pygame.quit()
cap.release()
video_output.release()

ruta_replay = rec.close(motivo_cierre, rondas=len(tiempos_por_ronda))
if ruta_replay:
    print(f"\nReplay guardado: {ruta_replay}")
    print(f"  Verlo:      python reproductor.py {ruta_replay}")
    print(f"  Metricas:   python metricas.py {ruta_replay}\n")

sys.exit()
