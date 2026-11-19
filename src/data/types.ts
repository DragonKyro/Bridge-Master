// The app's deal format, written by scripts/build-deals.ts from the scraped
// BBO Bridge Master files. One JSON file per set (src/data/sets/L1-A.json …),
// loaded on demand; catalog.json (bundled) lists every deal.

import type { Card, Seat } from '@/bridge/cards';

export type Vulnerability = 'None' | 'NS' | 'EW' | 'Both';

export interface Deal {
  /** "1A-7": level, set, number. */
  id: string;
  level: number;
  set: string;
  num: number;
  /** "3NT", "4S", "4Sx". */
  contract: string;
  /** Tricks declarer needs. */
  need: number;
  dealer: Seat;
  vul: Vulnerability;
  /** Calls from the dealer on: "1D", "Pass", "X", "XX", "2NT". */
  auction: string[];
  /** West's opening lead. */
  lead: Card;
  /** The layout the hand is played on, PBN from North ("N:… … … …"). */
  layout: string;
  /**
   * The other layouts BBO's review shows (same North / South) on which the
   * solution still makes — the defenders may switch to one of these, when it
   * still fits every card seen, to beat a line that isn't the solution's.
   */
  alts: string[];
  /** The solution's plays, from the opening lead (seats follow from the layout). */
  line: Card[];
  /** The solution relies on the scripted defence (best defence would beat it): off-script the defenders play double dummy anyway. */
  scriptedDefence?: boolean;
  /** No layout in BBO's review makes double dummy, so one defender card was swapped (scripts/build-deals.ts repair()). */
  repaired?: boolean;
  /** The commentary, by paragraph. */
  notes: string[];
  /** The review, step by step (BBO's "movie"). */
  review: ReviewStep[];
}

export interface ReviewStep {
  /** Hands still held, PBN from North; omitted when unchanged from the previous step. */
  h?: string;
  /** Cards in the current trick: "WST N S4" → seat + card, space separated ("" when none). */
  t: string;
  /** Tricks won so far by declarer / the defence. */
  d: number;
  f: number;
  /** Highlighted cards, seat + card ("SCA NCK"). */
  hl?: string;
  /** Commentary shown: [paragraph, characters shown], or literal text when it isn't a paragraph prefix. */
  c: [number, number] | string;
}

export interface CatalogDeal {
  id: string;
  num: number;
  contract: string;
}

export interface CatalogSet {
  /** "1A" */
  key: string;
  level: number;
  set: string;
  deals: CatalogDeal[];
}

export interface CatalogLevel {
  level: number;
  name: string;
  sets: CatalogSet[];
}

export interface Catalog {
  total: number;
  levels: CatalogLevel[];
}
