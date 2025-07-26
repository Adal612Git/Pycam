import { useEffect, useRef, useState } from 'react';
import './App.css';
import { HRVEstimator } from './lib/hrvEstimator';

function App() {
  const videoRef = useRef<HTMLVideoElement>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const [bpm, setBpm] = useState<string | null>(null);
  const [hrv, setHrv] = useState<string | null>(null);
  const [valid, setValid] = useState(false);
  const estimatorRef = useRef(new HRVEstimator(30));

  useEffect(() => {
    let frame = 0;
    const init = async () => {
      try {
        const stream = await navigator.mediaDevices.getUserMedia({ video: true });
        const video = videoRef.current!;
        video.srcObject = stream;
        await video.play();

        // @ts-ignore
        const mp = await import(/* @vite-ignore */ 'https://cdn.jsdelivr.net/npm/@mediapipe/face_mesh');
        const { FaceMesh } = mp as any;
        const mesh = new FaceMesh({
          locateFile: (f: string) => `https://cdn.jsdelivr.net/npm/@mediapipe/face_mesh/${f}`
        });
        mesh.setOptions({ maxNumFaces: 1, refineLandmarks: false });
        mesh.onResults((res: any) => {
          if (res.multiFaceLandmarks && res.multiFaceLandmarks.length) {
            estimatorRef.current.update(video, res.multiFaceLandmarks[0].landmark || res.multiFaceLandmarks[0]);
            frame++;
            if (frame % 30 === 0) {
              const data = estimatorRef.current.compute();
              if (data.snr >= 15 && data.bpm && data.hrv) {
                setBpm(data.bpm.toFixed(1));
                setHrv(data.hrv.toFixed(1));
                setValid(true);
              } else {
                setBpm(null);
                setHrv(null);
                setValid(false);
              }
            }
          }
        });

        const ctx = canvasRef.current!.getContext('2d')!;
        const draw = () => {
          const sig = estimatorRef.current.getSignal();
          ctx.clearRect(0, 0, ctx.canvas.width, ctx.canvas.height);
          ctx.strokeStyle = '#00ff00';
          ctx.beginPath();
          for (let i = 0; i < sig.length; i++) {
            const x = (i / sig.length) * ctx.canvas.width;
            const y = ctx.canvas.height / 2 - sig[i] + sig[sig.length - 1];
            if (i === 0) ctx.moveTo(x, y);
            else ctx.lineTo(x, y);
          }
          ctx.stroke();
        };

        const loop = async () => {
          await mesh.send({ image: video });
          draw();
          requestAnimationFrame(loop);
        };
        loop();
      } catch (err) {
        console.error(err);
      }
    };
    init();
  }, []);

  return (
    <div className="container">
      <div className="video-wrapper">
        <video ref={videoRef} autoPlay playsInline muted width={640} height={480}></video>
        <canvas ref={canvasRef} width={640} height={100}></canvas>
      </div>
      <div className="panel" style={{ color: valid ? '#33ff77' : '#ff3333' }}>
        <p>BPM: {valid && bpm ? bpm : 'N/D'}</p>
        <p>HRV (RMSSD): {valid && hrv ? `${hrv} ms` : 'N/D'}</p>
      </div>
    </div>
  );
}

export default App;
