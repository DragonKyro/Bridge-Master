// Per-device preferences, kept in localStorage.

import { create } from 'zustand';

export type Speed = 'relaxed' | 'normal' | 'fast';

export interface Prefs {
  /** Four-colour suits (♦ orange, ♣ green) rather than red / black. */
  fourColor: boolean;
  /** Play a card with one tap; otherwise the first tap raises it and the second plays it. */
  oneTap: boolean;
  sound: boolean;
  speed: Speed;
}

const KEY = 'bridgeMaster.prefs';
const touch = typeof window !== 'undefined' && !!window.matchMedia?.('(hover: none)').matches;
const DEFAULTS: Prefs = { fourColor: true, oneTap: !touch, sound: true, speed: 'normal' };

function load(): Prefs {
  try {
    return { ...DEFAULTS, ...(JSON.parse(localStorage.getItem(KEY) ?? '{}') as Partial<Prefs>) };
  } catch {
    return DEFAULTS;
  }
}

export const usePrefs = create<Prefs & { set: (p: Partial<Prefs>) => void }>((set, get) => ({
  ...load(),
  set: (p) => {
    set(p);
    const { set: _s, ...prefs } = { ...get(), ...p };
    void _s;
    try {
      localStorage.setItem(KEY, JSON.stringify(prefs));
    } catch {
      /* private mode */
    }
  },
}));

/** Milliseconds for the table's pacing. */
export function paceMs(speed: Speed): { card: number; trick: number } {
  switch (speed) {
    case 'relaxed':
      return { card: 750, trick: 1500 };
    case 'fast':
      return { card: 260, trick: 650 };
    default:
      return { card: 480, trick: 1050 };
  }
}
