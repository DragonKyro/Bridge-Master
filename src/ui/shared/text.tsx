// Bridge text: suit symbols in their colours, calls and contracts.

import { Fragment } from 'react';
import { SUIT_SYMBOL, rankLabel, type Card, type Rank, type Suit } from '@/bridge/cards';

const SYMBOL_SUIT: Record<string, Suit> = { '♠': 'S', '♥': 'H', '♦': 'D', '♣': 'C' };

export function SuitSym({ suit }: { suit: Suit }) {
  return <span className={`suit suit-${suit}`}>{SUIT_SYMBOL[suit]}</span>;
}

/** Text with any ♠♥♦♣ coloured. */
export function SuitText({ text }: { text: string }) {
  const parts = text.split(/([♠♥♦♣])/);
  return (
    <>
      {parts.map((p, i) =>
        SYMBOL_SUIT[p] ? (
          <span key={i} className={`suit suit-${SYMBOL_SUIT[p]}`}>
            {p}
          </span>
        ) : (
          <Fragment key={i}>{p}</Fragment>
        ),
      )}
    </>
  );
}

export function CardText({ card }: { card: Card }) {
  return (
    <span className="card-text">
      <SuitSym suit={card[0] as Suit} />
      {rankLabel(card[1] as Rank)}
    </span>
  );
}

/** "1D" → 1♦, "3NT", "Pass", "X" → Dbl, "XX" → Rdbl. */
export function Call({ call }: { call: string }) {
  if (call === 'Pass') return <span className="call call-pass">Pass</span>;
  if (call === 'X') return <span className="call call-x">Dbl</span>;
  if (call === 'XX') return <span className="call call-xx">Rdbl</span>;
  const m = /^([1-7])(NT|[SHDC])$/.exec(call);
  if (!m) return <span className="call">{call}</span>;
  return (
    <span className="call">
      {m[1]}
      {m[2] === 'NT' ? <span className="call-nt">NT</span> : <SuitSym suit={m[2] as Suit} />}
    </span>
  );
}

/** "4Sx" → 4♠×. */
export function Contract({ contract }: { contract: string }) {
  const m = /^([1-7])(NT|[SHDC])(x{0,2})$/i.exec(contract);
  if (!m) return <span>{contract}</span>;
  return (
    <span className="contract">
      <Call call={m[1]! + m[2]!} />
      {m[3] ? <span className="contract-x">{m[3].length === 2 ? '××' : '×'}</span> : null}
    </span>
  );
}
