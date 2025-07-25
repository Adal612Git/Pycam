import type { Results } from '@mediapipe/pose';

export function detectBalance(results: Results, last: Results | null, thresholdCm = 0.03): boolean {
    if (!last || !results.poseLandmarks || !last.poseLandmarks) return false;
    const lm = results.poseLandmarks;
    const prev = last.poseLandmarks;
    const leftShoulder = lm[11];
    const rightShoulder = lm[12];
    const leftHip = lm[23];
    const rightHip = lm[24];
    if (!leftShoulder || !rightShoulder || !leftHip || !rightHip) return false;
    const currX = (leftShoulder.x + rightShoulder.x + leftHip.x + rightHip.x) / 4;
    const prevX = (prev[11].x + prev[12].x + prev[23].x + prev[24].x) / 4;
    return Math.abs(currX - prevX) > thresholdCm;
}
