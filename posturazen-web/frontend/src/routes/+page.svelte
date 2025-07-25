<script lang="ts">
import { onMount } from 'svelte';
import { Pose } from '@mediapipe/pose';
import { calibrate, type CalibrationData } from '$lib/pose/calibrate';
import { PostureDetector } from '$lib/pose/detector';

let video: HTMLVideoElement;
let message = 'Siéntate bien por 10 segundos para calibrar tu postura ideal';
let detector: PostureDetector | null = null;
let calibrated = false;

onMount(async () => {
    const stream = await navigator.mediaDevices.getUserMedia({ video: true });
    video.srcObject = stream;
    await video.play();

    const pose = new Pose({ locateFile: (f) => `https://cdn.jsdelivr.net/npm/@mediapipe/pose/${f}` });
    pose.setOptions({ modelComplexity: 0, selfieMode: true });

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
