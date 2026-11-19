// One playing card (art from cardArt). `card` null draws the back.

import type { CSSProperties, MouseEvent } from 'react';
import { cardLabel, type Card } from '@/bridge/cards';
import { usePrefs } from '@/store/prefsStore';
import { cardSrc, type CardLayout } from './cardArt';

export function CardImg({ card, layout = 'compact' }: { card: Card | null; layout?: CardLayout }) {
  const fourColor = usePrefs((s) => s.fourColor);
  return <img className="card-img" src={cardSrc(card, layout, fourColor ? 'four' : 'two')} alt={card ? cardLabel(card) : 'card back'} draggable={false} />;
}

export function CardView({
  card,
  layout = 'compact',
  className,
  style,
  onClick,
  disabled,
  label,
}: {
  card: Card | null;
  layout?: CardLayout;
  className?: string;
  style?: CSSProperties;
  onClick?: (e: MouseEvent<HTMLButtonElement>) => void;
  disabled?: boolean;
  label?: string;
}) {
  const cls = `card${className ? ` ${className}` : ''}`;
  if (onClick) {
    return (
      <button type="button" className={cls} style={style} onClick={onClick} disabled={disabled} data-card={card ?? undefined} aria-label={label ?? (card ? cardLabel(card) : 'card')}>
        <CardImg card={card} layout={layout} />
      </button>
    );
  }
  return (
    <span className={cls} style={style} data-card={card ?? undefined}>
      <CardImg card={card} layout={layout} />
    </span>
  );
}
