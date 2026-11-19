// Reading the scraped BBO Bridge Master files (data/bbo_bridgemaster) and
// reconstructing what the review screen showed: the play line (with the
// review's rewinds undone) and every layout of the defenders' cards it showed.

import fs from 'node:fs';
import path from 'node:path';
import { FULL_DECK, SEATS, sortCards, type Card, type Seat, type Strain } from '@/bridge/cards';
import { emptyLayout, layoutKey, layoutProblems, parsePbn, type Layout } from '@/bridge/deal';
import { legalPlays, replay, type Play } from '@/bridge/play';

export interface RawStep {
  step: number;
  hands_pbn: string;
  trick_cards: Partial<Record<Seat, Card>>;
  declarer_tricks: number;
  defense_tricks: number;
  highlighted: Partial<Record<Seat, Partial<Record<string, string[]>>>>;
  commentary: string;
}

export interface RawDeal {
  title: string;
  level: number;
  level_name: string;
  deal_id: string;
  deal_pbn: string;
  contract: string;
  declarer: string;
  dealer: Seat;
  vulnerability: string;
  auction: string[];
  opening_lead: Card;
  par_tricks: number;
  notes: string;
  commentary_paragraphs: string[];
  play_sequence: Array<{ step: number; seat: Seat; card: Card }>;
  solution_steps: RawStep[];
}

export interface RawFile {
  file: string;
  folder: string;
  set: string;
  deal: RawDeal;
}

export function readRaw(root: string): RawFile[] {
  const out: RawFile[] = [];
  for (const folder of fs.readdirSync(root).sort()) {
    const dir = path.join(root, folder);
    if (!fs.statSync(dir).isDirectory() || !folder.startsWith('level_')) continue;
    for (const set of fs.readdirSync(dir).sort()) {
      for (const f of fs.readdirSync(path.join(dir, set))) {
        if (!f.endsWith('.json')) continue;
        const file = path.join(dir, set, f);
        out.push({ file, folder, set, deal: JSON.parse(fs.readFileSync(file, 'utf8')) as RawDeal });
      }
    }
  }
  const num = (id: string) => Number(id.split('-')[1]);
  return out.sort((a, b) => a.deal.level - b.deal.level || a.set.localeCompare(b.set) || num(a.deal.deal_id) - num(b.deal.deal_id));
}

export interface ParsedContract {
  level: number;
  strain: Strain;
  doubled: 0 | 1 | 2;
}

export function parseContract(s: string): ParsedContract {
  const m = /^([1-7])(NT|N|S|H|D|C)(x{0,2}|X{0,2})$/.exec(s.trim());
  if (!m) throw new Error(`bad contract "${s}"`);
  return { level: Number(m[1]), strain: (m[2] === 'NT' ? 'N' : m[2]) as Strain, doubled: m[3]!.length as 0 | 1 | 2 };
}

/** One review step, reconstructed: the full layout (played cards put back with whoever played them) and the play line so far. */
export interface StepState {
  step: number;
  line: Play[];
  layout: Layout;
  layoutKey: string;
  /** Plays undone at this step (the review rewound). */
  rewound: number;
  /**
   * The snapshot doesn't fit this deal: its played cards can't be explained
   * from the line so far, or it changes North's or South's hand (a few reviews
   * show "the same idea on another deal"). `line` / `layout` are then the last
   * good step's.
   */
  foreign: boolean;
}

/**
 * Walk the review's snapshots. Each snapshot gives the cards still in hand; the
 * cards gone from every hand are the ones played. Compared with the line so
 * far, new cards are plays (seat and order from play_sequence) and missing ones
 * are a rewind.
 */
export function reconstruct(d: RawDeal): StepState[] {
  const bySteps = new Map<number, Array<{ seat: Seat; card: Card }>>();
  for (const p of d.play_sequence) {
    const list = bySteps.get(p.step) ?? [];
    list.push({ seat: p.seat, card: p.card });
    bySteps.set(p.step, list);
  }
  const { strain } = parseContract(d.contract);
  const base = parsePbn(d.deal_pbn);
  /**
   * Several cards played between two snapshots (e.g. three rounds of trumps at
   * once): put them in an order the rules allow — turn by turn, each seat's
   * cards that follow suit first, the snapshot's current-trick cards last;
   * play_sequence's order breaks ties.
   */
  const inTurnOrder = (layout: Layout, before: Play[], added: Play[], inTrick: Set<Card>): Play[] => {
    const pending = [...added];
    const seq: Play[] = [];
    while (pending.length > 0) {
      let view = null;
      try {
        view = replay(layout, strain, [...before, ...seq]);
      } catch {
        /* fall back to the given order */
      }
      const legal = new Set(view ? legalPlays(view) : []);
      const mine = pending.filter((p) => p.seat === view?.turn);
      const rank = (p: Play) => (inTrick.has(p.card) ? 2 : 0) + (legal.has(p.card) ? 0 : 1);
      const pick = mine.length > 0 ? mine.reduce((a, b) => (rank(b) < rank(a) ? b : a)) : pending[0]!;
      pending.splice(pending.indexOf(pick), 1);
      seq.push(pick);
    }
    return [...before, ...seq];
  };
  const sameNS = (l: Layout) => l.N.join() === base.N.join() && l.S.join() === base.S.join();
  const states: StepState[] = [];
  let line: Play[] = [];
  let prevLayout = base;
  let prevStep = -1;
  for (const st of d.solution_steps) {
    const attempt = (): { line: Play[]; layout: Layout; rewound: number } | null => {
      const remaining = parsePbn(st.hands_pbn);
      const inHand = new Set(SEATS.flatMap((s) => remaining[s]));
      const played = new Set(FULL_DECK.filter((c) => !inHand.has(c)));
      let next = line;
      let rewound = 0;
      while (next.some((p) => !played.has(p.card))) {
        next = next.slice(0, -1);
        rewound++;
      }
      const have = new Set(next.map((p) => p.card));
      const added = [...played].filter((c) => !have.has(c));
      if (added.length > 0) {
        // Seats and order from play_sequence entries since the last good snapshot.
        const entries: Array<{ seat: Seat; card: Card }> = [];
        for (let k = prevStep + 1; k <= st.step; k++) entries.push(...(bySteps.get(k) ?? []));
        const ordered: Play[] = [];
        for (const e of entries) if (added.includes(e.card) && !ordered.some((o) => o.card === e.card)) ordered.push(e);
        for (const c of added) {
          if (ordered.some((o) => o.card === c)) continue;
          const seat = SEATS.find((s) => prevLayout[s].includes(c));
          if (!seat) return null;
          ordered.push({ seat, card: c });
        }
        next = [...next, ...ordered];
      }
      const layout = emptyLayout();
      for (const s of SEATS) layout[s] = [...remaining[s]];
      for (const p of next) layout[p.seat].push(p.card);
      for (const s of SEATS) layout[s] = sortCards(layout[s]);
      if (layoutProblems(layout).length > 0 || !sameNS(layout)) return null;
      if (added.length > 1) {
        const inTrick = new Set(Object.values(st.trick_cards) as Card[]);
        next = inTurnOrder(layout, next.slice(0, next.length - added.length), next.slice(next.length - added.length), inTrick);
      }
      return { line: next, layout, rewound };
    };
    const got = attempt();
    if (!got) {
      states.push({ step: st.step, line, layout: prevLayout, layoutKey: layoutKey(prevLayout), rewound: 0, foreign: true });
      continue;
    }
    line = got.line;
    states.push({ step: st.step, line, layout: got.layout, layoutKey: layoutKey(got.layout), rewound: got.rewound, foreign: false });
    prevLayout = got.layout;
    prevStep = st.step;
  }
  return states;
}
