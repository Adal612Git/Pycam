# PosturaZen

Sistema de detección de postura utilizando MediaPipe y OpenCV.

## Requisitos
- Python 3.10 a 3.12
- Webcam disponible

> **Nota sobre Python 3.13**
>
> Actualmente `mediapipe`, la dependencia principal del proyecto, no
> distribuye ruedas para Python 3.13. Para evitar errores al instalar los
> requisitos, se recomienda utilizar Python 3.10, 3.11 o 3.12. Cuando el
> paquete proporcione soporte oficial para Python 3.13 se actualizará la
> compatibilidad de PosturaZen.

## Instalación
```bash
pip install -r requirements.txt
```

## Uso
```bash
python main.py
```
El sistema se calibrará por 10 segundos y luego comenzará la detección.

