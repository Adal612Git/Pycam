"""Estimaci\u00f3n simplificada de HRV usando rPPG."""

from __future__ import annotations

import time
from collections import deque
from typing import Deque, Optional

import numpy as np
from scipy.signal import butter, filtfilt, periodogram


class HRVEstimator:
    """Calcula HRV (rPPG) a partir del canal verde de la cara."""

    def __init__(self, fps: int = 30) -> None:
        self.fps = fps
        self.signal: Deque[float] = deque(maxlen=fps * 30)
        self.timestamps: Deque[float] = deque(maxlen=fps * 30)

    def update(self, roi) -> Optional[float]:
        green = roi[:, :, 1].astype("float32")
        self.signal.append(float(np.mean(green)))
        self.timestamps.append(time.time())
        if len(self.signal) < self.fps * 5:
            return None
        sig = np.array(self.signal, dtype="float32")
        ts = np.array(self.timestamps)
        fs = 1.0 / np.mean(np.diff(ts))
        b, a = butter(1, [0.7 / (fs / 2), 4 / (fs / 2)], btype="band")
        filtered = filtfilt(b, a, sig)
        f, pxx = periodogram(filtered, fs)
        if pxx.size == 0:
            return None
        snr = 10 * np.log10(np.max(pxx) / (np.mean(pxx) + 1e-8))
        if snr < 15:
            return None
        diff = np.diff(filtered)
        rmssd = np.sqrt(np.mean(diff ** 2))
        return float(rmssd)
