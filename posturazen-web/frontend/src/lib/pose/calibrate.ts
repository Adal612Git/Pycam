import type { Pose, Results } from '@mediapipe/pose';
import { neckBackAngle, shoulderHipAngle, Point3D } from './angles';

export interface CalibrationData {
    neckBack: number;
    shoulderHip: number;
}

function visible(lm: any, min = 0.7) {
    return lm && (lm.visibility ?? 1) > min;
}

export async function calibrate(pose: Pose, video: HTMLVideoElement): Promise<CalibrationData> {
    const neckAngles: number[] = [];
    const hipAngles: number[] = [];

    return new Promise((resolve) => {
        const start = performance.now();

        function onResults(results: Results) {
            const lms = results.poseLandmarks;
            if (!lms) return;
            const needed = [lms[11], lms[12], lms[23], lms[24]]; // shoulders and hips
            if (!needed.every((p) => visible(p))) return;
            const ear = visible(lms[7]) ? lms[7] : visible(lms[8]) ? lms[8] : null;
            if (!ear) return;
            const shoulderMid: Point3D = {
                x: (lms[11].x + lms[12].x) / 2,
                y: (lms[11].y + lms[12].y) / 2,
                z: (lms[11].z + lms[12].z) / 2
            };
            const hipMid: Point3D = {
                x: (lms[23].x + lms[24].x) / 2,
                y: (lms[23].y + lms[24].y) / 2,
                z: (lms[23].z + lms[24].z) / 2
            };
            const neck = { x: ear.x, y: ear.y, z: ear.z };
            const neckAngle = neckBackAngle([shoulderMid, neck, hipMid]);
            const hipAngle = shoulderHipAngle(lms[11], lms[12], lms[23], lms[24]);
            neckAngles.push(neckAngle);
            hipAngles.push(hipAngle);
            if (performance.now() - start >= 10000) {
                pose.removeListener('results', onResults);
                resolve({
                    neckBack: neckAngles.reduce((a, b) => a + b, 0) / neckAngles.length,
                    shoulderHip: hipAngles.reduce((a, b) => a + b, 0) / hipAngles.length
                });
            }
        }

        pose.onResults(onResults);

        const capture = async () => {
            await pose.send({ image: video });
            if (performance.now() - start < 10000) requestAnimationFrame(capture);
        };
        capture();
    });
}
