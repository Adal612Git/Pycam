<script context="module" lang="ts">
  export const ssr = false;
</script>

<script lang="ts">
  import { onMount } from 'svelte';
  import { neckBackAngle, shoulderHipAngle } from '$lib/pose/angles';
  import { HRVEstimator } from '$lib/pose/hrv';
  import { speak } from '$lib/voice';

  let pose: any;
  let videoElement: HTMLVideoElement;
  let canvasElement: HTMLCanvasElement;
  let canvasCtx: CanvasRenderingContext2D;

  let countdown = 10;
  let message = 'Calibrando… espera 10s';
  let calibrating = true;
  let errorMessage: string | null = null;

  let baselineNeck = 0;
  let baselineHip = 0;
  let totalNeck = 0;
  let totalHip = 0;
  let totalCount = 0;

  let frames = 0;
  let neckAngle = 0;
  let hipAngle = 0;
  let visibility = 0;
  let posture = '';

  let bpm: number | null = null;
  let hrvValue: number | null = null;
  let hrvEstimator: HRVEstimator;

  let badStart: number | null = null;
  let showWarning = false;
  let lastNose: {x: number, y: number} | null = null;
  let stableFrames = 0;
  let movementAlertActive = false;
  let warningVoiceActive = false;

  onMount(() => {
    const timer = setInterval(() => {
      countdown--;
      message = `Calibrando… espera ${Math.max(countdown, 0)}s`;

      if (countdown <= 0) {
        clearInterval(timer);
        if (!errorMessage) {
          calibrating = false;
          message = 'Monitoreando tu postura';
          baselineNeck = totalNeck / (totalCount || 1);
          baselineHip = totalHip / (totalCount || 1);
        }
      }
    }, 1000);

    initPose();
  });

  async function initPose() {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ video: true });
      videoElement.srcObject = stream;
      await videoElement.play();

      const posePkg = await import('https://cdn.jsdelivr.net/npm/@mediapipe/pose');
      const { Pose } = posePkg;

      pose = new Pose({ locateFile: (f: string) => `https://cdn.jsdelivr.net/npm/@mediapipe/pose/${f}` });
      pose.setOptions({ modelComplexity: 1, smoothLandmarks: true });
      pose.onResults(handleResults);

      hrvEstimator = new HRVEstimator(30);

      canvasCtx = canvasElement.getContext('2d') as CanvasRenderingContext2D;

      startProcessing();
    } catch (err) {
      console.error(err);
      errorMessage = 'Error al acceder a la cámara o cargar la librería';
    }
  }

  function startProcessing() {
    const loop = async () => {
      await pose.send({ image: videoElement });
      requestAnimationFrame(loop);
    };
    loop();
  }

  function handleResults(results: any) {
    const lms = results.poseLandmarks;
    if (!lms) return;

    visibility = +(lms.reduce((s: number, p: any) => s + (p.visibility ?? 1), 0) / lms.length * 100).toFixed(1);

    const shoulderMid = {
      x: (lms[11].x + lms[12].x) / 2,
      y: (lms[11].y + lms[12].y) / 2,
      z: (lms[11].z + lms[12].z) / 2
    };
    const hipMid = {
      x: (lms[23].x + lms[24].x) / 2,
      y: (lms[23].y + lms[24].y) / 2,
      z: (lms[23].z + lms[24].z) / 2
    };
    const ear = (lms[7]?.visibility ?? 1) > 0.7 ? lms[7] : lms[8];
    const neck = { x: ear.x, y: ear.y, z: ear.z };

    const nose = lms[0];
    if (lastNose) {
      const dist = Math.hypot(nose.x - lastNose.x, nose.y - lastNose.y);
      const stable = dist < 0.02;
      if (stable) {
        stableFrames++;
        if (movementAlertActive && stableFrames > 60) {
          movementAlertActive = false;
        }
      } else {
        stableFrames = 0;
        if (!movementAlertActive) {
          speak('Detecté movimiento. Recuerda mantener tu postura alineada.');
          movementAlertActive = true;
        }
      }
    }
    lastNose = { x: nose.x, y: nose.y };

    neckAngle = +(neckBackAngle([shoulderMid, neck, hipMid]) * (180 / Math.PI)).toFixed(1);
    hipAngle = +(shoulderHipAngle(lms[11], lms[12], lms[23], lms[24]) * (180 / Math.PI)).toFixed(1);

    hrvEstimator.update(videoElement, lms);

    if (calibrating) {
      totalNeck += neckAngle;
      totalHip += hipAngle;
      totalCount++;
    } else {
      frames++;
      if (frames % 30 === 0) {
        const data = hrvEstimator.compute();
        bpm = data.bpm;
        hrvValue = data.hrv;
        if (hrvValue && hrvValue < 25) {
          alert('¡Alerta de estrés fisiológico!');
        }
      }
      const diff1 = Math.abs(neckAngle - baselineNeck);
      const diff2 = Math.abs(hipAngle - baselineHip);
      const incorrect = diff1 > 10 || diff2 > 10;

      if (incorrect) {
        posture = '⚠️ Incorrecta';
        if (badStart === null) badStart = Date.now();
        showWarning = Date.now() - (badStart ?? 0) >= 3000;
        if (showWarning && !warningVoiceActive) {
          speak('Tu postura no es correcta. Enderézate, por favor.');
          warningVoiceActive = true;
        }
      } else {
        posture = 'Correcta';
        badStart = null;
        showWarning = false;
        warningVoiceActive = false;
      }

      drawCanvas(incorrect);
    }
  }

  function drawCanvas(bad: boolean) {
    canvasCtx.save();
    canvasCtx.clearRect(0, 0, canvasElement.width, canvasElement.height);
    canvasCtx.lineWidth = 5;
    canvasCtx.strokeStyle = bad ? '#ff3333' : '#33ff77';
    canvasCtx.strokeRect(0, 0, canvasElement.width, canvasElement.height);
    canvasCtx.restore();
  }
</script>

<div class="container">
  <header>
    <h1>PosturaZen Web v2.0</h1>
  </header>
  <div class="main">
    <div class="video-box">
      <video bind:this={videoElement} autoplay playsinline></video>
      <canvas bind:this={canvasElement} width="640" height="480"></canvas>
    </div>
    <aside class="panel {showWarning ? 'warning' : ''}">
      <p>{message}</p>
      {#if errorMessage}
        <p class="alert">{errorMessage}</p>
      {/if}
      {#if !calibrating}
        <p>Frames procesados: {frames}</p>
        <p>Ángulo cuello-espalda: {neckAngle}°</p>
        <p>Ángulo hombros-cadera: {hipAngle}°</p>
        <p>Visibilidad promedio: {visibility}%</p>
        <p>Estado: {posture}</p>
        <p>Frecuencia cardiaca (BPM): {bpm === null ? 'N/D' : bpm.toFixed(1)}</p>
        <p>HRV estimado: {hrvValue === null ? 'N/D' : hrvValue.toFixed(1) + ' ms'}</p>
        {#if showWarning}
          <p class="alert">⚠️ Ajusta tu postura para evitar fatiga</p>
        {/if}
      {/if}
    </aside>
    <div id="explicacion-panel" class="info-box">
      <h3>¿Qué significan estos valores?</h3>
      <ul>
        <li><strong>HRV (Variabilidad Cardiaca):</strong> Una medida de tu equilibrio interno. Si es menor a 25 ms, podrías estar estresado. Si es mayor, estás relajado.</li>
        <li><strong>BPM:</strong> Tus latidos por minuto. Normalmente entre 60–90 en reposo.</li>
        <li><strong>Ángulo cuello-espalda:</strong> Muestra si estás encorvado. Un ángulo bajo indica mala postura.</li>
        <li><strong>Postura:</strong> Verde = Correcta, Amarillo = Dudosa, Rojo = Incorrecta.</li>
        <li><strong>Movimiento:</strong> Si te mueves bruscamente, el sistema lo detecta y te avisa.</li>
        <li><strong>Distancia:</strong> Qué tan lejos estás de la cámara. Muy cerca o muy lejos afecta la precisión.</li>
      </ul>
    </div>
  </div>
</div>

<style>
  .container {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: flex-start;
    height: 100vh;
    padding: 1rem;
    box-sizing: border-box;
    background: #202020;
    color: #eee;
  }

  header {
    margin-bottom: 1rem;
  }

  .main {
    display: flex;
    gap: 1rem;
    flex-wrap: wrap;
    align-items: flex-start;
  }

  .video-box {
    position: relative;
  }

  video {
    width: 640px;
    height: 480px;
    background: #000;
  }

  canvas {
    position: absolute;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    pointer-events: none;
  }

  .panel {
    display: flex;
    flex-direction: column;
    gap: 0.4rem;
    min-width: 220px;
    padding: 1rem;
    background: #2c2c2c;
    border-radius: 8px;
  }

  .info-box {
    display: flex;
    flex-direction: column;
    gap: 0.4rem;
    min-width: 220px;
    padding: 1rem;
    background: #2c2c2c;
    border-radius: 8px;
  }

  .panel.warning {
    animation: blink 1s infinite;
  }

  .alert {
    color: #ff5555;
  }

  @keyframes blink {
    0%, 100% { background-color: #2c2c2c; }
    50% { background-color: #552222; }
  }
</style>

