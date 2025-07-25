"""Funciones utilitarias para calculo de angulos en tres puntos."""

import math
from typing import Tuple


Point = Tuple[float, float]


def calcular_angulo(a: Point, b: Point, c: Point) -> float:
    """Calcula el angulo formado por los puntos a, b, c en grados.

    Args:
        a: Punto inicial.
        b: Punto en el vertice del angulo.
        c: Punto final.

    Returns:
        Angulo en grados entre las lineas ab y cb.
    """
    ab = (a[0] - b[0], a[1] - b[1])
    cb = (c[0] - b[0], c[1] - b[1])

    dot = ab[0] * cb[0] + ab[1] * cb[1]
    mag_ab = math.hypot(*ab)
    mag_cb = math.hypot(*cb)

    if mag_ab * mag_cb == 0:
        return 0.0

    cos_angle = max(min(dot / (mag_ab * mag_cb), 1.0), -1.0)
    angle = math.degrees(math.acos(cos_angle))
    return angle

