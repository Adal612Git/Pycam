import type { Pose, Results } from '@mediapipe/pose';
import { neckBackAngle, shoulderHipAngle, Point3D } from './angles';
import type { CalibrationData } from './calibrate';
import { ToleranceWindow } from './tolerance';
import { detectBalance } from './balance';

export interface DetectorOptions {
    toleranceMs?: number;
}

export class PostureDetector {
    private lastResults: Results | null = null;
    private tolerance: ToleranceWindow;
    private listeners: Array<(bad: boolean) => void> = [];

    constructor(private pose: Pose, private calib: CalibrationData, opts: DetectorOptions = {}) {
        this.tolerance = new ToleranceWindow(opts.toleranceMs ?? 5000);
    }

    onAlert(cb: (bad: boolean) => void) {
        this.listeners.push(cb);
    }

    start(video: HTMLVideoElement) {
        this.pose.onResults((res) => this.handleResults(res));
        const loop = async () => {
            await this.pose.send({ image: video });
            requestAnimationFrame(loop);
        };
        loop();
    }

    private handleResults(res: Results) {
        const lms = res.poseLandmarks;
        if (!lms) return;
        const needed = [lms[11], lms[12], lms[23], lms[24]];
        const visible = needed.every((p) => (p.visibility ?? 1) > 0.7);
        if (!visible) return;
        const ear = (lms[7]?.visibility ?? 1) > 0.7 ? lms[7] : (lms[8]?.visibility ?? 1) > 0.7 ? lms[8] : null;
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
        const badPosture = Math.abs(neckAngle - this.calib.neckBack) > 0.15 || Math.abs(hipAngle - this.calib.shoulderHip) > 0.15;
        const swaying = detectBalance(res, this.lastResults);
        const alert = this.tolerance.update(badPosture || swaying);
        if (alert) this.listeners.forEach((l) => l(true));
        this.lastResults = res;
    }
}
