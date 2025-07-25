"""Modulo de calibracion inicial del sistema PosturaZen."""

from __future__ import annotations

import json
import time
from dataclasses import dataclass
from typing import Dict, Tuple, List

import cv2
import mediapipe as mp

from ..utils.angulos import calcular_angulo


mp_pose = mp.solutions.pose


@dataclass
class PosturaBase:
    """Datos de postura de referencia."""

    neck_back_angle: float
    shoulder_hip_angle: float
    center_x: float

    @classmethod
    def from_dict(cls, data: Dict[str, float]) -> "PosturaBase":
        return cls(**data)


LANDMARKS = {
    "left_shoulder": mp_pose.PoseLandmark.LEFT_SHOULDER,
    "right_shoulder": mp_pose.PoseLandmark.RIGHT_SHOULDER,
    "left_hip": mp_pose.PoseLandmark.LEFT_HIP,
    "right_hip": mp_pose.PoseLandmark.RIGHT_HIP,
    "nose": mp_pose.PoseLandmark.NOSE,
}


class Calibrador:
    """Realiza la calibracion inicial capturando la postura ideal."""

    def __init__(self, segundos: int = 10, fps: int = 30) -> None:
        self.segundos = segundos
        self.fps = fps

    def _obtener_puntos(self, resultados) -> Dict[str, Tuple[float, float, float]]:
        puntos = {}
        for nombre, idx in LANDMARKS.items():
            landmark = resultados.pose_landmarks.landmark[idx]
            puntos[nombre] = (landmark.x, landmark.y, landmark.visibility)
        return puntos

    def calibrar(self) -> PosturaBase:
        print("Siéntate bien por 10 segundos para calibrar")
        cap = cv2.VideoCapture(0)
        pose = mp_pose.Pose()

        start_time = time.time()
        buenos_frames: List[float] = []
        angulos_cuello: List[float] = []
        angulos_cadera: List[float] = []
        centros_x: List[float] = []

        while True:
            ret, frame = cap.read()
            if not ret:
                continue
            image_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            resultados = pose.process(image_rgb)
            if not resultados.pose_landmarks:
                continue
            puntos = self._obtener_puntos(resultados)
            if all(puntos[n][2] > 0.7 for n in puntos):
                shoulder_mid = (
                    (puntos["left_shoulder"][0] + puntos["right_shoulder"][0]) / 2,
                    (puntos["left_shoulder"][1] + puntos["right_shoulder"][1]) / 2,
                )
                hip_mid = (
                    (puntos["left_hip"][0] + puntos["right_hip"][0]) / 2,
                    (puntos["left_hip"][1] + puntos["right_hip"][1]) / 2,
                )
                nose = (puntos["nose"][0], puntos["nose"][1])

                angulo_cuello = calcular_angulo(nose, shoulder_mid, hip_mid)
                angulo_cadera = calcular_angulo(shoulder_mid, hip_mid, (hip_mid[0], hip_mid[1] + 0.1))
                angulos_cuello.append(angulo_cuello)
                angulos_cadera.append(angulo_cadera)
                centros_x.append(hip_mid[0])
                buenos_frames.append(1)

            if time.time() - start_time >= self.segundos:
                break

        cap.release()
        pose.close()

        if len(buenos_frames) < self.segundos * self.fps * 0.5:
            print("No se detectó suficiente visibilidad. Reiniciando calibración...")
            return self.calibrar()

        promedio = PosturaBase(
            neck_back_angle=sum(angulos_cuello) / len(angulos_cuello),
            shoulder_hip_angle=sum(angulos_cadera) / len(angulos_cadera),
            center_x=sum(centros_x) / len(centros_x),
        )
        with open("PosturaZen/postura_base.json", "w", encoding="utf-8") as f:
            json.dump(promedio.__dict__, f, indent=4)
        return promedio


