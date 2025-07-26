<script context="module" lang="ts">
  export const ssr = false;
</script>

<script lang="ts">
  import { onMount } from 'svelte';
  import { neckBackAngle, shoulderHipAngle } from '$lib/pose/angles';
  import { HRVEstimator } from '$lib/pose/hrv';
  import Chart from 'chart.js/auto';

  let pose: any;
  let videoElement: HTMLVideoElement;
  let canvasElement: HTMLCanvasElement;
  let canvasCtx: CanvasRenderingContext2D;

  let countdown = 10;
  let message = 'Calibrando… espera 10s';
  let calibrating = true;

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

  let bpm = 0;
  let hrvValue = 0;
  let hrvEstimator: HRVEstimator;

  let badStart: number | null = null;
  let showWarning = false;

  let alertCount = 0;
  let postureState: 'good' | 'warn' | 'bad' = 'good';
  let prevIncorrect = false;
  let timer = 0;
  let celebration = false;
  let chartCanvas: HTMLCanvasElement;
  let hrvChart: Chart;
  const hrvData: number[] = [];

  // --- Voice feedback state ---
  let compassionate = false;
  let silentMode = false;
  let goodStart: number | null = null;
  let congratulated = false;
  let lastSpeak = 0;

  function speak(text: string) {
    if (silentMode) return;
    const now = Date.now();
    if (now - lastSpeak < 5000) return;
    lastSpeak = now;
    const utter = new SpeechSynthesisUtterance(text);
    speechSynthesis.speak(utter);
  }

  function formatTime(t: number) {
    const m = String(Math.floor(t / 60)).padStart(2, '0');
    const s = String(t % 60).padStart(2, '0');
    return `${m}:${s}`;
  }

  onMount(async () => {
    const stream = await navigator.mediaDevices.getUserMedia({ video: true });
    videoElement.srcObject = stream;
    await videoElement.play();

    const posePkg = await import('@mediapipe/pose');
    const { Pose } = posePkg;

    pose = new Pose({ locateFile: (f: string) => `https://cdn.jsdelivr.net/npm/@mediapipe/pose/${f}` });
    pose.setOptions({ modelComplexity: 1, smoothLandmarks: true });
    pose.onResults(handleResults);

    hrvEstimator = new HRVEstimator(30);

    canvasCtx = canvasElement.getContext('2d') as CanvasRenderingContext2D;

    startProcessing();

    hrvChart = new Chart(chartCanvas.getContext('2d') as CanvasRenderingContext2D, {
      type: 'line',
      data: { labels: [], datasets: [{ data: hrvData, borderColor: '#4caf50', tension: 0.3 }] },
      options: { animation: false, scales: { x: { display: false }, y: { beginAtZero: true } } }
    });

    const countdownTimer = setInterval(() => {
      countdown--;
      if (countdown <= 0) {
        calibrating = false;
        message = 'Monitoreando tu postura';
        baselineNeck = totalNeck / (totalCount || 1);
        baselineHip = totalHip / (totalCount || 1);
        clearInterval(countdownTimer);
      } else {
        message = `Calibrando… espera ${countdown}s`;
      }
    }, 1000);

    setInterval(() => {
      if (!calibrating) {
        if (postureState === 'good') {
          timer++;
          if (timer >= 600 && !celebration) {
            celebration = true;
            speak('¡Excelente trabajo! Has mantenido una buena postura por 10 minutos.');
          }
        } else {
          timer = 0;
          celebration = false;
        }
      }
    }, 1000);
  });

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
        if (hrvValue) {
          hrvData.push(hrvValue);
          if (hrvData.length > 50) hrvData.shift();
          hrvChart.update();
        }
        if (hrvValue && hrvValue < 25) {
          const msg = compassionate
            ? 'Recuerda respirar y relajarte, lo estás haciendo muy bien.'
            : 'Atención, tu HRV está bajo.';
          speak(msg);
        }
      }
      const diff1 = Math.abs(neckAngle - baselineNeck);
      const diff2 = Math.abs(hipAngle - baselineHip);
      postureState = diff1 > 15 || diff2 > 15 ? 'bad' : diff1 > 10 || diff2 > 10 ? 'warn' : 'good';
      const incorrect = postureState !== 'good';

      posture = postureState === 'good' ? 'Correcta' : postureState === 'warn' ? 'Dudosa' : 'Incorrecta';

      if (incorrect && !prevIncorrect) {
        alertCount++;
      }
      prevIncorrect = incorrect;

      showWarning = postureState === 'bad';
      
      if (!incorrect && (!hrvValue || hrvValue >= 25)) {
        if (goodStart === null) {
          goodStart = Date.now();
          congratulated = false;
        } else if (!congratulated && Date.now() - goodStart >= 600000) {
          speak('¡Excelente trabajo! Has mantenido una postura perfecta por 10 minutos.');
          congratulated = true;
        }
      } else {
        goodStart = null;
        congratulated = false;
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
    <div class="toggles">
      <label><input type="checkbox" bind:checked={compassionate}> Modo compasivo</label>
      <label><input type="checkbox" bind:checked={silentMode}> No molestar</label>
    </div>
  </header>
  <div class="main">
    <div class="video-box">
      <video bind:this={videoElement} autoplay playsinline></video>
      <canvas bind:this={canvasElement} width="640" height="480"></canvas>
    </div>
    <aside class="panel {postureState} {showWarning ? 'warning' : ''}">
      <p>{message}</p>
      {#if !calibrating}
        <div class="status {postureState}">Estado: {posture}</div>
        <canvas bind:this={chartCanvas} id="hrvGraph" width="280" height="100"></canvas>
        <p>HRV: {hrvValue ? hrvValue.toFixed(1) + ' ms' : 'N/A'}</p>
        <p>BPM: {bpm ? bpm.toFixed(1) : 'N/A'}</p>
        <p>Alertas posturales: {alertCount}</p>
        <p>Tiempo buena postura: {formatTime(timer)}</p>
        {#if celebration}
          <p class="celebrate">🎉 ¡Excelente! 10 min de buena postura</p>
        {/if}
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

  .panel.good { background: #2c2c2c; }
  .panel.warn { background: #3e3a18; }
  .panel.bad { background: #552222; }

  .status {
    padding: 0.3rem;
    border-radius: 4px;
    text-align: center;
    font-weight: bold;
  }
  .status.good { background: #4caf50; }
  .status.warn { background: #ffeb3b; color: #000; }
  .status.bad { background: #f44336; }

  #hrvGraph {
    width: 100%;
    height: 100px;
  }

  .celebrate {
    color: #4caf50;
    text-align: center;
    font-weight: bold;
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

  .toggles {
    display: flex;
    gap: 1rem;
    margin-top: 0.5rem;
  }

  .toggles label {
    font-size: 0.9rem;
  }

  @keyframes blink {
    0%, 100% { background-color: #2c2c2c; }
    50% { background-color: #552222; }
  }
</style>

