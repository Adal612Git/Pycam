"""Modulo de deteccion de postura utilizando los datos de calibracion."""

from __future__ import annotations

import json
import time
import hashlib
from collections import deque
from typing import Deque, Dict

import cv2
from ultralytics import YOLO

from ..utils.angulos import calcular_angulo
from ..utils.hrv import HRVEstimator
from ..voz.feedback import decir
from ..calibracion.calibrador import PosturaBase


KEYPOINT_INDEX = {
    "left_shoulder": 5,
    "right_shoulder": 6,
    "left_hip": 11,
    "right_hip": 12,
    "nose": 0,
}


class Detector:
    """Detecta postura en tiempo real bas\u00e1ndose en la calibraci\u00f3n."""

    def __init__(self, postura_base: PosturaBase, fps: int = 30, no_molestar: bool = False) -> None:
        self.postura_base = postura_base
        self.fps = fps
        self.no_molestar = no_molestar
        self.window: Deque[bool] = deque(maxlen=fps * 5)
        self.model = YOLO("yolov8n-pose.pt")
        self.hrv = HRVEstimator(fps)
        self.alertas = 0
        self.buenos_frames = 0

    def _obtener_puntos(self, frame) -> Dict[str, tuple]:
        resultados = self.model(frame, verbose=False)[0]
        if resultados.keypoints is None or len(resultados.keypoints) == 0:
            return {}
        kp = resultados.keypoints.xyn[0]
        puntos = {n: (float(kp[idx][0]), float(kp[idx][1])) for n, idx in KEYPOINT_INDEX.items()}
        return puntos

    def detectar(self) -> None:
        cap = cv2.VideoCapture(0)
        face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")

        while True:
            ret, frame = cap.read()
            if not ret:
                continue

            frame_bytes = frame.tobytes()
            hash_hex = hashlib.sha256(frame_bytes).hexdigest()
            print(f"Frame hash: {hash_hex}")

            puntos = self._obtener_puntos(frame)
            if len(puntos) != len(KEYPOINT_INDEX):
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
            if mala_postura:
                self.buenos_frames = 0
            else:
                self.buenos_frames += 1

            if len(self.window) == self.window.maxlen and all(self.window):
                self.alertas += 1
                decir("Cuidado con tu postura", self.no_molestar)
                print("\u26a0\ufe0f Postura incorrecta")

            if self.buenos_frames >= self.fps * 60 * 10:
                self.buenos_frames = 0
                decir("Excelente postura, sigue asi", self.no_molestar)

            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            faces = face_cascade.detectMultiScale(gray, 1.3, 5)
            hrv_val = None
            for (x, y, w, h) in faces[:1]:
                roi = frame[y : y + h, x : x + w]
                hrv_val = self.hrv.update(roi)
            estado = "\u2705" if not mala_postura else "\u26a0\ufe0f"
            mensaje = f"Postura: {estado} | Alertas: {self.alertas}"
            if hrv_val is not None:
                mensaje += f" | HRV: {hrv_val:.2f}"
            print(mensaje)

            if cv2.waitKey(1) & 0xFF == ord("q"):
                break

        cap.release()
        cv2.destroyAllWindows()


def cargar_postura(path: str = "PosturaZen/postura_base.json") -> PosturaBase:
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return PosturaBase.from_dict(data)
