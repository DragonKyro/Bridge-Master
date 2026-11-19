// Layouts (who holds which cards) and PBN.
//
// PBN deal strings name the first seat and then list the hands clockwise, each
// as spades.hearts.diamonds.clubs: "S:J32.A32.K32.AQ32 KT987.… …" is South,
// West, North, East.

import { SEATS, SUITS, compareCards, sortCards, suitOf, type Card, type Seat, type Suit } from './cards';

export type Layout = Record<Seat, Card[]>;

export function emptyLayout(): Layout {
  return { N: [], E: [], S: [], W: [] };
}

/** A hand from its PBN form "AK2.QJ3..T98". */
export function parseHand(pbn: string): Card[] {
  const parts = pbn.split('.');
  if (parts.length !== 4) throw new Error(`bad PBN hand "${pbn}"`);
  const cards: Card[] = [];
  parts.forEach((ranks, i) => {
    for (const r of ranks) cards.push(SUITS[i]! + r);
  });
  return sortCards(cards);
}

export function handToPbn(cards: readonly Card[]): string {
  return SUITS.map((s) =>
    sortCards(cards.filter((c) => suitOf(c) === s))
      .map((c) => c[1])
      .join(''),
  ).join('.');
}

/** "S:… … … …" → layout. */
export function parsePbn(pbn: string): Layout {
  const [first, rest] = pbn.trim().split(':');
  const hands = (rest ?? '').trim().split(/\s+/);
  if (!first || !SEATS.includes(first as Seat) || hands.length !== 4) throw new Error(`bad PBN deal "${pbn}"`);
  const layout = emptyLayout();
  let seat = SEATS.indexOf(first as Seat);
  for (const h of hands) {
    layout[SEATS[seat]!] = parseHand(h);
    seat = (seat + 1) % 4;
  }
  return layout;
}

/** Layout → PBN starting from `first` (DDS wants "N:" order; the data uses "S:"). */
export function layoutToPbn(layout: Layout, first: Seat = 'N'): string {
  const start = SEATS.indexOf(first);
  const hands = [0, 1, 2, 3].map((k) => handToPbn(layout[SEATS[(start + k) % 4]!]));
  return `${first}:${hands.join(' ')}`;
}

export function cloneLayout(layout: Layout): Layout {
  return { N: [...layout.N], E: [...layout.E], S: [...layout.S], W: [...layout.W] };
}

/** A stable key for comparing layouts. */
export function layoutKey(layout: Layout): string {
  return layoutToPbn(layout, 'N');
}

/** Problems with a full deal (13 cards each, 52 distinct); empty when fine. */
export function layoutProblems(layout: Layout): string[] {
  const problems: string[] = [];
  const seen = new Set<Card>();
  for (const s of SEATS) {
    if (layout[s].length !== 13) problems.push(`${s} has ${layout[s].length} cards`);
    for (const c of layout[s]) {
      if (seen.has(c)) problems.push(`${c} appears twice`);
      seen.add(c);
    }
  }
  if (seen.size !== 52 && problems.length === 0) problems.push(`${seen.size} distinct cards`);
  return problems;
}

export function holderOf(layout: Layout, card: Card): Seat | null {
  for (const s of SEATS) if (layout[s].includes(card)) return s;
  return null;
}

export function suitCards(cards: readonly Card[], suit: Suit): Card[] {
  return cards.filter((c) => suitOf(c) === suit).sort(compareCards);
}

/** High-card points (A4 K3 Q2 J1). */
export function hcp(cards: readonly Card[]): number {
  let n = 0;
  for (const c of cards) n += ({ A: 4, K: 3, Q: 2, J: 1 } as Record<string, number>)[c[1]!] ?? 0;
  return n;
}
