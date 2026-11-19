// Hash routes, so the phone's back button walks back through the app and
// GitHub Pages needs no rewrites: #/  #/level/2  #/deal/2B-7  #/deal/2B-7/solution

import { useSyncExternalStore } from 'react';

export type Route = { name: 'home' } | { name: 'level'; level: number } | { name: 'deal'; id: string; solution: boolean };

export function parseHash(hash: string): Route {
  const parts = hash.replace(/^#\/?/, '').split('/').filter(Boolean);
  if (parts[0] === 'level' && /^[1-5]$/.test(parts[1] ?? '')) return { name: 'level', level: Number(parts[1]) };
  if (parts[0] === 'deal' && /^[1-5][A-D]-\d+$/.test(parts[1] ?? '')) return { name: 'deal', id: parts[1]!, solution: parts[2] === 'solution' };
  return { name: 'home' };
}

const subscribe = (cb: () => void) => {
  window.addEventListener('hashchange', cb);
  return () => window.removeEventListener('hashchange', cb);
};

export function useRoute(): Route {
  const hash = useSyncExternalStore(subscribe, () => window.location.hash);
  return parseHash(hash);
}

export const paths = {
  home: '#/',
  level: (n: number) => `#/level/${n}`,
  deal: (id: string) => `#/deal/${id}`,
  solution: (id: string) => `#/deal/${id}/solution`,
};

/** Pages pushed by go() this visit, so an in-app "back" knows whether history.back() stays in the app. */
let pushed = 0;

/** Navigate; `replace` swaps the current history entry (no extra back step). */
export function go(path: string, replace = false): void {
  if (replace) {
    window.location.replace(path);
  } else {
    pushed++;
    window.location.hash = path.slice(1);
  }
}

/** Back through history when we got here within the app, else straight to `fallback` (e.g. a shared deal link). */
export function back(fallback: string): void {
  if (pushed > 0) {
    pushed--;
    window.history.back();
  } else {
    go(fallback, true);
  }
}
