// The solver's thread: DDS loads here (about half a megabyte of WebAssembly)
// and answers DdApi calls from dd/client.ts.

import { localApi, type DdApi } from '@/game/engine';
import { DdSolver } from './solver';

export interface DdRequest {
  id: number;
  method: keyof DdApi;
  args: unknown[];
}

export type DdResponse = { id: number; result: unknown } | { id: number; error: string };

const api: Promise<DdApi> = DdSolver.create().then(localApi);

self.onmessage = async (e: MessageEvent<DdRequest>) => {
  const { id, method, args } = e.data;
  try {
    const fn = (await api)[method] as (...a: unknown[]) => Promise<unknown>;
    const result = await fn(...args);
    (self as unknown as Worker).postMessage({ id, result } satisfies DdResponse);
  } catch (err) {
    (self as unknown as Worker).postMessage({ id, error: err instanceof Error ? err.message : String(err) } satisfies DdResponse);
  }
};
