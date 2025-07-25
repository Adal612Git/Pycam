# PosturaZen

Sistema de correcci\u00f3n de postura compatible con **Python 3.13**.
Se basa en `ultralytics` (YOLOv8 pose) y `opencv-python` para
la detecci\u00f3n esquel\u00e9tica. No requiere `mediapipe`.

## Requisitos
- Python 3.13+
- Webcam disponible

## Instalaci\u00f3n
```bash
pip install -r requirements.txt
```

## Uso
```bash
python main.py
```
El sistema se calibrar\u00e1 por 10 segundos y luego comenzar\u00e1 la detecci\u00f3n
y el c\u00e1lculo de HRV.
