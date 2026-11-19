// Hands as text, the way bridge columns print them: one line per suit
// (♠ A K 7 2), highlighted cards in gold, played cards struck through when given.

import type { CSSProperties } from 'react';
import { SEAT_NAME, SUITS, rankLabel, type Card, type Rank, type Seat } from '@/bridge/cards';
import type { Layout } from '@/bridge/deal';
import { SuitSym } from './text';

export function HandText({
  seat,
  cards,
  highlight,
  gone,
  label,
  style,
}: {
  seat: Seat;
  cards: readonly Card[];
  highlight?: ReadonlySet<Card>;
  /** Cards to show struck through (already played). */
  gone?: ReadonlySet<Card>;
  label?: string;
  style?: CSSProperties;
}) {
  const order = 'AKQJT98765432';
  return (
    <div className={`hand-text hand-text-${seat}`} style={style}>
      <div className="hand-text-seat">{label ?? SEAT_NAME[seat]}</div>
      {SUITS.map((s) => {
        const ranks = cards.filter((c) => c[0] === s).sort((a, b) => order.indexOf(a[1]!) - order.indexOf(b[1]!));
        return (
          <div key={s} className="hand-text-suit">
            <SuitSym suit={s} />
            <span className="hand-text-ranks">
              {ranks.length === 0 ? (
                <span className="faint">—</span>
              ) : (
                ranks.map((c) => (
                  <span key={c} className={`hand-text-rank${highlight?.has(c) ? ' is-hl' : ''}${gone?.has(c) ? ' is-gone' : ''}`}>
                    {rankLabel(c[1] as Rank)}
                  </span>
                ))
              )}
            </span>
          </div>
        );
      })}
    </div>
  );
}

/** All four hands round a compass (North top, South bottom). */
export function DealDiagram({ layout, highlight, gone, center }: { layout: Layout; highlight?: ReadonlySet<Card>; gone?: ReadonlySet<Card>; center?: React.ReactNode }) {
  return (
    <div className="deal-diagram">
      <HandText seat="N" cards={layout.N} highlight={highlight} gone={gone} label="North · dummy" />
      <HandText seat="W" cards={layout.W} highlight={highlight} gone={gone} />
      <div className="deal-diagram-center">{center}</div>
      <HandText seat="E" cards={layout.E} highlight={highlight} gone={gone} />
      <HandText seat="S" cards={layout.S} highlight={highlight} gone={gone} label="South · you" />
    </div>
  );
}
