export interface HRVResult {
  bpm: number;
  hrv: number;
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
    if (this.signal.length < this.fps * 2) return { bpm: 0, hrv: 0 };
    const mean = this.signal.reduce((a, b) => a + b, 0) / this.signal.length;
    const centered = this.signal.map((v) => v - mean);
    const peaks: number[] = [];
    for (let i = 1; i < centered.length - 1; i++) {
      if (centered[i] > centered[i - 1] && centered[i] > centered[i + 1]) {
        peaks.push(i);
      }
    }
    if (peaks.length < 2) return { bpm: 0, hrv: 0 };
    const rr: number[] = [];
    for (let i = 1; i < peaks.length; i++) {
      rr.push((peaks[i] - peaks[i - 1]) / this.fps);
    }
    const rrMean = rr.reduce((a, b) => a + b, 0) / rr.length;
    const bpm = 60 / rrMean;
    const diff: number[] = [];
    for (let i = 1; i < rr.length; i++) {
      diff.push(rr[i] - rr[i - 1]);
    }
    const rmssd = Math.sqrt(diff.reduce((a, b) => a + b * b, 0) / (diff.length || 1)) * 1000;
    return { bpm, hrv: rmssd };
  }

  private static offscreen: HTMLCanvasElement = document.createElement('canvas');
}
