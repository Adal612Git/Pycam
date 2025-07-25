"""Modulo de calibracion inicial del sistema PosturaZen usando YOLOv8."""

from __future__ import annotations

import json
import time
from dataclasses import dataclass
from typing import Dict, Tuple, List

import cv2
from ultralytics import YOLO

from PosturaZen.utils.angulos import calcular_angulo


@dataclass
class PosturaBase:
    """Datos de postura de referencia."""

    neck_back_angle: float
    shoulder_hip_angle: float
    center_x: float

    @classmethod
    def from_dict(cls, data: Dict[str, float]) -> "PosturaBase":
        return cls(**data)


KEYPOINT_INDEX = {
    "left_shoulder": 5,
    "right_shoulder": 6,
    "left_hip": 11,
    "right_hip": 12,
    "nose": 0,
}


class Calibrador:
    """Realiza la calibracion inicial capturando la postura ideal."""

    def __init__(self, segundos: int = 10, fps: int = 30) -> None:
        self.segundos = segundos
        self.fps = fps
        self.model = YOLO("yolov8n-pose.pt")

    def _obtener_puntos(self, frame) -> Dict[str, Tuple[float, float]]:
        resultados = self.model(frame, verbose=False)[0]
        if resultados.keypoints is None or len(resultados.keypoints) == 0:
            return {}
        kp = resultados.keypoints.xyn[0]
        puntos = {n: (float(kp[idx][0]), float(kp[idx][1])) for n, idx in KEYPOINT_INDEX.items()}
        return puntos

    def calibrar(self) -> PosturaBase:
        print("Si\u00e9ntate bien por 10 segundos para calibrar")
        cap = cv2.VideoCapture(0)

        start_time = time.time()
        buenos_frames: List[float] = []
        angulos_cuello: List[float] = []
        angulos_cadera: List[float] = []
        centros_x: List[float] = []

        while True:
            ret, frame = cap.read()
            if not ret:
                continue
            puntos = self._obtener_puntos(frame)
            if len(puntos) == len(KEYPOINT_INDEX):
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

        if len(buenos_frames) < self.segundos * self.fps * 0.5:
            print("No se detect\u00f3 suficiente visibilidad. Reiniciando calibraci\u00f3n...")
            return self.calibrar()

        promedio = PosturaBase(
            neck_back_angle=sum(angulos_cuello) / len(angulos_cuello),
            shoulder_hip_angle=sum(angulos_cadera) / len(angulos_cadera),
            center_x=sum(centros_x) / len(centros_x),
        )
        with open("PosturaZen/postura_base.json", "w", encoding="utf-8") as f:
            json.dump(promedio.__dict__, f, indent=4)
        return promedio
