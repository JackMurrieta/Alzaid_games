# -*- coding: utf-8 -*-
"""
test_patron.py - Script para visualizar el patrón de objetivos
===============================================================

Ejecutar:
    python -m actividades.tap_actividad.test_patron
"""

from models.patron_objetivos import PatronObjetivos


def test_patron_basico():
    """Prueba el patrón básico con elecciones aleatorias deterministas"""
    print("=" * 70)
    print("PATRÓN BÁSICO (con elecciones aleatorias deterministas)")
    print("=" * 70)

    patron = PatronObjetivos(ancho=1500, alto=800, margen=50, semilla=20260101)

    print("\nSecuencia de los primeros 24 objetivos (2 ciclos completos):\n")

    for i in range(24):
        x, y, desc = patron.siguiente_posicion()
        escenario = patron.obtener_escenario_actual()
        ciclo = patron.obtener_ciclo_actual()

        print(f"Objetivo #{i:2d} | Escenario {escenario} | Ciclo {ciclo} | "
              f"Pos: ({x:4d}, {y:3d}) | {desc}")

        # Separador entre escenarios
        if (i + 1) % 6 == 0:
            print("-" * 70)


def test_patron_fijo():
    """Prueba el patrón completamente fijo"""
    print("\n" + "=" * 70)
    print("PATRÓN FIJO (completamente determinista, sin aleatoriedad)")
    print("=" * 70)

    patron = PatronObjetivos(ancho=1500, alto=800, margen=50, semilla=20260101)

    print("\nSecuencia de los primeros 24 objetivos (2 ciclos completos):\n")

    for i in range(24):
        x, y, desc = patron.siguiente_posicion_fija()

        print(f"Objetivo #{i:2d} | Pos: ({x:4d}, {y:3d}) | {desc}")

        # Separador cada 12 (ciclo completo)
        if (i + 1) % 12 == 0:
            print("-" * 70)


def test_reproducibilidad():
    """Prueba que la misma semilla produce la misma secuencia"""
    print("\n" + "=" * 70)
    print("TEST DE REPRODUCIBILIDAD")
    print("=" * 70)

    print("\nGenerando 2 patrones con la MISMA semilla (20260101)...")

    patron1 = PatronObjetivos(ancho=1500, alto=800, semilla=20260101)
    patron2 = PatronObjetivos(ancho=1500, alto=800, semilla=20260101)

    print("\nComparando primeros 12 objetivos:\n")

    iguales = True
    for i in range(12):
        x1, y1, desc1 = patron1.siguiente_posicion()
        x2, y2, desc2 = patron2.siguiente_posicion()

        match = "✓" if (x1 == x2 and y1 == y2) else "✗"
        print(f"{match} Objetivo #{i:2d}: Patrón1=({x1}, {y1}) | Patrón2=({x2}, {y2})")

        if x1 != x2 or y1 != y2:
            iguales = False

    if iguales:
        print("\n✓ ÉXITO: Ambos patrones generan la misma secuencia")
    else:
        print("\n✗ ERROR: Los patrones difieren")


def test_posiciones_unicas():
    """Muestra todas las posiciones únicas del patrón"""
    print("\n" + "=" * 70)
    print("POSICIONES ÚNICAS DEL PATRÓN")
    print("=" * 70)

    patron = PatronObjetivos(ancho=1500, alto=800, margen=50)

    posiciones = patron.obtener_todas_posiciones_unicas()

    print(f"\nTotal de posiciones únicas: {len(posiciones)}\n")

    for x, y, desc in posiciones:
        print(f"  • ({x:4d}, {y:3d}) → {desc}")


def comparar_semillas():
    """Compara cómo cambian las secuencias con diferentes semillas"""
    print("\n" + "=" * 70)
    print("COMPARACIÓN DE SEMILLAS DIFERENTES")
    print("=" * 70)

    semillas = [20260101, 12345, 99999]

    print("\nPrimeros 6 objetivos con diferentes semillas:\n")

    for semilla in semillas:
        patron = PatronObjetivos(ancho=1500, alto=800, semilla=semilla)
        print(f"Semilla {semilla}:")

        for i in range(6):
            x, y, desc = patron.siguiente_posicion()
            print(f"  {i+1}. ({x:4d}, {y:3d}) - {desc}")

        print()


if __name__ == "__main__":
    test_patron_basico()
    test_patron_fijo()
    test_reproducibilidad()
    test_posiciones_unicas()
    comparar_semillas()

    print("\n" + "=" * 70)
    print("CONCLUSIÓN")
    print("=" * 70)
    print("""
El patrón determinista garantiza que:
  ✓ Misma semilla = misma secuencia exacta de objetivos
  ✓ Diferentes pacientes resuelven el MISMO desafío
  ✓ Sesiones del mismo paciente son COMPARABLES a lo largo del tiempo
  ✓ Las métricas tienen validez científica

Recomendación:
  - Usar semilla FIJA (ej: 20260101) para estudios clínicos
  - Usar patron.siguiente_posicion_fija() para máxima reproducibilidad
    """)
