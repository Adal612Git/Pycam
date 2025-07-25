export interface HRVResult {
  bpm: number | null;
  hrv: number | null;
}

function std(arr: number[]): number {
  const m = arr.reduce((a, b) => a + b, 0) / arr.length;
  const v = arr.reduce((a, b) => a + (b - m) * (b - m), 0) / arr.length;
  return Math.sqrt(v);
}

function bandpass(sig: number[], fps: number): number[] {
  // Butterworth coefficients for fps=30, 0.7-3.5 Hz band
  const b = [0.06004382, 0, -0.12008764, 0, 0.06004382];
  const a = [1, -3.02200416, 3.55111471, -1.95868597, 0.43749735];
  const y = new Array(sig.length).fill(0);
  for (let i = 0; i < sig.length; i++) {
    y[i] = b[0] * sig[i];
    if (i >= 1) y[i] += b[1] * sig[i - 1] - a[1] * y[i - 1];
    if (i >= 2) y[i] += b[2] * sig[i - 2] - a[2] * y[i - 2];
    if (i >= 3) y[i] += b[3] * sig[i - 3] - a[3] * y[i - 3];
    if (i >= 4) y[i] += b[4] * sig[i - 4] - a[4] * y[i - 4];
  }
  const out = new Array(sig.length).fill(0);
  for (let i = sig.length - 1; i >= 0; i--) {
    out[i] = b[0] * y[i];
    if (i + 1 < sig.length) out[i] += b[1] * y[i + 1] - a[1] * out[i + 1];
    if (i + 2 < sig.length) out[i] += b[2] * y[i + 2] - a[2] * out[i + 2];
    if (i + 3 < sig.length) out[i] += b[3] * y[i + 3] - a[3] * out[i + 3];
    if (i + 4 < sig.length) out[i] += b[4] * y[i + 4] - a[4] * out[i + 4];
  }
  return out;
}

/**
 * Simple rPPG HRV estimator using the green channel around landmark 10.
 */
export class HRVEstimator {
  private signal: number[] = [];
  constructor(private fps = 30) {}

  update(frame: HTMLVideoElement, landmarks: any[]) {
    if (!landmarks || landmarks.length <= 10) return;
    const w = frame.videoWidth;
    const h = frame.videoHeight;
    const lm = landmarks[10];
    const cx = Math.round(lm.x * w);
    const cy = Math.round(lm.y * h);
    const size = 10;
    const off = HRVEstimator.offscreen;
    if (!off) return;
    off.width = w;
    off.height = h;
    const ctx = off.getContext('2d');
    if (!ctx) return;
    ctx.drawImage(frame, 0, 0, w, h);
    const x1 = Math.max(cx - size, 0);
    const y1 = Math.max(cy - size, 0);
    const width = Math.min(size * 2, w - x1);
    const height = Math.min(size * 2, h - y1);
    const data = ctx.getImageData(x1, y1, width, height).data;
    let sum = 0;
    let count = 0;
    for (let i = 0; i < data.length; i += 4) {
      sum += data[i + 1];
      count++;
    }
    const mean = sum / (count || 1);
    this.signal.push(mean);
    if (this.signal.length > this.fps * 10) this.signal.shift();
  }

  compute(): HRVResult {
    if (this.signal.length < this.fps * 2) return { bpm: null, hrv: null };
    const mean = this.signal.reduce((a, b) => a + b, 0) / this.signal.length;
    const centered = this.signal.map((v) => v - mean);

    const filtered = bandpass(centered, this.fps);

    const N = filtered.length;
    const re: number[] = new Array(Math.floor(N / 2) + 1).fill(0);
    const im: number[] = new Array(Math.floor(N / 2) + 1).fill(0);
    for (let k = 0; k < re.length; k++) {
      for (let n = 0; n < N; n++) {
        const ang = (2 * Math.PI * k * n) / N;
        re[k] += filtered[n] * Math.cos(ang);
        im[k] -= filtered[n] * Math.sin(ang);
      }
    }
    const freqs = re.map((_, i) => (i * this.fps) / N);
    let peakIdx = -1;
    let maxP = -Infinity;
    for (let i = 0; i < freqs.length; i++) {
      if (freqs[i] >= 0.7 && freqs[i] <= 3.5) {
        const p = re[i] * re[i] + im[i] * im[i];
        if (p > maxP) {
          maxP = p;
          peakIdx = i;
        }
      }
    }
    if (peakIdx === -1) return { bpm: null, hrv: null };
    const bpm = freqs[peakIdx] * 60;

    const peaks: number[] = [];
    const thresh = std(filtered) * 0.5;
    for (let i = 1; i < filtered.length - 1; i++) {
      if (
        filtered[i] > filtered[i - 1] &&
        filtered[i] > filtered[i + 1] &&
        filtered[i] > thresh
      ) {
        peaks.push(i);
      }
    }
    if (peaks.length < 3) return { bpm, hrv: null };
    const rr: number[] = [];
    for (let i = 1; i < peaks.length; i++) {
      rr.push((peaks[i] - peaks[i - 1]) / this.fps);
    }
    if (rr.length < 2) return { bpm, hrv: null };
    const diff: number[] = [];
    for (let i = 1; i < rr.length; i++) diff.push(rr[i] - rr[i - 1]);
    const rmssd = Math.sqrt(diff.reduce((a, b) => a + b * b, 0) / diff.length) * 1000;
    return { bpm, hrv: rmssd };
  }

  private static offscreen: HTMLCanvasElement | null =
    typeof window !== 'undefined' && typeof document !== 'undefined'
      ? document.createElement('canvas')
      : null;
}
