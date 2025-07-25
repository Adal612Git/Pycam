<script context="module" lang="ts">
  export const ssr = false;
</script>

<script lang="ts">
import { onMount } from 'svelte';
let pose: any, camera: any;
let videoElement: HTMLVideoElement, canvasElement: HTMLCanvasElement;

onMount(async () => {
  const posePkg = await import('@mediapipe/pose');
  const { Pose } = posePkg;
  const camPkg = await import('@mediapipe/camera_utils');
  const { Camera } = camPkg;

  pose = new Pose({ locateFile: f => `https://cdn.jsdelivr.net/npm/@mediapipe/pose/${f}` });
  pose.setOptions({ modelComplexity: 1, smoothLandmarks: true });
  pose.onResults((results: any) => {
    // lógica de dibujo en canvas
  });

  camera = new Camera(videoElement, {
    onFrame: async () => await pose.send({ image: videoElement }),
    width: 640,
    height: 480
  });
  camera.start();
});
</script>

<video bind:this={videoElement}></video>
<canvas bind:this={canvasElement}></canvas>
