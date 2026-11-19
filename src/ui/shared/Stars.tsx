// Stars: gold (solved cleanly), silver (solved with undo or after seeing the solution), empty.

import type { CSSProperties } from 'react';
import type { Star as StarKind } from '@/store/progressStore';

const STAR = 'M12 2.6l2.9 6 6.5.8-4.8 4.5 1.2 6.5L12 17.3l-5.8 3.1 1.2-6.5L2.6 9.4l6.5-.8z';

/** The gradients the stars use; rendered once at the app root. */
export function StarDefs() {
  return (
    <svg width="0" height="0" style={{ position: 'absolute' }} aria-hidden>
      <defs>
        <linearGradient id="star-gold" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0" stopColor="#fff0b8" />
          <stop offset=".5" stopColor="#ebc35a" />
          <stop offset="1" stopColor="#c48d22" />
        </linearGradient>
        <linearGradient id="star-silver" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0" stopColor="#ffffff" />
          <stop offset=".55" stopColor="#c8d1da" />
          <stop offset="1" stopColor="#8b97a3" />
        </linearGradient>
      </defs>
    </svg>
  );
}

export function Star({ kind, className, style, title }: { kind: StarKind | 0; className?: string; style?: CSSProperties; title?: string }) {
  const cls = kind === 2 ? 'star-gold' : kind === 1 ? 'star-silver' : 'star-none';
  return (
    <svg
      className={`star ${cls}${className ? ` ${className}` : ''}`}
      viewBox="0 0 24 24"
      style={style}
      role={title ? 'img' : undefined}
      aria-label={title}
      aria-hidden={title ? undefined : true}
    >
      <path d={STAR} strokeWidth="1.1" strokeLinejoin="round" />
    </svg>
  );
}
