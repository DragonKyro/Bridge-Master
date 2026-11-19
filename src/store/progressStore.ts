// Which deals are solved. A gold star: made cleanly (no undo, solution not
// looked at first); silver: made with help. Kept in localStorage, and synced
// to Firestore when signed in (net/cloud.ts merges both ways: best star wins).

import { create } from 'zustand';

export type Star = 1 | 2; // 1 silver, 2 gold

export interface DealProgress {
  /** Best star earned (absent: not solved yet). */
  b?: Star;
  /** Attempts finished. */
  t: number;
  /** When the best star was earned (ms). */
  at?: number;
}

export type ProgressMap = Record<string, DealProgress>;

const KEY = 'bridgeMaster.progress';

function load(): ProgressMap {
  try {
    return JSON.parse(localStorage.getItem(KEY) ?? '{}') as ProgressMap;
  } catch {
    return {};
  }
}

function save(p: ProgressMap): void {
  try {
    localStorage.setItem(KEY, JSON.stringify(p));
  } catch {
    /* private mode */
  }
}

/** Combine two records of a deal: the better star (earliest time for it), the most attempts. */
export function mergeDeal(a: DealProgress | undefined, b: DealProgress | undefined): DealProgress {
  if (!a) return b!;
  if (!b) return a;
  const best = Math.max(a.b ?? 0, b.b ?? 0) as 0 | Star;
  const ats = [a, b].filter((x) => (x.b ?? 0) === best && x.at).map((x) => x.at!);
  return { ...(best ? { b: best } : {}), t: Math.max(a.t, b.t), ...(ats.length ? { at: Math.min(...ats) } : {}) };
}

export function mergeProgress(a: ProgressMap, b: ProgressMap): ProgressMap {
  const out: ProgressMap = { ...a };
  for (const [id, p] of Object.entries(b)) out[id] = mergeDeal(a[id], p);
  return out;
}

interface ProgressState {
  deals: ProgressMap;
  /** Record a finished attempt. Returns the deal's new progress. */
  record: (id: string, made: boolean, clean: boolean) => DealProgress;
  /** Fold in progress from elsewhere (the cloud). */
  absorb: (other: ProgressMap) => void;
  /** Called with each change, for the cloud sync. */
  onChange: ((id: string, p: DealProgress) => void) | null;
}

export const useProgress = create<ProgressState>((set, get) => ({
  deals: load(),
  onChange: null,
  record: (id, made, clean) => {
    const prev = get().deals[id];
    const now: DealProgress = { t: 1, ...(made ? { b: clean ? 2 : 1, at: Date.now() } : {}) };
    const next = mergeDeal(prev, now);
    next.t = (prev?.t ?? 0) + 1;
    const deals = { ...get().deals, [id]: next };
    save(deals);
    set({ deals });
    get().onChange?.(id, next);
    return next;
  },
  absorb: (other) => {
    const deals = mergeProgress(get().deals, other);
    save(deals);
    set({ deals });
  },
}));

export function starOf(p: DealProgress | undefined): 0 | Star {
  return p?.b ?? 0;
}
