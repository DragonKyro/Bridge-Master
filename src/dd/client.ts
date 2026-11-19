// The app's DdApi: calls go to the solver worker (started on first use, or
// early with warmUpSolver() so DDS is ready by the time the first card is played).

import type { DdApi } from '@/game/engine';
import type { DdRequest, DdResponse } from './worker';

let worker: Worker | null = null;
let nextId = 1;
const pending = new Map<number, { resolve: (v: unknown) => void; reject: (e: Error) => void }>();

function getWorker(): Worker {
  if (worker) return worker;
  worker = new Worker(new URL('./worker.ts', import.meta.url), { type: 'module' });
  worker.onmessage = (e: MessageEvent<DdResponse>) => {
    const p = pending.get(e.data.id);
    if (!p) return;
    pending.delete(e.data.id);
    if ('error' in e.data) p.reject(new Error(e.data.error));
    else p.resolve(e.data.result);
  };
  worker.onerror = (e) => {
    for (const p of pending.values()) p.reject(new Error(e.message || 'solver failed'));
    pending.clear();
    worker = null;
  };
  return worker;
}

function call<T>(method: keyof DdApi, args: unknown[]): Promise<T> {
  return new Promise<T>((resolve, reject) => {
    const id = nextId++;
    pending.set(id, { resolve: resolve as (v: unknown) => void, reject });
    getWorker().postMessage({ id, method, args } satisfies DdRequest);
  });
}

export const ddApi: DdApi = {
  scores: (...args) => call('scores', args),
  punisher: (...args) => call('punisher', args),
  declarerMax: (...args) => call('declarerMax', args),
};

/** Start the worker (and DDS) ahead of need. */
export function warmUpSolver(): void {
  getWorker();
}
