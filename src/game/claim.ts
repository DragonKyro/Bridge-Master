// Claims: when the tricks declarer still needs are just a matter of cashing
// winners, the rest can be played out quickly and the deal counted as made.
//
// A claim has to be safe two ways:
//
//  1. Against any defenders. The check never looks at how East and West hold
//     their cards, only at which cards are unseen (still in some defender's
//     hand). A trick is sure if declarer's side plays a card that beats every
//     unseen card of the suit that could still be out — after r rounds of a
//     suit, at most (unseen − r) of them remain, and the defenders may have
//     kept the highest. While a defender might still hold a trump, only trump
//     leads count; side-suit winners count once the trumps are surely drawn.
//  2. Obvious, so it can't skip the lesson. It must work in *every* order of
//     cashing those sure tricks, partner following low and discarding a
//     non-winner. If the result depends on unblocking or using entries in the
//     right order, that's a skill being taught, and there is no claim. And
//     claims open only once the hand is past the solution's scripted plays
//     (the crux), with declarer's side on lead.
//
// After a claim the hand plays on fast: declarer's side follows the model's
// line (claimPlay), the defenders play as ever; the model guarantees the tricks.

import { SUITS, cardValue, isDeclarerSide, suitOf, type Card, type Strain, type Suit } from '@/bridge/cards';
import type { PlayView } from '@/bridge/play';
import { handView, type HandState } from './hand';

type Side = 'N' | 'S';

/** What the claim can rely on: the cards unseen when it was made, and the strain. */
interface Model {
  strain: Strain;
  /** Unseen cards of each suit at the claim (the defenders' cards, in whatever split), high to low. */
  unseen: Record<Suit, number[]>;
}

/** Rounds of each suit led since the claim. */
type Rounds = Record<Suit, number>;

interface Option {
  lead: Card;
  follow: Card;
  winner: Side;
}

const partner = (s: Side): Side => (s === 'N' ? 'S' : 'N');
const zeroRounds = (): Rounds => ({ S: 0, H: 0, D: 0, C: 0 });

/** The highest unseen card of `suit` that might still be out after `rounds` rounds (−1: none can be). */
function defMax(m: Model, rounds: Rounds, suit: Suit): number {
  const u = m.unseen[suit];
  return rounds[suit] >= u.length ? -1 : u[0]!;
}

/** Could a defender still hold a trump? */
function trumpsOut(m: Model, rounds: Rounds): boolean {
  return m.strain !== 'N' && rounds[m.strain] < m.unseen[m.strain].length;
}

const lowest = (cards: Card[]): Card => cards.reduce((a, b) => (cardValue(b) < cardValue(a) ? b : a));

/** Partner's discard on a trick its side is winning: the lowest non-winner, keeping trumps if it can. */
function discard(m: Model, rounds: Rounds, hand: Card[]): Card {
  const nonTrumps = m.strain === 'N' ? hand : hand.filter((c) => suitOf(c) !== m.strain);
  const pool = nonTrumps.length > 0 ? nonTrumps : hand;
  const losers = pool.filter((c) => cardValue(c) <= defMax(m, rounds, suitOf(c)));
  return lowest(losers.length > 0 ? losers : pool);
}

/**
 * Partner's card when the leader has led `lead` (the claim's fixed policy):
 * low when the lead is winning, the cheapest sure winner when it isn't,
 * a ruff when void and the defenders surely have no trumps. Null: no sure trick.
 */
function follow(m: Model, rounds: Rounds, lead: Card, hand: Card[]): { card: Card; wins: boolean } | null {
  const suit = suitOf(lead);
  const top = defMax(m, rounds, suit);
  const same = hand.filter((c) => suitOf(c) === suit);
  const leadWins = cardValue(lead) > top;
  if (same.length > 0) {
    if (leadWins) {
      const low = lowest(same);
      return { card: low, wins: cardValue(low) > cardValue(lead) };
    }
    const winners = same.filter((c) => cardValue(c) > top);
    return winners.length > 0 ? { card: lowest(winners), wins: true } : null;
  }
  if (leadWins) {
    const d = discard(m, rounds, hand);
    // Only trumps left: the "discard" ruffs partner's winner — still our trick.
    return { card: d, wins: m.strain !== 'N' && suitOf(d) === m.strain && suit !== m.strain };
  }
  if (m.strain !== 'N' && suit !== m.strain && !trumpsOut(m, rounds)) {
    const trumps = hand.filter((c) => suitOf(c) === m.strain);
    if (trumps.length > 0) return { card: lowest(trumps), wins: true };
  }
  return null;
}

/** Every sure trick the leader can start. While trumps may be out, only trump leads. */
function options(m: Model, rounds: Rounds, hands: Record<Side, Card[]>, leader: Side): Option[] {
  const out: Option[] = [];
  const seen = new Set<string>();
  for (const lead of hands[leader]) {
    const suit = suitOf(lead);
    if (trumpsOut(m, rounds) && suit !== m.strain) continue;
    const f = follow(m, rounds, lead, hands[partner(leader)]);
    if (!f) continue;
    const key = `${lead}|${f.card}`;
    if (seen.has(key)) continue;
    seen.add(key);
    out.push({ lead, follow: f.card, winner: f.wins ? partner(leader) : leader });
  }
  return out;
}

const BUDGET = 60_000;

/** Does every order of sure tricks reach `need` more tricks? (Out of budget: no.) */
function always(m: Model, hands: Record<Side, Card[]>, leader: Side, need: number): boolean {
  const memo = new Map<string, boolean>();
  let nodes = 0;
  const go = (h: Record<Side, Card[]>, lead: Side, rounds: Rounds, k: number): boolean => {
    if (k <= 0) return true;
    if (++nodes > BUDGET) throw new Error('budget');
    const key = `${h.N.join('')}|${h.S.join('')}|${lead}|${SUITS.map((s) => rounds[s]).join('')}|${k}`;
    const hit = memo.get(key);
    if (hit !== undefined) return hit;
    const opts = options(m, rounds, h, lead);
    let ok = opts.length > 0;
    for (const o of opts) {
      if (!ok) break;
      const next: Record<Side, Card[]> = { N: h.N, S: h.S };
      next[lead] = h[lead].filter((c) => c !== o.lead);
      next[partner(lead)] = h[partner(lead)].filter((c) => c !== o.follow);
      ok = go(next, o.winner, { ...rounds, [suitOf(o.lead)]: rounds[suitOf(o.lead)] + 1 }, k - 1);
    }
    memo.set(key, ok);
    return ok;
  };
  try {
    return go(hands, leader, zeroRounds(), need);
  } catch {
    return false;
  }
}

/** The obviousness check on its own (tests): North's and South's cards, the unseen cards, who leads, tricks needed. */
export function obviousClaim(north: Card[], south: Card[], unseen: Card[], strain: Strain, leader: Side, need: number): boolean {
  const u: Record<Suit, number[]> = { S: [], H: [], D: [], C: [] };
  for (const c of unseen) u[suitOf(c)].push(cardValue(c));
  for (const s of SUITS) u[s].sort((a, b) => b - a);
  return always({ strain, unseen: u }, { N: [...north], S: [...south] }, leader, need);
}

function modelAt(view: PlayView, strain: Strain): Model {
  const unseen: Record<Suit, number[]> = { S: [], H: [], D: [], C: [] };
  for (const c of [...view.remaining.E, ...view.remaining.W]) unseen[suitOf(c)].push(cardValue(c));
  for (const s of SUITS) unseen[s].sort((a, b) => b - a);
  return { strain, unseen };
}

/** Whether declarer may claim now: past the script, declarer's side to lead, and the rest is obvious. */
export function canClaim(h: HandState): boolean {
  if (h.claimFrom !== null || h.plays.length < h.script.length) return false;
  const view = handView(h);
  if (view.done || view.turn === null || !isDeclarerSide(view.turn) || view.current.plays.length > 0) return false;
  const need = h.need - view.ns;
  if (need <= 0) return false;
  return always(modelAt(view, h.strain), { N: [...view.remaining.N], S: [...view.remaining.S] }, view.turn as Side, need);
}

/** Declarer's side's card under a claim in progress (null: no claim, or not declarer's turn). */
export function claimPlay(h: HandState): Card | null {
  if (h.claimFrom === null) return null;
  const view = handView(h);
  const seat = view.turn;
  if (seat === null || !isDeclarerSide(seat)) return null;
  // The model as it stood at the claim, with the rounds led since.
  const atClaim = handViewAt(h, h.claimFrom);
  const m = modelAt(atClaim, h.strain);
  const rounds = zeroRounds();
  for (const t of view.tricks.slice(atClaim.tricks.length)) rounds[suitOf(t.plays[0]!.card)]++;
  const hands: Record<Side, Card[]> = { N: [...view.remaining.N], S: [...view.remaining.S] };
  const plays = view.current.plays;
  if (plays.length === 0) {
    const opts = options(m, rounds, hands, seat as Side);
    if (opts.length === 0) return null;
    // Cash trumps first, then keep the lead where it is, top cards first.
    const order = (o: Option) => (m.strain !== 'N' && suitOf(o.lead) === m.strain ? 0 : 2) + (o.winner === seat ? 0 : 1);
    opts.sort((a, b) => order(a) - order(b) || cardValue(b.lead) - cardValue(a.lead));
    return opts[0]!.lead;
  }
  const leadPlay = plays[0]!;
  if (!isDeclarerSide(leadPlay.seat) || leadPlay.seat === seat) return null;
  return follow(m, rounds, leadPlay.card, hands[seat as Side])?.card ?? null;
}

function handViewAt(h: HandState, n: number): PlayView {
  return handView({ ...h, plays: h.plays.slice(0, n) });
}
