// The moves around the human's: after declarer's card, the rigging check;
// then each defender's card. Async because double-dummy work goes through a
// DdApi — the solver worker in the app (dd/client.ts), DDS directly in tests.

import type { Card, Strain } from '@/bridge/cards';
import { layoutToPbn, parsePbn } from '@/bridge/deal';
import { legalPlays, replay, type Play } from '@/bridge/play';
import type { Deal } from '@/data/types';
import type { CardScore, DdSolver } from '@/dd/solver';
import { naturalCard } from './defence';
import { applyPlay, consistentAlternatives, handView, inScriptSpan, scriptedCard, switchLayout, type HandState } from './hand';
import { findPunisher } from './rig';

export interface DdApi {
  /** Scores of every legal card for the player to move. */
  scores(layout: string, strain: Strain, plays: Play[]): Promise<CardScore[]>;
  /** Index of an alternative that beats declarer from here (see rig.ts), or -1. */
  punisher(current: string, alternatives: string[], strain: Strain, plays: Play[], need: number): Promise<number>;
  /** Most tricks declarer's side can still take (current trick on). */
  declarerMax(layout: string, strain: Strain, plays: Play[]): Promise<number>;
}

/** Declarer (or dummy) plays `card`; off the script, the defenders may switch layouts. */
export async function declarerPlays(h: HandState, card: Card, deal: Deal, api: DdApi): Promise<HandState> {
  let next = applyPlay(h, card);
  if (!next.onScript && inScriptSpan(h)) {
    const alts = consistentAlternatives(next, deal);
    if (alts.length > 0) {
      const i = await api.punisher(layoutToPbn(next.layout), alts.map((a) => layoutToPbn(a.layout)), next.strain, next.plays, next.need);
      if (i >= 0) next = switchLayout(next, alts[i]!.index, alts[i]!.layout);
    }
  }
  return next;
}

/** The card the defender to move plays: the script's, else the most natural double-dummy-best one. */
export async function defenderCard(h: HandState, api: DdApi): Promise<Card> {
  const view = handView(h);
  const scripted = scriptedCard(h);
  if (scripted && legalPlays(view).includes(scripted)) return scripted;
  const scores = await api.scores(layoutToPbn(h.layout), h.strain, h.plays);
  return naturalCard(view, h.strain, scores);
}

/** Tricks declarer ends with if the rest is played double dummy (claims). */
export async function claimTricks(h: HandState, api: DdApi): Promise<number> {
  const view = handView(h);
  if (view.done) return view.ns;
  return view.ns + (await api.declarerMax(layoutToPbn(h.layout), h.strain, h.plays));
}

/** A DdApi over a solver in this thread (tests, scripts, and the worker itself). */
export function localApi(dd: DdSolver): DdApi {
  return {
    scores: async (layout, strain, plays) => dd.scores(replay(parsePbn(layout), strain, plays), strain),
    punisher: async (current, alternatives, strain, plays, need) => findPunisher(dd, current, alternatives, strain, plays, need),
    declarerMax: async (layout, strain, plays) => dd.declarerMax(replay(parsePbn(layout), strain, plays), strain),
  };
}
