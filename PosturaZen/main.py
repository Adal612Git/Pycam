"""Punto de entrada para PosturaZen."""

import os

from PosturaZen.deteccion.detector import Detector, cargar_postura

BASE_PATH = os.path.join(os.path.dirname(__file__), "postura_base.json")


def main() -> None:
    """Ejecuta la detección de postura asegurando calibración válida."""

    # Cargar la calibración o generar una de prueba si es necesario
    postura_base = cargar_postura(BASE_PATH)

    no_molestar = os.environ.get("POSTURAZEN_SILENCIO", "0") == "1"
    detector = Detector(postura_base, no_molestar=no_molestar)
    detector.detectar()


if __name__ == "__main__":
    main()
