// The hand on the table: the human plays South and dummy, the engine plays the
// defenders (paced so each card can be watched), and the attempt is scored
// when the contract is made or beaten (tricks after that don't matter).

import { create } from 'zustand';
import { isDeclarerSide, type Card } from '@/bridge/cards';
import { legalPlays } from '@/bridge/play';
import type { Deal } from '@/data/types';
import { ddApi } from '@/dd/client';
import { declarerPlays, defenderCard } from '@/game/engine';
import { applyPlay, handView, startHand, type HandState } from '@/game/hand';
import { paceMs, usePrefs } from './prefsStore';
import { useProgress, type DealProgress } from './progressStore';
import { playSound } from '@/ui/sounds';

export type Phase = 'auction' | 'play' | 'done';

export interface Outcome {
  made: boolean;
  /** Tricks declarer had when the result was settled. */
  tricks: number;
  /** Gold-star attempt: no undo, solution not looked at. */
  clean: boolean;
  progress: DealProgress;
  /** The defenders' cards moved to beat this line (shown in the result). */
  switched: boolean;
}

interface PlayState {
  deal: Deal | null;
  hand: HandState | null;
  /** Hand states before each of the human's cards (undo). */
  history: HandState[];
  phase: Phase;
  /** The engine is choosing or pacing the defenders' cards. */
  busy: boolean;
  usedUndo: boolean;
  /** The solution has been opened since this deal was opened (later solves earn silver). */
  peeked: boolean;
  outcome: Outcome | null;
  error: string | null;
  open: (deal: Deal) => void;
  /** End the auction display: the opening lead goes down. */
  begin: () => void;
  play: (card: Card) => void;
  undo: () => void;
  restart: () => void;
  notePeek: () => void;
}

/** Bumped on every open / restart / undo so stale async work stops. */
let session = 0;
const sleep = (ms: number) => new Promise<void>((r) => setTimeout(r, ms));

export const usePlay = create<PlayState>((set, get) => {
  const pace = () => paceMs(usePrefs.getState().speed);
  const sound = (s: Parameters<typeof playSound>[0]) => {
    if (usePrefs.getState().sound) playSound(s);
  };

  /** Settle the attempt once it can't change: made, or beaten. */
  const settle = (h: HandState): boolean => {
    const view = handView(h);
    const made = view.ns >= h.need;
    const beaten = view.ew > 13 - h.need;
    if (!made && !beaten && !view.done) return false;
    const { deal, usedUndo, peeked } = get();
    const clean = !usedUndo && !peeked;
    const progress = useProgress.getState().record(deal!.id, made, clean);
    set({ phase: 'done', busy: false, outcome: { made, tricks: view.ns, clean, progress, switched: h.switches > 0 } });
    sound(made ? 'win' : 'fail');
    return true;
  };

  /** Defenders play until it is declarer's (or dummy's) turn, or the result is settled. */
  const runDefence = async (id: number) => {
    for (;;) {
      const h = get().hand!;
      if (settle(h)) return;
      const view = handView(h);
      if (view.turn === null || isDeclarerSide(view.turn)) break;
      // A finished trick stays up a moment before the next lead.
      await sleep(view.current.plays.length === 0 && view.tricks.length > 0 ? pace().trick : pace().card);
      if (id !== session) return;
      let card: Card;
      try {
        card = await defenderCard(h, ddApi);
      } catch (e) {
        if (id === session) set({ busy: false, error: (e as Error).message });
        return;
      }
      if (id !== session) return;
      const next = applyPlay(h, card);
      set({ hand: next });
      sound(handView(next).current.plays.length === 0 ? 'trick' : 'card');
    }
    if (id === session) set({ busy: false });
  };

  return {
    deal: null,
    hand: null,
    history: [],
    phase: 'auction',
    busy: false,
    usedUndo: false,
    peeked: false,
    outcome: null,
    error: null,

    open: (deal) => {
      session++;
      set({ deal, hand: startHand(deal), history: [], phase: 'auction', busy: false, usedUndo: false, peeked: false, outcome: null, error: null });
    },

    begin: () => {
      if (get().phase !== 'auction') return;
      set({ phase: 'play' });
      sound('card');
      const id = session;
      set({ busy: true });
      void runDefence(id);
    },

    play: (card) => {
      const { hand, deal, phase, busy } = get();
      if (!hand || !deal || phase !== 'play' || busy) return;
      const view = handView(hand);
      if (view.turn === null || !isDeclarerSide(view.turn) || !legalPlays(view).includes(card)) return;
      const id = session;
      set({ busy: true, history: [...get().history, hand] });
      // Show the card at once; the rigging check (which may change the hidden cards) runs meanwhile.
      const shown = applyPlay(hand, card);
      set({ hand: shown });
      sound(handView(shown).current.plays.length === 0 ? 'trick' : 'card');
      void (async () => {
        let next: HandState;
        try {
          next = await declarerPlays(hand, card, deal, ddApi);
        } catch (e) {
          if (id === session) set({ busy: false, error: (e as Error).message });
          return;
        }
        if (id !== session) return;
        set({ hand: next });
        await runDefence(id);
      })();
    },

    undo: () => {
      const { history, phase } = get();
      if (history.length === 0 || phase === 'auction') return;
      session++;
      set({ hand: history[history.length - 1]!, history: history.slice(0, -1), busy: false, usedUndo: true, phase: 'play', outcome: null });
    },

    restart: () => {
      const { deal } = get();
      if (!deal) return;
      session++;
      set({ hand: startHand(deal), history: [], phase: 'auction', busy: false, usedUndo: false, outcome: null, error: null });
    },

    notePeek: () => set({ peeked: true }),
  };
});

/** Whether the human may act now (their turn, nothing pending). */
export function humanTurn(s: PlayState): boolean {
  if (!s.hand || s.phase !== 'play' || s.busy) return false;
  const t = handView(s.hand).turn;
  return t !== null && isDeclarerSide(t);
}
