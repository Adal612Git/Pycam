<script context="module" lang="ts">
export const ssr = false;
</script>

<script lang="ts">
import { onMount } from 'svelte';
import { calibrate } from '$lib/pose/calibrate';
import { PostureDetector } from '$lib/pose/detector';

let video: HTMLVideoElement;
let message = 'Siéntate bien por 10 segundos para calibrar tu postura ideal';
let detector: PostureDetector | null = null;
let calibrated = false;

onMount(async () => {
    const posePkg = await import('@mediapipe/pose');
    const { Pose } = posePkg;
    const camPkg = await import('@mediapipe/camera_utils');
    const { Camera } = camPkg;

    const pose = new Pose({
        locateFile: (file: string) => `https://cdn.jsdelivr.net/npm/@mediapipe/pose/${file}`
    });
    pose.setOptions({ modelComplexity: 0, selfieMode: true });

    const camera = new Camera(video, { onFrame: async () => {} });
    await camera.start();

    const calib = await calibrate(pose, video);
    calibrated = true;
    message = 'Postura calibrada. Monitoreando...';
    detector = new PostureDetector(pose, calib);
    detector.onAlert(() => speak('Por favor, corrige tu postura'));
    detector.start(video);
});

function speak(text: string) {
    const utter = new SpeechSynthesisUtterance(text);
    speechSynthesis.speak(utter);
}
</script>

<video bind:this={video} style="display:none"><track kind="captions" /></video>
<h1>{message}</h1>
