"""Modulo de retroalimentaci\u00f3n por voz."""

from __future__ import annotations

import datetime

import pyttsx3

_engine = pyttsx3.init()


def decir(texto: str, no_molestar: bool = False) -> None:
    volumen = 1.0
    hora = datetime.datetime.now().hour
    if no_molestar and 9 <= hora <= 17:
        volumen = 0.3
    _engine.setProperty("volume", volumen)
    _engine.say(texto)
    _engine.runAndWait()
