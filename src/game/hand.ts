// A hand being played: the plays so far, the layout the defenders hold, and
// whether declarer is still on the solution's line. Pure and synchronous; the
// double-dummy parts (the defenders' cards off the script, switching layouts)
// are driven by the play store through the solver worker.
//
// The rigging (see also scripts/build-deals.ts):
//  - On the script the defenders play the solution's cards — BBO's defence,
//    realistic rather than double dummy (a few solutions rely on it).
//  - Declarer may swap a card for an equivalent one (the 3 for the 2 when
//    nothing lies between): still on the script.
//  - Any other departure leaves the script. From then on the defenders play
//    double dummy, and while the hand is still within the script's span the
//    defenders may switch to one of the deal's alternative layouts that fits
//    every card seen and on which declarer can no longer make (rig.ts) — so a
//    line that only works on the dealt cards fails like it would in BBO.
//  - Getting back to exactly a position of the script (tricks played in
//    another order) rejoins it.

import { SEATS, isDeclarerSide, type Card, type Strain } from '@/bridge/cards';
import { layoutKey, parsePbn, type Layout } from '@/bridge/deal';
import { IllegalPlay, equivalent, legalPlays, playsFromCards, replay, type Play, type PlayView } from '@/bridge/play';
import type { Deal } from '@/data/types';

export interface HandState {
  dealId: string;
  strain: Strain;
  need: number;
  /** The cards the defenders hold now (switching changes it). */
  layout: Layout;
  /** 0: the deal's own layout; k: deal.alts[k - 1]. */
  layoutIndex: number;
  plays: Play[];
  /** The solution's cards, with declarer's equivalent substitutions applied. */
  script: Card[];
  /** Still on the solution (true too once the script has run out without a departure). */
  onScript: boolean;
  /** Index into plays of declarer's first departure from the script. */
  deviatedAt: number | null;
  /** How many times the defenders' layout changed. */
  switches: number;
}

export function strainOf(contract: string): Strain {
  const m = /^[1-7](NT|N|S|H|D|C)/.exec(contract);
  if (!m) throw new Error(`bad contract ${contract}`);
  return (m[1] === 'NT' ? 'N' : m[1]) as Strain;
}

export function layoutOf(deal: Deal, index: number): Layout {
  return parsePbn(index === 0 ? deal.layout : deal.alts[index - 1]!);
}

/** A fresh hand with West's opening lead on the table. */
export function startHand(deal: Deal): HandState {
  const layout = layoutOf(deal, 0);
  return {
    dealId: deal.id,
    strain: strainOf(deal.contract),
    need: deal.need,
    layout,
    layoutIndex: 0,
    plays: [{ seat: 'W', card: deal.lead }],
    script: [...deal.line],
    onScript: true,
    deviatedAt: null,
    switches: 0,
  };
}

export function handView(h: HandState): PlayView {
  return replay(h.layout, h.strain, h.plays);
}

/** The defenders' card while on the script (null off it or once it has run out). */
export function scriptedCard(h: HandState): Card | null {
  if (!h.onScript || h.plays.length >= h.script.length) return null;
  return h.script[h.plays.length]!;
}

/** The solution's card for whoever is to play, if declarer is still on it (hints). */
export const solutionCard = scriptedCard;

/** Whether the play about to be made is inside the script's span (switching is allowed there). */
export function inScriptSpan(h: HandState): boolean {
  return h.plays.length < h.script.length;
}

/** Make the next play (whoever's turn it is). Throws IllegalPlay. */
export function applyPlay(h: HandState, card: Card): HandState {
  const view = handView(h);
  const seat = view.turn;
  if (seat === null) throw new IllegalPlay('the hand is over');
  if (!legalPlays(view).includes(card)) throw new IllegalPlay(`${seat} cannot play ${card}`);
  const i = h.plays.length;
  let { script, onScript, deviatedAt } = h;
  if (onScript && i < script.length) {
    const want = script[i]!;
    if (card !== want) {
      if (isDeclarerSide(seat) && equivalent(view, seat, card, want)) {
        // Play the rest of the script with the two cards swapped.
        script = script.map((c, j) => (j === i ? card : j > i && c === card ? want : c));
      } else {
        onScript = false;
        if (deviatedAt === null) deviatedAt = i;
      }
    }
  }
  const plays = [...h.plays, { seat, card }];
  let next: HandState = { ...h, plays, script, onScript, deviatedAt };
  if (!onScript && next.layoutIndex === 0 && plays.length < script.length && samePosition(next)) next = { ...next, onScript: true };
  return next;
}

/** Is the position the same as the script's after as many plays (tricks taken in another order)? */
function samePosition(h: HandState): boolean {
  const plays = playsFromCards(h.layout, h.strain, h.script.slice(0, h.plays.length));
  if (plays.length < h.plays.length) return false;
  const scripted = replay(h.layout, h.strain, plays);
  const now = handView(h);
  if (scripted.ns !== now.ns || scripted.turn !== now.turn) return false;
  if (scripted.current.plays.map((p) => p.seat + p.card).join() !== now.current.plays.map((p) => p.seat + p.card).join()) return false;
  return SEATS.every((s) => scripted.remaining[s].join() === now.remaining[s].join());
}

/** The deal's alternative layouts (with their indices) that fit every card played so far, the current one excluded. */
export function consistentAlternatives(h: HandState, deal: Deal): Array<{ index: number; layout: Layout }> {
  const out: Array<{ index: number; layout: Layout }> = [];
  const current = layoutKey(h.layout);
  for (let index = 0; index <= deal.alts.length; index++) {
    if (index === h.layoutIndex) continue;
    const layout = layoutOf(deal, index);
    if (layoutKey(layout) === current) continue;
    try {
      replay(layout, h.strain, h.plays);
      out.push({ index, layout });
    } catch {
      /* contradicts a card already seen */
    }
  }
  return out;
}

export function switchLayout(h: HandState, index: number, layout: Layout): HandState {
  return { ...h, layout, layoutIndex: index, switches: h.switches + 1 };
}

export interface HandResult {
  done: boolean;
  /** Tricks won by declarer. */
  tricks: number;
  made: boolean;
  /** Over- (positive) or under- (negative) tricks. */
  margin: number;
}

export function handResult(h: HandState, tricks = handView(h).ns): HandResult {
  return { done: true, tricks, made: tricks >= h.need, margin: tricks - h.need };
}
