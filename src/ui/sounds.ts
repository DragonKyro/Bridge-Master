// Small synthesized sounds (Web Audio, no files): a card snapping down, a
// trick gathered, the contract made or beaten. Browsers only allow audio
// after a user gesture, so the context is created on the first pointer press.

export type Sound = 'card' | 'trick' | 'win' | 'fail' | 'tap';

let ctx: AudioContext | null = null;

function audio(): AudioContext | null {
  if (typeof window === 'undefined') return null;
  if (!ctx) {
    const C = window.AudioContext ?? (window as unknown as { webkitAudioContext?: typeof AudioContext }).webkitAudioContext;
    if (!C) return null;
    try {
      ctx = new C();
    } catch {
      return null;
    }
  }
  if (ctx.state === 'suspended') void ctx.resume().catch(() => {});
  return ctx;
}

if (typeof window !== 'undefined') {
  window.addEventListener('pointerdown', () => audio(), { once: true, capture: true });
}

function tone(a: AudioContext, freq: number, start: number, dur: number, type: OscillatorType = 'sine', gain = 0.07): void {
  const osc = a.createOscillator();
  const g = a.createGain();
  osc.type = type;
  osc.frequency.setValueAtTime(freq, start);
  g.gain.setValueAtTime(0, start);
  g.gain.linearRampToValueAtTime(gain, start + 0.01);
  g.gain.exponentialRampToValueAtTime(0.0001, start + dur);
  osc.connect(g).connect(a.destination);
  osc.start(start);
  osc.stop(start + dur + 0.02);
}

/** A short filtered noise burst: card on felt. */
function snap(a: AudioContext, start: number, gain = 0.2, freq = 2200): void {
  const len = Math.floor(a.sampleRate * 0.05);
  const buf = a.createBuffer(1, len, a.sampleRate);
  const data = buf.getChannelData(0);
  for (let i = 0; i < len; i++) data[i] = (Math.random() * 2 - 1) * (1 - i / len) ** 3;
  const src = a.createBufferSource();
  src.buffer = buf;
  const filter = a.createBiquadFilter();
  filter.type = 'bandpass';
  filter.frequency.value = freq;
  filter.Q.value = 0.8;
  const g = a.createGain();
  g.gain.value = gain;
  src.connect(filter).connect(g).connect(a.destination);
  src.start(start);
}

export function playSound(kind: Sound): void {
  const a = audio();
  if (!a || a.state !== 'running') return;
  const t = a.currentTime + 0.01;
  switch (kind) {
    case 'card':
      snap(a, t);
      break;
    case 'tap':
      snap(a, t, 0.08, 3200);
      break;
    case 'trick':
      snap(a, t);
      snap(a, t + 0.06, 0.12, 1600);
      tone(a, 740, t + 0.05, 0.12, 'triangle', 0.035);
      break;
    case 'win':
      [523, 659, 784, 1047].forEach((f, i) => tone(a, f, t + i * 0.11, 0.32, 'triangle', 0.07));
      break;
    case 'fail':
      tone(a, 330, t, 0.22, 'triangle', 0.05);
      tone(a, 247, t + 0.18, 0.4, 'triangle', 0.05);
      break;
  }
}
