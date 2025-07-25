"""Funciones de analisis avanzado de postura para PosturaZen v2.0."""

from __future__ import annotations

import math
from typing import Iterable, Sequence, Dict, Any, List

import cv2
import numpy as np


# Tipo generico para un punto (x, y)
Point = Sequence[float]


def _to_point(landmark: Any) -> Point:
    """Extrae coordenadas (x, y) de un landmark flexible."""
    if hasattr(landmark, "x") and hasattr(landmark, "y"):
        return float(landmark.x), float(landmark.y)
    return float(landmark[0]), float(landmark[1])


def calculate_head_inclination(frame, landmarks) -> float:
    """Calcular la inclinación de la cabeza y dibujar la visualización.

    Args:
        frame: Imagen BGR del frame actual.
        landmarks: Lista o secuencia de landmarks faciales.

    Returns:
        Ángulo de inclinación respecto a la vertical en grados.
    """
    if len(landmarks) <= 152:
        return 0.0

    h, w = frame.shape[:2]
    forehead = _to_point(landmarks[10])
    chin = _to_point(landmarks[152])
    p1 = (int(forehead[0] * w), int(forehead[1] * h))
    p2 = (int(chin[0] * w), int(chin[1] * h))

    cv2.line(frame, p1, p2, (0, 255, 0), 2)
    cv2.circle(frame, p1, 4, (0, 0, 255), -1)
    cv2.circle(frame, p2, 4, (0, 0, 255), -1)

    dx = p2[0] - p1[0]
    dy = p2[1] - p1[1]
    angle = math.degrees(math.atan2(dx, dy))
    abs_angle = abs(angle)

    if abs_angle <= 5:
        estado = "Correcto"
    elif abs_angle <= 15:
        estado = "Leve inclinación"
    else:
        estado = "Incorrecto"

    cv2.putText(
        frame,
        f"Inclinación: {angle:.1f}° {estado}",
        (10, 30),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.7,
        (0, 255, 0),
        2,
    )
    return float(angle)


def estimate_user_distance(frame, landmarks, focal_length_pixels: float = 800.0) -> float:
    """Estimar la distancia del usuario a la cámara en centímetros.

    Args:
        frame: Frame actual en formato BGR.
        landmarks: Landmarks faciales detectados.
        focal_length_pixels: Focal estimada de la cámara en píxeles.

    Returns:
        Distancia estimada en centímetros.
    """
    if len(landmarks) <= 263:
        return 0.0

    h, w = frame.shape[:2]
    left_eye = _to_point(landmarks[33])
    right_eye = _to_point(landmarks[263])
    p1 = (int(left_eye[0] * w), int(left_eye[1] * h))
    p2 = (int(right_eye[0] * w), int(right_eye[1] * h))

    measured = math.hypot(p2[0] - p1[0], p2[1] - p1[1])
    known_eye_distance_cm = 6.3
    distance_cm = (known_eye_distance_cm * focal_length_pixels) / max(measured, 1e-6)

    cv2.putText(
        frame,
        f"Distancia estimada: {distance_cm:.1f} cm",
        (10, 60),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.7,
        (255, 255, 255),
        2,
    )
    return float(distance_cm)


def is_posture_stable(past_landmarks: Iterable[Sequence[Any]], current_landmarks: Sequence[Any], threshold: float = 5) -> bool:
    """Determina si la cabeza se ha mantenido estable durante varios frames.

    Args:
        past_landmarks: Secuencia de landmarks de frames previos.
        current_landmarks: Landmarks del frame actual.
        threshold: Desplazamiento máximo permitido en píxeles.

    Returns:
        ``True`` si la posición del landmark 10 cambia menos de ``threshold``
        píxeles entre todos los frames, ``False`` en caso contrario.
    """
    if not past_landmarks:
        return False

    prev_point = _to_point(current_landmarks[10])
    for lms in reversed(list(past_landmarks)):
        point = _to_point(lms[10])
        if math.hypot(point[0] - prev_point[0], point[1] - prev_point[1]) > threshold:
            return False
        prev_point = point
    return True


def extract_rppg_signal(frames: Sequence[Any], landmarks: Sequence[Sequence[Any]], fps: int = 30) -> Dict[str, float]:
    """Extrae una señal rPPG básica para estimar BPM y HRV.

    Args:
        frames: Lista de frames (BGR) correspondientes a ``landmarks``.
        landmarks: Landmarks faciales por frame.
        fps: Tasa de cuadros por segundo de la captura.

    Returns:
        Diccionario con ``bpm`` y ``hrv`` aproximados.
    """
    vals: List[float] = []
    for frame, lms in zip(frames, landmarks):
        if len(lms) <= 10:
            continue
        h, w = frame.shape[:2]
        pt = _to_point(lms[10])
        x = int(pt[0] * w)
        y = int(pt[1] * h)
        size = 10
        x1, x2 = max(x - size, 0), min(x + size, w)
        y1, y2 = max(y - size, 0), min(y + size, h)
        roi = frame[y1:y2, x1:x2]
        if roi.size == 0:
            continue
        vals.append(float(np.mean(roi[:, :, 1])))

    if len(vals) < fps:
        return {"bpm": 0.0, "hrv": 0.0}

    sig = np.array(vals, dtype=np.float32)
    sig = sig - np.mean(sig)
    freqs = np.fft.rfftfreq(len(sig), d=1.0 / fps)
    fft = np.abs(np.fft.rfft(sig))
    idx = np.where((freqs >= 0.75) & (freqs <= 3.0))[0]
    if idx.size == 0:
        bpm = 0.0
    else:
        peak = idx[np.argmax(fft[idx])]
        bpm = float(freqs[peak] * 60.0)

    diff = np.diff(sig)
    hrv = float(np.sqrt(np.mean(diff ** 2))) if diff.size > 0 else 0.0

    return {"bpm": bpm, "hrv": hrv}
