"""Modulo de retroalimentaci\u00f3n por voz."""

from __future__ import annotations

import datetime

import pyttsx3

_engine = pyttsx3.init()
_engine.setProperty("rate", 165)
for voice in _engine.getProperty("voices"):
    if "spanish" in voice.name.lower() or "es_" in voice.id.lower():
        _engine.setProperty("voice", voice.id)
        break

# Indica si ya se emitió una alerta por movimiento reciente
alerta_movimiento_activa = False


def speak(text: str) -> None:
    """Pronuncia ``text`` en voz alta usando una voz en español."""
    _engine.say(text)
    _engine.runAndWait()


def decir(texto: str, no_molestar: bool = False) -> None:
    volumen = 1.0
    hora = datetime.datetime.now().hour
    if no_molestar and 9 <= hora <= 17:
        volumen = 0.3
    _engine.setProperty("volume", volumen)
    _engine.say(texto)
    _engine.runAndWait()
