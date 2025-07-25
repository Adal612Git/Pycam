"""Modulo de deteccion de postura utilizando los datos de calibracion."""

from __future__ import annotations

import json
import time
import hashlib
from collections import deque
from typing import Deque, Dict

import cv2
import mediapipe as mp

from ..utils.angulos import calcular_angulo
from ..calibracion.calibrador import PosturaBase


mp_pose = mp.solutions.pose


class Detector:
    """Detecta postura en tiempo real basandose en la calibracion."""

    def __init__(self, postura_base: PosturaBase, fps: int = 30) -> None:
        self.postura_base = postura_base
        self.fps = fps
        self.window: Deque[bool] = deque(maxlen=fps * 5)

    def _obtener_puntos(self, resultados) -> Dict[str, tuple]:
        puntos = {}
        ids = [
            mp_pose.PoseLandmark.LEFT_SHOULDER,
            mp_pose.PoseLandmark.RIGHT_SHOULDER,
            mp_pose.PoseLandmark.LEFT_HIP,
            mp_pose.PoseLandmark.RIGHT_HIP,
            mp_pose.PoseLandmark.NOSE,
        ]
        nombres = [
            "left_shoulder",
            "right_shoulder",
            "left_hip",
            "right_hip",
            "nose",
        ]
        for nombre, idx in zip(nombres, ids):
            landmark = resultados.pose_landmarks.landmark[idx]
            puntos[nombre] = (landmark.x, landmark.y, landmark.visibility)
        return puntos

    def detectar(self) -> None:
        cap = cv2.VideoCapture(0)
        pose = mp_pose.Pose()

        while True:
            ret, frame = cap.read()
            if not ret:
                continue

            # Hash SHA-256 para verificar que no se almacena la imagen
            frame_bytes = frame.tobytes()
            hash_hex = hashlib.sha256(frame_bytes).hexdigest()
            print(f"Frame hash: {hash_hex}")

            image_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            resultados = pose.process(image_rgb)
            if not resultados.pose_landmarks:
                continue
            puntos = self._obtener_puntos(resultados)
            if not all(puntos[n][2] > 0.7 for n in puntos):
                continue

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
            centro_x = hip_mid[0]

            dif_cuello = abs(angulo_cuello - self.postura_base.neck_back_angle)
            dif_cadera = abs(angulo_cadera - self.postura_base.shoulder_hip_angle)
            dif_centro = abs(centro_x - self.postura_base.center_x)

            mala_postura = dif_cuello > 10 or dif_cadera > 10 or dif_centro > 0.1
            self.window.append(mala_postura)
            if len(self.window) == self.window.maxlen and all(self.window):
                print("⚠️ Postura incorrecta")

            key = cv2.waitKey(1)
            if key & 0xFF == ord("q"):
                break

        cap.release()
        pose.close()
        cv2.destroyAllWindows()


def cargar_postura(path: str = "PosturaZen/postura_base.json") -> PosturaBase:
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return PosturaBase.from_dict(data)

