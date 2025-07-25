"""Punto de entrada para PosturaZen."""

import os

from calibracion.calibrador import Calibrador, PosturaBase
from deteccion.detector import Detector, cargar_postura

BASE_PATH = os.path.join(os.path.dirname(__file__), "postura_base.json")


def main() -> None:
    if not os.path.exists(BASE_PATH):
        calibrador = Calibrador()
        postura_base = calibrador.calibrar()
    else:
        postura_base = cargar_postura(BASE_PATH)

    no_molestar = os.environ.get("POSTURAZEN_SILENCIO", "0") == "1"
    detector = Detector(postura_base, no_molestar=no_molestar)
    detector.detectar()


if __name__ == "__main__":
    main()
