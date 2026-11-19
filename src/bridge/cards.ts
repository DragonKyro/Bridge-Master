// Cards, seats and strains. A card is suit + rank, the way the BBO data writes
// it: 'SA' (ace of spades), 'HT' (ten of hearts), 'C2'. Seats go clockwise
// N E S W; South is always declarer, so N/S are "us" and E/W the defenders.

export type Suit = 'S' | 'H' | 'D' | 'C';
export type Rank = 'A' | 'K' | 'Q' | 'J' | 'T' | '9' | '8' | '7' | '6' | '5' | '4' | '3' | '2';
export type Card = string;
export type Seat = 'N' | 'E' | 'S' | 'W';
export type Strain = Suit | 'N';

export const SUITS: readonly Suit[] = ['S', 'H', 'D', 'C'];
/** High to low. */
export const RANKS: readonly Rank[] = ['A', 'K', 'Q', 'J', 'T', '9', '8', '7', '6', '5', '4', '3', '2'];
/** Clockwise from North. */
export const SEATS: readonly Seat[] = ['N', 'E', 'S', 'W'];

export const SUIT_SYMBOL: Record<Suit, string> = { S: '♠', H: '♥', D: '♦', C: '♣' };
export const SUIT_NAME: Record<Suit, string> = { S: 'spades', H: 'hearts', D: 'diamonds', C: 'clubs' };
export const SEAT_NAME: Record<Seat, string> = { N: 'North', E: 'East', S: 'South', W: 'West' };

export const suitOf = (c: Card): Suit => c[0] as Suit;
export const rankOf = (c: Card): Rank => c[1] as Rank;
/** 14 for the ace down to 2. */
export const rankValue = (r: Rank): number => 14 - RANKS.indexOf(r);
export const cardValue = (c: Card): number => rankValue(rankOf(c));

export const nextSeat = (s: Seat): Seat => SEATS[(SEATS.indexOf(s) + 1) % 4]!;
export const partnerOf = (s: Seat): Seat => SEATS[(SEATS.indexOf(s) + 2) % 4]!;
export const isDeclarerSide = (s: Seat): boolean => s === 'N' || s === 'S';

/** Rank as printed: 'T' → '10'. */
export const rankLabel = (r: Rank): string => (r === 'T' ? '10' : r);
export const cardLabel = (c: Card): string => SUIT_SYMBOL[suitOf(c)] + rankLabel(rankOf(c));

/** Sort key: suits in S H D C order, high to low within a suit. */
export function compareCards(a: Card, b: Card): number {
  const ds = SUITS.indexOf(suitOf(a)) - SUITS.indexOf(suitOf(b));
  return ds !== 0 ? ds : cardValue(b) - cardValue(a);
}

export function sortCards(cards: readonly Card[]): Card[] {
  return [...cards].sort(compareCards);
}

export const FULL_DECK: readonly Card[] = SUITS.flatMap((s) => RANKS.map((r) => s + r));
