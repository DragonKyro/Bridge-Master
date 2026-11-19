// Double-dummy analysis over DDS (Bo Haglund's solver, compiled to WebAssembly
// by the bridge-dds package). Synchronous and CPU-bound: the app runs it in a
// Web Worker (worker.ts); the deal pipeline and the tests call it directly.

import { Dds, loadDds } from 'bridge-dds';
import { RANKS, SEATS, isDeclarerSide, rankValue, type Card, type Rank, type Strain } from '@/bridge/cards';
import { layoutToPbn } from '@/bridge/deal';
import { tricksLeft, type PlayView } from '@/bridge/play';

const DDS_STRAIN: Record<Strain, number> = { S: 0, H: 1, D: 2, C: 3, N: 4 };
const DDS_SUIT = ['S', 'H', 'D', 'C'] as const;
/** DDS seat numbers: N 0, E 1, S 2, W 3 — the same order as SEATS. */
const seatNo = (s: (typeof SEATS)[number]) => SEATS.indexOf(s);
const rankFromValue = (v: number): Rank => RANKS[14 - v]!;

export interface CardScore {
  card: Card;
  /** Tricks the side to play can take from here (the current trick included) after this card. */
  score: number;
}

export class DdSolver {
  private constructor(private readonly dds: Dds) {}

  static async create(): Promise<DdSolver> {
    return new DdSolver(new Dds(await loadDds()));
  }

  private deal(view: PlayView, strain: Strain) {
    const plays = view.current.plays;
    return {
      trump: DDS_STRAIN[strain],
      first: seatNo(view.current.leader),
      currentTrickSuit: [0, 1, 2].map((i) => (plays[i] ? DDS_SUIT.indexOf(plays[i]!.card[0] as (typeof DDS_SUIT)[number]) : 0)),
      currentTrickRank: [0, 1, 2].map((i) => (plays[i] ? rankValue(plays[i]!.card[1] as Rank) : 0)),
      remainCards: layoutToPbn(view.remaining, 'N'),
    };
  }

  /** Every legal card for the player to move, with its double-dummy score (equal cards listed separately). */
  scores(view: PlayView, strain: Strain): CardScore[] {
    if (view.turn === null) return [];
    const r = this.dds.SolveBoardPBN(this.deal(view, strain), -1, 3, 1);
    const out: CardScore[] = [];
    for (let i = 0; i < r.cards; i++) {
      const suit = DDS_SUIT[r.suit[i]!]!;
      out.push({ card: suit + rankFromValue(r.rank[i]!), score: r.score[i]! });
      const eq = r.equals[i]!;
      for (let v = 2; v <= 14; v++) if (eq & (1 << v)) out.push({ card: suit + rankFromValue(v), score: r.score[i]! });
    }
    return out;
  }

  /** The most tricks declarer's side can still take (from the current trick on) against best defence. */
  declarerMax(view: PlayView, strain: Strain): number {
    if (view.turn === null) return 0;
    const r = this.dds.SolveBoardPBN(this.deal(view, strain), -1, 1, 1);
    const best = r.score[0]!;
    return isDeclarerSide(view.turn) ? best : tricksLeft(view) - best;
  }

  /** Can declarer's side still reach `needed` total tricks (tricks already won count)? */
  canMake(view: PlayView, strain: Strain, needed: number): boolean {
    const want = needed - view.ns;
    if (want <= 0) return true;
    if (want > tricksLeft(view)) return false;
    return this.declarerMax(view, strain) >= want;
  }
}
