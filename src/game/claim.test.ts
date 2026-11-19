// Claims: offered only when obvious, and when made they always come home —
// against the dealt cards and against any other split of the unseen cards.

import { describe, expect, it } from 'vitest';
import { isDeclarerSide } from '@/bridge/cards';
import { cloneLayout, layoutToPbn } from '@/bridge/deal';
import { legalPlays, replay } from '@/bridge/play';
import type { Deal } from '@/data/types';
import { DdSolver } from '@/dd/solver';
import { canClaim, claimPlay, obviousClaim } from './claim';
import { applyPlay, handView, startHand, type HandState } from './hand';
import { declarerPlays, defenderCard, localApi, type DdApi } from './engine';

const sets = import.meta.glob<Deal[]>('../data/sets/*.json', { eager: true, import: 'default' });
const deals = Object.values(sets).flat();

/** A seeded RNG, so failures reproduce. */
function rng(seed: number) {
  return () => {
    seed = (seed * 1664525 + 1013904223) >>> 0;
    return seed / 2 ** 32;
  };
}

/** The same position with the unseen cards dealt differently between East and West (consistent with every card played). */
function reshuffle(h: HandState, rand: () => number): HandState | null {
  const view = handView(h);
  const unseen = [...view.remaining.E, ...view.remaining.W];
  for (let attempt = 0; attempt < 60; attempt++) {
    const pool = [...unseen];
    for (let i = pool.length - 1; i > 0; i--) {
      const j = Math.floor(rand() * (i + 1));
      [pool[i], pool[j]] = [pool[j]!, pool[i]!];
    }
    const layout = cloneLayout(h.layout);
    const playedBy = (seat: 'E' | 'W') => h.plays.filter((p) => p.seat === seat).map((p) => p.card);
    layout.E = [...playedBy('E'), ...pool.slice(0, view.remaining.E.length)];
    layout.W = [...playedBy('W'), ...pool.slice(view.remaining.E.length)];
    try {
      replay(layout, h.strain, h.plays);
      return { ...h, layout };
    } catch {
      /* contradicts a show-out; try another split */
    }
  }
  return null;
}

/** Claim now and play it out; returns declarer's tricks and whether the claim line ever ran out of cards. */
async function claimOut(h0: HandState, api: DdApi): Promise<{ tricks: number; stuck: boolean }> {
  let h: HandState = { ...h0, claimFrom: h0.plays.length };
  for (;;) {
    const view = handView(h);
    if (view.done || view.ns >= h.need) return { tricks: view.ns, stuck: false };
    let card;
    if (isDeclarerSide(view.turn!)) {
      card = claimPlay(h);
      if (!card || !legalPlays(view).includes(card)) return { tricks: view.ns, stuck: true };
    } else {
      card = await defenderCard(h, api);
    }
    h = applyPlay(h, card);
  }
}

describe('what counts as obvious', () => {
  it('all top cards in notrump: yes', () => {
    expect(obviousClaim(['HA', 'HK', 'C2'], ['SA', 'SK', 'CA'], ['SQ', 'SJ', 'HQ', 'CK', 'D2', 'D3'], 'N', 'S', 3)).toBe(true);
  });
  it('winners stranded in a hand with no entry: no', () => {
    // South can cash two spades, but dummy's hearts can never be reached.
    expect(obviousClaim(['HA', 'HK', 'HQ'], ['SA', 'SK', 'D2'], ['SQ', 'SJ', 'HJ', 'DA', 'D3', 'C2'], 'N', 'S', 3)).toBe(false);
  });
  it('a defender may still hold a higher trump: no', () => {
    expect(obviousClaim(['S2', 'HA', 'HK'], ['SQ', 'DA', 'DK'], ['SK', 'S3', 'HQ', 'DQ', 'C2', 'C3'], 'S', 'S', 3)).toBe(false);
  });
  it('top trumps draw the last ones, then the side winners are safe: yes', () => {
    expect(obviousClaim(['S2', 'HA', 'HK'], ['SA', 'SK', 'DA'], ['SQ', 'S3', 'HQ', 'DQ', 'C2', 'C3'], 'S', 'S', 3)).toBe(true);
  });
});

describe('claims', () => {
  it('are never offered inside the scripted solution', () => {
    for (const deal of deals) {
      let h = startHand(deal);
      for (let i = 1; i < deal.line.length; i++) {
        expect(canClaim(h)).toBe(false);
        h = applyPlay(h, deal.line[i]!);
      }
    }
  });

  it('always come home: every claim offered along the solution and along random lines, against many splits', async () => {
    const api = localApi(await DdSolver.create());
    const rand = rng(7);
    let offered = 0;
    let checked = 0;
    const firstClaimTrick: number[] = [];
    const failures: string[] = [];
    for (const deal of deals) {
      // Two playthroughs: the solution then double-dummy declarer, and one with random declarer cards after the script.
      for (const randomDeclarer of [false, true]) {
        let h = startHand(deal);
        let firstHere = true;
        for (;;) {
          const view = handView(h);
          if (view.done || view.ns >= h.need || view.ew > 13 - h.need) break;
          if (canClaim(h)) {
            offered++;
            if (firstHere && !randomDeclarer) firstClaimTrick.push(view.tricks.length + 1);
            firstHere = false;
            for (const variant of [h, reshuffle(h, rand), reshuffle(h, rand), reshuffle(h, rand)]) {
              if (!variant) continue;
              checked++;
              const r = await claimOut(variant, api);
              if (r.stuck || r.tricks < h.need) failures.push(`${deal.id} trick ${view.tricks.length + 1}: ${r.tricks}/${h.need}${r.stuck ? ' (claim line stuck)' : ''}`);
            }
          }
          const seat = view.turn!;
          let card;
          if (isDeclarerSide(seat)) {
            const scripted = h.onScript && h.plays.length < h.script.length ? h.script[h.plays.length]! : null;
            if (scripted) card = scripted;
            else if (randomDeclarer) {
              const legal = legalPlays(view);
              card = legal[Math.floor(rand() * legal.length)]!;
            } else {
              const scores = await api.scores(layoutToPbn(h.layout), h.strain, h.plays);
              const best = Math.max(...scores.map((s) => s.score));
              card = scores.find((s) => s.score === best)!.card;
            }
            h = await declarerPlays(h, card, deal, api);
          } else {
            h = applyPlay(h, await defenderCard(h, api));
          }
        }
      }
    }
    const avg = firstClaimTrick.reduce((a, b) => a + b, 0) / Math.max(1, firstClaimTrick.length);
    console.log(`claims offered ${offered} times, ${checked} claim runs checked; on the solution line ${firstClaimTrick.length}/${deals.length} deals offer a claim, first at trick ${avg.toFixed(1)} on average`);
    expect(failures).toEqual([]);
  });
});
