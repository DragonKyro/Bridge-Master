// A face-up hand as an overlapping fan, grouped by suit (trumps first, colours
// alternating). The human plays South's and dummy's cards from here: one tap,
// or a tap to raise and another to play (prefs.oneTap). Cards deal in when the
// hand opens and slide together as cards leave (FLIP).

import { useLayoutEffect, useRef, useState, type CSSProperties } from 'react';
import { suitOf, type Card, type Seat, type Strain, type Suit } from '@/bridge/cards';
import { usePrefs } from '@/store/prefsStore';
import { CardView } from '../cards/CardView';
import { launch, prefersReducedMotion } from './flight';
import { playSound } from '../sounds';

/** Suit order for display: trumps first, red and black alternating. */
export function displaySuits(strain: Strain): Suit[] {
  switch (strain) {
    case 'H':
      return ['H', 'S', 'D', 'C'];
    case 'D':
      return ['D', 'S', 'H', 'C'];
    case 'C':
      return ['C', 'H', 'S', 'D'];
    default:
      return ['S', 'H', 'C', 'D'];
  }
}

export function sortForDisplay(cards: readonly Card[], strain: Strain): Card[] {
  const order = displaySuits(strain);
  const rank = 'AKQJT98765432';
  return [...cards].sort((a, b) => order.indexOf(suitOf(a)) - order.indexOf(suitOf(b)) || rank.indexOf(a[1]!) - rank.indexOf(b[1]!));
}

interface Props {
  seat: Seat;
  cards: readonly Card[];
  strain: Strain;
  /** The human may play from this hand now. */
  active: boolean;
  legal: ReadonlySet<Card>;
  onPlay: (card: Card) => void;
  /** Gold-ringed cards (hints). */
  marked?: ReadonlySet<Card>;
  /** Changes when a new deal is dealt (replays the deal-in). */
  dealKey: string;
}

export function HandFan({ seat, cards, strain, active, legal, onPlay, marked, dealKey }: Props) {
  const oneTap = usePrefs((s) => s.oneTap);
  const sound = usePrefs((s) => s.sound);
  const [raised, setRaised] = useState<Card | null>(null);
  const ref = useRef<HTMLDivElement | null>(null);
  const prev = useRef<Map<string, DOMRect>>(new Map());
  const sorted = sortForDisplay(cards, strain);
  const suitsHeld = new Set(sorted.map(suitOf)).size;

  if (raised && (!active || !cards.includes(raised))) setRaised(null);

  // FLIP: the cards that stay slide from where they were.
  useLayoutEffect(() => {
    const el = ref.current;
    if (!el) return;
    const now = new Map<string, DOMRect>();
    el.querySelectorAll<HTMLElement>('.card[data-card]').forEach((c) => now.set(c.dataset.card!, c.getBoundingClientRect()));
    if (!prefersReducedMotion()) {
      el.querySelectorAll<HTMLElement>('.card[data-card]').forEach((c) => {
        const before = prev.current.get(c.dataset.card!);
        const after = now.get(c.dataset.card!);
        if (!before || !after) return;
        const dx = before.left - after.left;
        if (Math.abs(dx) < 1) return;
        c.animate([{ translate: `${dx}px 0` }, { translate: '0 0' }], { duration: 320, easing: 'cubic-bezier(.2,.8,.2,1)' });
      });
    }
    prev.current = now;
  });

  const play = (card: Card, target: HTMLElement) => {
    launch(card, target.getBoundingClientRect());
    setRaised(null);
    onPlay(card);
  };

  let suitIndex = -1;
  let lastSuit: Suit | null = null;
  return (
    <div
      ref={ref}
      key={dealKey}
      className={`fan fan-${seat}${active ? ' fan-active' : ''}`}
      style={{ '--n': sorted.length, '--gaps': Math.max(0, suitsHeld - 1) } as CSSProperties}
      onClick={(e) => {
        if (e.target === e.currentTarget) setRaised(null);
      }}
    >
      {sorted.map((card, i) => {
        const suit = suitOf(card);
        const newSuit = suit !== lastSuit;
        if (newSuit) suitIndex++;
        lastSuit = suit;
        const playable = active && legal.has(card);
        const cls = [
          'fan-card',
          newSuit && i > 0 && 'fan-suit-start',
          playable && 'is-playable',
          active && !playable && 'is-dim',
          raised === card && 'is-raised',
          marked?.has(card) && 'is-marked',
        ]
          .filter(Boolean)
          .join(' ');
        return (
          <CardView
            key={card}
            card={card}
            className={cls}
            style={{ '--i': i, '--s': suitIndex } as CSSProperties}
            disabled={!playable}
            // Always a button (a span ↔ button swap would remount the card and replay its deal-in).
            onClick={(e) => {
              if (!playable) return;
              const target = e.currentTarget;
              if (oneTap || raised === card) play(card, target);
              else {
                setRaised(card);
                if (sound) playSound('tap');
              }
            }}
          />
        );
      })}
    </div>
  );
}
