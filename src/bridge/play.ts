// The card play: replaying a sequence of plays on a layout, legality, trick
// winners. South declares, so West always makes the opening lead.

import { SEATS, cardValue, isDeclarerSide, nextSeat, suitOf, type Card, type Seat, type Strain, type Suit } from './cards';
import { cloneLayout, type Layout } from './deal';

export interface Play {
  seat: Seat;
  card: Card;
}

export interface Trick {
  leader: Seat;
  plays: Play[];
  /** Set once four cards are in. */
  winner: Seat | null;
}

export interface PlayView {
  /** Cards still in hand (the current trick's cards are out). */
  remaining: Layout;
  /** Completed tricks. */
  tricks: Trick[];
  /** The trick in progress (no plays yet when a new trick is about to be led). */
  current: Trick;
  /** Whose card is next (null when all 13 tricks are done). */
  turn: Seat | null;
  /** Tricks won by declarer's side / the defence. */
  ns: number;
  ew: number;
  done: boolean;
}

export class IllegalPlay extends Error {}

export function trickWinner(plays: readonly Play[], strain: Strain): Seat {
  const led = suitOf(plays[0]!.card);
  let best = plays[0]!;
  for (const p of plays.slice(1)) {
    const s = suitOf(p.card);
    const bs = suitOf(best.card);
    if (s === bs) {
      if (cardValue(p.card) > cardValue(best.card)) best = p;
    } else if (strain !== 'N' && s === strain && bs !== strain) {
      best = p;
    } else if (s === led && bs !== led && bs !== strain) {
      best = p;
    }
  }
  return best.seat;
}

export function ledSuit(trick: Trick): Suit | null {
  return trick.plays.length > 0 ? suitOf(trick.plays[0]!.card) : null;
}

/** The cards `hand` may play to a trick led in `led` (null: any). */
export function legalFrom(hand: readonly Card[], led: Suit | null): Card[] {
  if (led === null) return [...hand];
  const follow = hand.filter((c) => suitOf(c) === led);
  return follow.length > 0 ? follow : [...hand];
}

export function legalPlays(view: PlayView): Card[] {
  if (view.turn === null) return [];
  return legalFrom(view.remaining[view.turn], ledSuit(view.current));
}

/** Replay `plays` from the start (West on lead). Throws IllegalPlay on a card out of turn, not held, or a revoke. */
export function replay(layout: Layout, strain: Strain, plays: readonly Play[], leader: Seat = 'W'): PlayView {
  const remaining = cloneLayout(layout);
  const tricks: Trick[] = [];
  let current: Trick = { leader, plays: [], winner: null };
  let turn: Seat | null = leader;
  let ns = 0;
  let ew = 0;
  plays.forEach((p, i) => {
    if (turn === null) throw new IllegalPlay(`play ${i} (${p.seat} ${p.card}) after the last trick`);
    if (p.seat !== turn) throw new IllegalPlay(`play ${i}: ${p.seat} played ${p.card} but it is ${turn}'s turn`);
    const hand = remaining[p.seat];
    const at = hand.indexOf(p.card);
    if (at < 0) throw new IllegalPlay(`play ${i}: ${p.seat} does not hold ${p.card}`);
    if (!legalFrom(hand, ledSuit(current)).includes(p.card)) throw new IllegalPlay(`play ${i}: ${p.seat} revokes with ${p.card}`);
    hand.splice(at, 1);
    current.plays.push(p);
    if (current.plays.length === 4) {
      const winner = trickWinner(current.plays, strain);
      current.winner = winner;
      if (isDeclarerSide(winner)) ns++;
      else ew++;
      tricks.push(current);
      current = { leader: winner, plays: [], winner: null };
      turn = tricks.length === 13 ? null : winner;
    } else {
      turn = nextSeat(p.seat);
    }
  });
  return { remaining, tricks, current, turn, ns, ew, done: tricks.length === 13 };
}

/** Every card played so far (completed tricks and the current one). */
export function playedCards(view: PlayView): Card[] {
  return [...view.tricks.flatMap((t) => t.plays.map((p) => p.card)), ...view.current.plays.map((p) => p.card)];
}

/**
 * Whether `a` and `b` are interchangeable for `seat` right now: same suit, both
 * in its hand, and every card ranked between them is either in the same hand
 * or gone in a completed trick. (A card in the current trick, or in any other
 * hand — partner's included — makes them different.)
 */
export function equivalent(view: PlayView, seat: Seat, a: Card, b: Card): boolean {
  if (a === b) return true;
  if (suitOf(a) !== suitOf(b)) return false;
  const hand = view.remaining[seat];
  if (!hand.includes(a) || !hand.includes(b)) return false;
  const lo = Math.min(cardValue(a), cardValue(b));
  const hi = Math.max(cardValue(a), cardValue(b));
  const suit = suitOf(a);
  for (const s of SEATS) {
    if (s === seat) continue;
    for (const c of view.remaining[s]) if (suitOf(c) === suit && cardValue(c) > lo && cardValue(c) < hi) return false;
  }
  for (const p of view.current.plays) if (suitOf(p.card) === suit && cardValue(p.card) > lo && cardValue(p.card) < hi) return false;
  return true;
}

/** Tricks still to be decided, counting the current one. */
export function tricksLeft(view: PlayView): number {
  return 13 - view.tricks.length;
}

/**
 * The plays for a list of cards played in turn from the start (each card's
 * seat follows from the turn order). Stops early at a card the player to move
 * doesn't hold or may not play.
 */
export function playsFromCards(layout: Layout, strain: Strain, cards: readonly Card[], leader: Seat = 'W'): Play[] {
  const remaining = cloneLayout(layout);
  const plays: Play[] = [];
  let trick: Play[] = [];
  let turn: Seat = leader;
  for (const card of cards) {
    const hand = remaining[turn];
    const led = trick.length > 0 ? suitOf(trick[0]!.card) : null;
    if (!hand.includes(card) || !legalFrom(hand, led).includes(card)) break;
    hand.splice(hand.indexOf(card), 1);
    const play = { seat: turn, card };
    plays.push(play);
    trick.push(play);
    if (trick.length === 4) {
      turn = trickWinner(trick, strain);
      trick = [];
    } else {
      turn = nextSeat(turn);
    }
  }
  return plays;
}
