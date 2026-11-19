// Headless play of whole deals with the real engine (tests and scripts/simulate.ts).

import { isDeclarerSide, type Card } from '@/bridge/cards';
import { layoutToPbn } from '@/bridge/deal';
import { equivalent, legalPlays } from '@/bridge/play';
import type { Deal } from '@/data/types';
import { declarerPlays, defenderCard, type DdApi } from '@/game/engine';
import { handView, scriptedCard, startHand, type HandState } from '@/game/hand';

/** Declarer's double-dummy best card on the current layout (clairvoyant: an upper bound on declarer). */
async function bestDeclarerCard(h: HandState, api: DdApi): Promise<Card> {
  const scores = await api.scores(layoutToPbn(h.layout), h.strain, h.plays);
  const best = Math.max(...scores.map((s) => s.score));
  return scores.find((s) => s.score === best)!.card;
}

export interface Played {
  state: HandState;
  tricks: number;
  made: boolean;
}

/**
 * Play a deal to the end. Declarer follows the solution while on it (and
 * `deviate` says nothing else), then plays double dummy; the defenders use
 * the engine.
 */
export async function playOut(deal: Deal, api: DdApi, deviate?: (h: HandState, i: number) => Card | null): Promise<Played> {
  let h = startHand(deal);
  for (;;) {
    const view = handView(h);
    if (view.done) return { state: h, tricks: view.ns, made: view.ns >= deal.need };
    const seat = view.turn!;
    if (isDeclarerSide(seat)) {
      const forced = deviate?.(h, h.plays.length) ?? null;
      const card = forced ?? scriptedCard(h) ?? (await bestDeclarerCard(h, api));
      h = await declarerPlays(h, card, deal, api);
    } else {
      const card = await defenderCard(h, api);
      h = await declarerPlays(h, card, deal, api);
    }
  }
}

/** Declarer's non-equivalent alternatives to the script's card at the first declarer decision that has any. */
export function firstDecision(deal: Deal): { at: number; options: Card[] } | null {
  let h = startHand(deal);
  for (let i = 1; i < deal.line.length; i++) {
    const view = handView(h);
    const seat = view.turn!;
    const want = deal.line[i]!;
    if (isDeclarerSide(seat)) {
      const options = legalPlays(view).filter((c) => c !== want && !equivalent(view, seat, c, want));
      // One card per group of equivalent alternatives.
      const distinct: Card[] = [];
      for (const c of options) if (!distinct.some((d) => equivalent(view, seat, c, d))) distinct.push(c);
      if (distinct.length > 0) return { at: i, options: distinct };
    }
    h = { ...h, plays: [...h.plays, { seat, card: want }] };
  }
  return null;
}
