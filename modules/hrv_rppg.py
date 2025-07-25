"""Real-time HRV and BPM estimation using rPPG.

This module uses a simple green channel approach over the
forehead region to compute heart rate variability (HRV)
and beats per minute (BPM) from a video stream.
"""

from __future__ import annotations

from collections import deque
from typing import Any, Sequence, Deque, Dict

import cv2
import numpy as np
from scipy.signal import butter, filtfilt, find_peaks


Point = Sequence[float]


def _to_point(landmark: Any) -> Point:
    """Converts a flexible landmark object to an ``(x, y)`` tuple."""
    if hasattr(landmark, "x") and hasattr(landmark, "y"):
        return float(landmark.x), float(landmark.y)
    return float(landmark[0]), float(landmark[1])


class HRVEstimator:
    """Estimates BPM and HRV (RMSSD) from face video frames."""

    def __init__(self, fps: int = 30) -> None:
        self.fps = fps
        self.signal: Deque[float] = deque(maxlen=300)

    def update(self, frame: np.ndarray, landmarks: Sequence[Any]) -> None:
        """Update the internal green channel signal with the forehead ROI."""
        if len(landmarks) <= 10:
            return
        h, w = frame.shape[:2]
        x, y = _to_point(landmarks[10])
        cx, cy = int(x * w), int(y * h)
        size = 10
        x1, x2 = max(cx - size, 0), min(cx + size, w)
        y1, y2 = max(cy - size, 0), min(cy + size, h)
        roi = frame[y1:y2, x1:x2]
        if roi.size == 0:
            return
        green = roi[:, :, 1].astype(np.float32)
        mean_val = float(np.mean(green))
        self.signal.append(mean_val)

    def compute(self) -> Dict[str, float]:
        """Compute BPM and HRV from the stored signal."""
        if len(self.signal) < self.fps * 2:
            return {"bpm": 0.0, "hrv": 0.0}

        sig = np.array(self.signal, dtype=np.float32)
        sig = sig - np.mean(sig)
        fs = self.fps
        b, a = butter(2, [0.7 / (fs / 2), 4 / (fs / 2)], btype="band")
        filtered = filtfilt(b, a, sig)

        peaks, _ = find_peaks(filtered, distance=int(fs * 0.25))
        if len(peaks) < 2:
            return {"bpm": 0.0, "hrv": 0.0}

        rr = np.diff(peaks) / fs
        bpm = 60.0 / np.mean(rr)
        diff_rr = np.diff(rr)
        rmssd = np.sqrt(np.mean(diff_rr ** 2)) * 1000.0  # ms
        return {"bpm": float(bpm), "hrv": float(rmssd)}

