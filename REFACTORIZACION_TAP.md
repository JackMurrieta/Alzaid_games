# Refactorización 01_tap.py - Changelog y Guía de Uso

## Cambios Realizados (Schema V2)

### 1. Sistema de Fantasmas ELIMINADO
- **Removido:** Todo el código relacionado con `fantasma.py`, `MOSTRAR_FANTASMA`, `FANTASMA_CRITERIO`
- **Razón:** Simplificar la interfaz durante el juego y enfocar en captura de datos
- **Efecto:** La actividad ahora es más limpia, el análisis se hace en replay posterior

### 2. Detección Automática Táctil/Mouse
✅ **Implementado** - Soporte dual sin configuración manual

**Cómo funciona:**
- El código escucha **simultáneamente** eventos `FINGERDOWN/FINGERUP/FINGERMOTION` (táctil) y `MOUSEBUTTONDOWN/MOUSEBUTTONUP/MOUSEMOTION` (mouse)
- Automáticamente detecta qué tipo de input está usando el paciente
- Guarda `input_type: "touch"` o `"mouse"` en cada evento

**Beneficios:**
- Testing en PC con mouse funciona perfectamente
- En pantalla táctil, detecta automáticamente y captura multi-touch
- Sin necesidad de cambiar código o configuración

### 3. Nuevas Métricas Capturadas

#### A) Duración del Toque (DOWN → UP)
- **Campo:** `duracion_ms` en evento `"up"`
- **Qué mide:** Tiempo en milisegundos que el paciente mantuvo presionado
- **Valor clínico:** Toques prolongados pueden indicar dificultad para planificar liberación motora

#### B) Multi-Touch Simultáneo
- **Campo:** `n_dedos` en evento `"down"` (cuántos dedos tocaron al mismo tiempo)
- **Campo:** `finger_id` (0, 1, 2...) en eventos táctiles
- **Qué mide:** Control motor fino, toques involuntarios
- **Valor clínico:** Multi-touch no intencional puede indicar problemas de control motor

#### C) Presión del Toque
- **Campo:** `pressure` (0.0 a 1.0) si el hardware lo soporta, `null` si no
- **Qué mide:** Fuerza aplicada al tocar (solo en pantallas que lo soporten)
- **Nota:** La mayoría de pantallas táctiles capacitivas NO envían presión, será `null`
- **Aproximación:** Usamos `duracion_ms` como proxy de "intensidad"

#### D) Coordenadas de Objetivos
- **Ya existía:** Evento `"target"` con `x`, `y`, `r` (radio)
- **Ahora garantizado:** Todas las apariciones de objetivos quedan registradas

### 4. Nuevo Evento: "up"
**Antes:** Solo se registraba el DOWN (toque inicial)
**Ahora:** También se registra el UP (levantamiento), con:
```json
{
  "t": "up",
  "ms": 705.7,
  "x": 439,
  "y": 191,
  "finger_id": 0,
  "duracion_ms": 145.3,
  "input_type": "touch"
}
```

### 5. Schema Actualizado (V1 → V2)
- `SCHEMA_VERSION = 2` en `replay.py`
- **Retrocompatible:** Los logs antiguos (v1) se pueden leer sin problemas
- Los nuevos campos son opcionales, no rompen compatibilidad

---

## Archivos Modificados

| Archivo | Cambios |
|---------|---------|
| `replay.py` | Schema v2, método `move()` acepta `input_type` y `finger_id` |
| `01_tap.py` | Eliminado fantasmas, implementado dual touch/mouse, captura nuevas métricas |
| `metricas.py` | Agregadas 15 métricas nuevas (duracion, presion, multi-touch, ratios) |
| `reproductor_avanzado.py` | **NUEVO** - Reproductor con 4 vistas avanzadas |

---

## Nuevas Métricas en metricas.py

Ejecutar:
```bash
.venv/Scripts/python metricas.py replays/sesion.jsonl
```

### Métricas Agregadas (Schema V2)

#### Duración de Toques
- `duracion_toque_media_ms`: Promedio de tiempo presionado
- `duracion_toque_desv_ms`: Variabilidad (inconsistencia motora)
- `duracion_toque_max_ms`: Toque más prolongado
- `duracion_toque_min_ms`: Toque más rápido

#### Presión
- `pressure_media`: Presión promedio (0.0-1.0) si disponible
- `pressure_desv`: Variabilidad de presión
- `pressure_max`: Presión máxima registrada
- `pressure_disponible`: `true/false` si el hardware soporta presión

#### Multi-Touch
- `multitouch_count`: Número de toques con 2+ dedos
- `multitouch_max_dedos`: Máximo de dedos simultáneos
- `multitouch_ratio`: Proporción de toques multi-touch

#### Tipo de Input
- `touch_events`: Toques con pantalla táctil
- `mouse_events`: Toques con mouse
- `input_type_dominante`: "touch" o "mouse" según mayoría

#### Clasificación por Duración (Indicadores Cognitivos)
- `toques_prolongados`: Toques > 500ms (vacilación/planificación)
- `toques_rapidos`: Toques < 100ms (impulsividad)
- `ratio_prolongados`: Proporción de toques lentos
- `ratio_rapidos`: Proporción de toques rápidos

**Valor clínico:** El ratio de toques prolongados vs rápidos puede indicar:
- Alto ratio prolongado → Dificultad para planificar liberación motora
- Alto ratio rápido → Impulsividad, falta de control

---

## Reproductor Avanzado (NUEVO)

### Uso
```bash
.venv/Scripts/python reproductor_avanzado.py replays/sesion.jsonl
```

### 4 Vistas Disponibles

#### Vista 1: Overlay Visual Mejorado
- **Toques:** Círculos de tamaño proporcional a duración
- **Colores:** Verde=acierto, Rojo=fallo
- **Multi-touch:** Contornos múltiples según número de dedos
- **Tipo:** Círculo pequeño=touch, Cuadrado=mouse
- **Presión:** Opacidad del color según intensidad (si disponible)
- **Texto:** Número de dedos si > 1

#### Vista 2: Panel Lateral de Eventos
- **Tabla:** Lista de todos los toques con atributos
- **Columnas:** ms, tipo, x-y, dedos, duración, hit
- **Auto-scroll:** Sigue el replay
- **Highlight:** Evento actual resaltado en azul

#### Vista 3: Gráficas Temporales
- **Gráfica 1:** Número de dedos a lo largo del tiempo
- **Gráfica 2:** Duración de cada toque (barras verticales)
- **Gráfica 3:** Presión si disponible (línea continua)
- **Marcadores:** Verde=aciertos, Rojo=fallos
- **Cursor:** Línea amarilla en tiempo actual

#### Vista 4: Mapa de Calor
- **Grid:** 50×50 celdas
- **Gradiente:** Azul (frío) → Amarillo → Rojo (caliente)
- **Qué muestra:** Zonas más tocadas, frecuencia acumulada
- **Uso clínico:** Detectar si el paciente favorece ciertas áreas

### Controles
| Tecla | Acción |
|-------|--------|
| `ESPACIO` | Pausa/Resume |
| `← →` | Saltar 1s atrás/adelante |
| `+ -` | Velocidad 2x / 0.5x |
| `1 2 3 4` | Cambiar vista directamente |
| `TAB` | Ciclar entre vistas |
| `R` | Reiniciar desde el inicio |
| `ESC` | Salir |

---

## Testing

### En PC con Mouse
```bash
.venv/Scripts/python 01_tap.py
```
- Ingresar nombre
- Click en "Inicio"
- Jugar con mouse normalmente
- Los eventos se guardarán como `input_type: "mouse"`

### En Pantalla Táctil
- Ejecutar el mismo archivo
- Tocar con dedos
- Los eventos se guardarán como `input_type: "touch"`
- Si tocas con 2+ dedos, `n_dedos` reflejará eso

### Verificar Datos Capturados
```bash
# Ver replay
.venv/Scripts/python reproductor_avanzado.py replays/<archivo>.jsonl

# Ver métricas
.venv/Scripts/python metricas.py replays/<archivo>.jsonl

# Exportar a CSV
.venv/Scripts/python metricas.py replays/ --csv resultados.csv
```

---

## Compatibilidad

### Logs Antiguos (Schema V1)
✅ **Se pueden leer sin problemas**
- `metricas.py` calcula métricas antiguas + nuevas (campos opcionales)
- `reproductor.py` original sigue funcionando
- `reproductor_avanzado.py` detecta campos faltantes y los trata como `None`

### Logs Nuevos (Schema V2)
✅ **Incluyen todos los campos extendidos**
- Todos los archivos generados desde esta refactorización tendrán `schema: 2`
- Métricas completas disponibles

---

## Interpretación Clínica

### Métricas con Mayor Valor Diagnóstico

#### 1. Duración de Toque (Variabilidad)
- **Métrica:** `duracion_toque_desv_ms`
- **Qué indica:** Inconsistencia en control motor
- **Interpretación:** Desviación alta → Fatiga, dificultad para mantener consistencia

#### 2. Multi-Touch Involuntario
- **Métrica:** `multitouch_ratio`
- **Qué indica:** Control motor fino
- **Interpretación:** Ratio alto (> 0.3) → Dificultad para aislar dedos

#### 3. Ratio Toques Prolongados
- **Métrica:** `ratio_prolongados`
- **Qué indica:** Planificación motora
- **Interpretación:**
  - Alto (> 0.4) → Dificultad para liberar toque, vacilación
  - Bajo (< 0.1) → Control adecuado

#### 4. Cambios de Dirección (ya existía)
- **Métrica:** `cambios_direccion_por_s`
- **Qué indica:** Temblor, titubeo
- **Interpretación:** > 5 giros/s → Posible temblor intencional

### Seguimiento Longitudinal
**Comparar mismo paciente a lo largo del tiempo:**
```bash
# Sesiones del mismo paciente
.venv/Scripts/python metricas.py replays/ --csv evolucion.csv

# Filtrar en Excel/Python por participante y analizar tendencias
```

---

## Próximos Pasos Sugeridos

### 1. Testing Real en Pantalla Táctil
- Ejecutar en mesa interactiva
- Verificar captura de `finger_id`
- Probar multi-touch deliberado (2-3 dedos)

### 2. Validar Presión
- La mayoría de pantallas capacitivas NO tienen presión
- Si tu hardware soporta presión, verificar que `pressure` no sea `null`
- Si es `null`, usar `duracion_ms` como proxy

### 3. Migrar Otras 9 Actividades
El mismo patrón aplicado a `01_tap.py` se puede replicar en:
- `02_drag_and_drop.py`
- `03_pinch_zoom.py`
- ... (resto de actividades)

---

## Preguntas Frecuentes

### ¿Por qué eliminar fantasmas?
**Respuesta:** El fantasma agregaba complejidad visual durante el juego. La refactorización se enfoca en capturar datos detallados y analizarlos DESPUÉS en el reproductor. Si más adelante quieres volver a agregarlo, está en el git history.

### ¿El código detecta automáticamente táctil vs mouse?
**Respuesta:** Sí, escucha ambos tipos de eventos simultáneamente. No necesitas cambiar nada para testing en PC vs producción en pantalla táctil.

### ¿Qué pasa si `pressure` siempre es `null`?
**Respuesta:** Es normal en pantallas capacitivas. Las métricas usan `duracion_ms` como aproximación de "intensidad/intención" del toque.

### ¿Puedo seguir usando `reproductor.py` simple?
**Respuesta:** Sí, sigue funcionando. `reproductor_avanzado.py` es opcional para análisis profundo.

---

## Resumen de Comandos

```bash
# Jugar actividad (PC con mouse o pantalla táctil)
.venv/Scripts/python 01_tap.py

# Ver replay con visualización avanzada
.venv/Scripts/python reproductor_avanzado.py replays/<archivo>.jsonl

# Calcular métricas de una sesión
.venv/Scripts/python metricas.py replays/<archivo>.jsonl

# Exportar todas las sesiones a CSV
.venv/Scripts/python metricas.py replays/ --csv resultados.csv

# Listar sesiones disponibles
.venv/Scripts/python fantasma.py replays
```

---

**Fecha:** 2026-09-25
**Schema Version:** 2
**Autor:** Refactorización para soporte multi-touch y análisis clínico avanzado
