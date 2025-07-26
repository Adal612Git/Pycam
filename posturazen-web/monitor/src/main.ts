import './style.css'
import Chart from 'chart.js/auto'

const statusEl = document.getElementById('postureStatus') as HTMLDivElement
const hrvValueEl = document.getElementById('hrvValue') as HTMLSpanElement
const bpmValueEl = document.getElementById('bpmValue') as HTMLSpanElement
const alertEl = document.getElementById('alertCount') as HTMLSpanElement
const timerEl = document.getElementById('timer') as HTMLSpanElement
const messageEl = document.getElementById('message') as HTMLDivElement

let alerts = 0
let countdown = 600 // 10 min in seconds
let currentStatus: 'good' | 'warn' | 'bad' = 'good'

const hrvData: number[] = []
const ctx = (document.getElementById('hrvChart') as HTMLCanvasElement).getContext('2d')!
const hrvChart = new Chart(ctx, {
  type: 'line',
  data: { labels: [], datasets: [{ data: hrvData, borderColor: '#4caf50', tension: 0.3 }] },
  options: { animation: false, scales: { x: { display: false }, y: { beginAtZero: true } } }
})

function randomChoice<T>(items: T[]): T {
  return items[Math.floor(Math.random() * items.length)]
}

function simulatePosture() {
  const state = randomChoice(['good', 'good', 'warn', 'bad']) as 'good' | 'warn' | 'bad'
  currentStatus = state
  if (state === 'good') {
    statusEl.textContent = '✅ Buena postura'
  } else if (state === 'warn') {
    statusEl.textContent = '⚠️ Postura incorrecta'
  } else {
    statusEl.textContent = '❌ Muy mala postura'
  }
  statusEl.className = 'status ' + state
  if (state !== 'good') {
    alerts++
    alertEl.textContent = String(alerts)
    countdown = 600
  }
}

function simulateHRV() {
  const value = 20 + Math.random() * 60
  hrvValueEl.textContent = value.toFixed(0)
  hrvData.push(value)
  if (hrvData.length > 20) hrvData.shift()
  hrvChart.update()
  if (value < 25 || alerts > 5) {
    messageEl.textContent = 'Relájate un poco 😟'
  }
}

function simulateBPM() {
  const value = 60 + Math.random() * 40
  bpmValueEl.textContent = value.toFixed(0)
}

function updateTimer() {
  if (currentStatus === 'good') {
    if (countdown > 0) countdown--
    if (countdown === 0) {
      messageEl.textContent = '¡Logro desbloqueado! 🎉'
    }
  }
  const m = String(Math.floor(countdown / 60)).padStart(2, '0')
  const s = String(countdown % 60).padStart(2, '0')
  timerEl.textContent = `${m}:${s}`
}

setInterval(simulatePosture, 1000)
setInterval(simulateHRV, 2000)
setInterval(simulateBPM, 1500)
setInterval(updateTimer, 1000)
