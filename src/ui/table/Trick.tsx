// The middle of the table: the current trick (or the last one, until the next
// card), the defenders' seats, and a compass pointing at whoever is to play.
// The human's cards fly in from where they sat in the hand; the defenders'
// slide in from their seat and flip face up. A finished trick lights its
// winning card, then sweeps off toward the side that won it.

import { useLayoutEffect, useRef, type CSSProperties } from 'react';
import { isDeclarerSide, type Card, type Seat, type Strain } from '@/bridge/cards';
import { trickWinner, type Play, type PlayView } from '@/bridge/play';
import { paceMs, usePrefs } from '@/store/prefsStore';
import { CardImg } from '../cards/CardView';
import { land, prefersReducedMotion } from './flight';

interface Props {
  view: PlayView;
  strain: Strain;
  /** Before the opening lead is shown (the auction is up). */
  hideLead: boolean;
  /** The hand is over: the last trick stays put. */
  over: boolean;
  /** Whose turn it is, for the compass (null: nobody's). */
  turn: Seat | null;
  thinking: boolean;
}

export function Trick({ view, strain, hideLead, over, turn, thinking }: Props) {
  const speed = usePrefs((s) => s.speed);
  const pace = paceMs(speed);
  let plays: Play[] = view.current.plays;
  let trickNo = view.tricks.length;
  let complete = false;
  if (plays.length === 0 && view.tricks.length > 0) {
    const last = view.tricks[view.tricks.length - 1]!;
    plays = last.plays;
    trickNo = view.tricks.length - 1;
    complete = true;
  }
  if (hideLead) plays = [];
  const winner = complete ? trickWinner(plays, strain) : null;
  const sweepStyle = {
    '--sweep-delay': `${Math.round(pace.trick * 0.5)}ms`,
    '--sweep-ms': `${Math.round(pace.trick * 0.4)}ms`,
  } as CSSProperties;

  return (
    <div className={`trick${complete && !over ? ' trick-sweeping' : ''}${winner ? ` trick-won-${isDeclarerSide(winner) ? 'ns' : 'ew'} trick-winner-${winner}` : ''}`} style={sweepStyle}>
      <Compass turn={hideLead ? null : turn} thinking={thinking} />
      {plays.map((p) => (
        <TrickCard key={`${trickNo}-${p.seat}`} play={p} winner={winner === p.seat} />
      ))}
    </div>
  );
}

function TrickCard({ play, winner }: { play: Play; winner: boolean }) {
  const ref = useRef<HTMLDivElement | null>(null);
  const human = isDeclarerSide(play.seat);
  useLayoutEffect(() => {
    const el = ref.current;
    if (!el) return;
    const from = human ? land(play.card) : null;
    if (!from || prefersReducedMotion() || !el.animate) return;
    el.classList.add('trick-card-flown');
    const inner = el.querySelector<HTMLElement>('.trick-card-inner');
    const to = el.getBoundingClientRect();
    if (!inner) return;
    const dx = from.left + from.width / 2 - (to.left + to.width / 2);
    const dy = from.top + from.height / 2 - (to.top + to.height / 2);
    const s = to.width > 0 ? from.width / to.width : 1;
    inner.animate([{ transform: `translate(${dx}px, ${dy}px) scale(${s}) rotate(${play.seat === 'S' ? -8 : 8}deg)` }, { transform: 'none' }], {
      duration: 430,
      easing: 'cubic-bezier(.22,.9,.3,1.04)',
    });
    // Mount only: a card flies in once.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);
  return (
    <div ref={ref} className={`trick-card trick-${play.seat}${human ? '' : ' trick-card-flip'}${winner ? ' is-winner' : ''}`} data-card={play.card}>
      <div className="trick-card-inner">
        <span className="trick-face card">
          <CardImg card={play.card as Card} />
        </span>
        {!human && (
          <span className="trick-back card" aria-hidden>
            <CardImg card={null} />
          </span>
        )}
      </div>
    </div>
  );
}

function Compass({ turn, thinking }: { turn: Seat | null; thinking: boolean }) {
  return (
    <div className={`compass${turn ? ` compass-turn-${turn}` : ''}${thinking ? ' compass-thinking' : ''}`} aria-hidden>
      <svg viewBox="0 0 100 100">
        <circle cx="50" cy="50" r="46" className="compass-ring" />
        <circle cx="50" cy="50" r="38" className="compass-ring-inner" />
        <path d="M50 14L56 50L50 86L44 50Z" className="compass-ns" />
        <path d="M14 50L50 44L86 50L50 56Z" className="compass-ew" />
        <circle cx="50" cy="50" r="4" className="compass-hub" />
      </svg>
      {(['N', 'E', 'S', 'W'] as const).map((s) => (
        <span key={s} className={`compass-letter compass-${s}${turn === s ? ' is-turn' : ''}`}>
          {s}
        </span>
      ))}
    </div>
  );
}

/** A defender's place at the table: name, a little stack of backs with the count, a glow when it's their turn. */
export function DefenderSeat({ seat, count, active, thinking }: { seat: 'E' | 'W'; count: number; active: boolean; thinking: boolean }) {
  const shown = Math.min(count, 4);
  return (
    <div className={`defender defender-${seat}${active ? ' is-active' : ''}`}>
      <span className="defender-name">{seat === 'W' ? 'West' : 'East'}</span>
      <span className="defender-stack" aria-label={`${count} cards`}>
        {Array.from({ length: shown }, (_, i) => (
          <span key={i} className="defender-back card" style={{ '--j': i, '--k': shown } as CSSProperties}>
            <CardImg card={null} />
          </span>
        ))}
        <span className="defender-count">{count}</span>
      </span>
      {active && thinking && (
        <span className="dots" aria-hidden>
          <i />
          <i />
          <i />
        </span>
      )}
    </div>
  );
}
