// Which of the double-dummy-best cards a defender plays. DDS says which cards
// hold declarer to the fewest tricks; among those, play like a person would:
// low in second seat, cheaply high in third and fourth, the top of a
// sequence on lead, discards from the least useful suit.

import { cardValue, isDeclarerSide, partnerOf, suitOf, type Card, type Strain, type Suit } from '@/bridge/cards';
import { ledSuit, trickWinner, type PlayView } from '@/bridge/play';
import type { CardScore } from '@/dd/solver';

export function naturalCard(view: PlayView, strain: Strain, scores: readonly CardScore[]): Card {
  if (scores.length === 0) throw new Error('no cards to choose from');
  const best = Math.max(...scores.map((s) => s.score));
  const good = scores.filter((s) => s.score === best).map((s) => s.card);
  if (good.length === 1) return good[0]!;
  const seat = view.turn!;
  const hand = view.remaining[seat];
  const led = ledSuit(view.current);
  const low = (cards: Card[]) => cards.reduce((a, b) => (cardValue(b) < cardValue(a) ? b : a));

  if (led === null) return leadChoice(good, hand);

  const following = good.filter((c) => suitOf(c) === led);
  if (following.length > 0) {
    const plays = view.current.plays;
    const winnerNow = trickWinner(plays, strain);
    const partnerWinning = winnerNow === partnerOf(seat) && !isDeclarerSide(winnerNow);
    if (plays.length === 1 || partnerWinning) return low(following);
    // Third / fourth seat: the cheapest card that takes the trick, if one is as good.
    const winners = following.filter((c) => trickWinner([...plays, { seat, card: c }], strain) === seat);
    return winners.length > 0 ? low(winners) : low(following);
  }

  // Void: ruff low if ruffing is best, otherwise discard from the least useful suit.
  const ruffs = good.filter((c) => strain !== 'N' && suitOf(c) === strain);
  const discards = good.filter((c) => !(strain !== 'N' && suitOf(c) === strain));
  if (discards.length === 0) return low(ruffs);
  return discardChoice(discards, hand);
}

/** Leading: the top of touching honours, else a low card; prefer the suit with the most cards among the good ones. */
function leadChoice(good: Card[], hand: readonly Card[]): Card {
  const bySuit = groupBySuit(good);
  const suits = [...bySuit.keys()].sort((a, b) => bySuit.get(b)!.length - bySuit.get(a)!.length);
  const suit = suits[0]!;
  const cards = bySuit.get(suit)!.sort((a, b) => cardValue(b) - cardValue(a));
  const top = cards[0]!;
  const held = hand.filter((c) => suitOf(c) === suit);
  // Touching honours: lead the top of the sequence.
  if (cardValue(top) >= 10 && held.some((c) => cardValue(c) === cardValue(top) - 1)) return top;
  return cards[cards.length - 1]!;
}

/** Discard the lowest card of the suit with the fewest high cards (ties: the longest). */
function discardChoice(good: Card[], hand: readonly Card[]): Card {
  const bySuit = groupBySuit(good);
  const worth = (s: Suit) => hand.filter((c) => suitOf(c) === s && cardValue(c) >= 11).length;
  const length = (s: Suit) => hand.filter((c) => suitOf(c) === s).length;
  const suit = [...bySuit.keys()].sort((a, b) => worth(a) - worth(b) || length(b) - length(a))[0]!;
  return bySuit.get(suit)!.reduce((a, b) => (cardValue(b) < cardValue(a) ? b : a));
}

function groupBySuit(cards: Card[]): Map<Suit, Card[]> {
  const m = new Map<Suit, Card[]>();
  for (const c of cards) m.set(suitOf(c), [...(m.get(suitOf(c)) ?? []), c]);
  return m;
}
