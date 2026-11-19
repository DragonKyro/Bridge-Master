// Line icons (24 × 24, stroked).

const PATHS = {
  back: 'M15 5l-7 7 7 7',
  undo: 'M9 14L4 9l5-5M4 9h10a6 6 0 010 12h-3',
  restart: 'M4 12a8 8 0 108-8 8.4 8.4 0 00-6 2.6L4 8M4 3v5h5',
  book: 'M4 5.5A2.5 2.5 0 016.5 3H20v15H6.5A2.5 2.5 0 004 20.5zM4 20.5A2.5 2.5 0 016.5 18H20v3H6.5A2.5 2.5 0 014 20.5zM9 7h7M9 10.5h5',
  auction: 'M4 5h16M4 10h16M4 15h10M4 20h7',
  gear: 'M12 15a3 3 0 100-6 3 3 0 000 6zM19.4 15a1.7 1.7 0 00.3 1.8l.1.1a2 2 0 11-2.8 2.8l-.1-.1a1.7 1.7 0 00-1.8-.3 1.7 1.7 0 00-1 1.5V21a2 2 0 11-4 0v-.1a1.7 1.7 0 00-1.1-1.5 1.7 1.7 0 00-1.8.3l-.1.1a2 2 0 11-2.8-2.8l.1-.1a1.7 1.7 0 00.3-1.8 1.7 1.7 0 00-1.5-1H3a2 2 0 110-4h.1a1.7 1.7 0 001.5-1.1 1.7 1.7 0 00-.3-1.8l-.1-.1a2 2 0 112.8-2.8l.1.1a1.7 1.7 0 001.8.3H9a1.7 1.7 0 001-1.5V3a2 2 0 114 0v.1a1.7 1.7 0 001 1.5 1.7 1.7 0 001.8-.3l.1-.1a2 2 0 112.8 2.8l-.1.1a1.7 1.7 0 00-.3 1.8V9a1.7 1.7 0 001.5 1H21a2 2 0 110 4h-.1a1.7 1.7 0 00-1.5 1z',
  play: 'M7 4.5v15l12-7.5z',
  pause: 'M8 5v14M16 5v14',
  prev: 'M15 5l-7 7 7 7',
  next: 'M9 5l7 7-7 7',
  first: 'M6 5v14M18 5l-7 7 7 7',
  last: 'M18 5v14M6 5l7 7-7 7',
  close: 'M6 6l12 12M18 6L6 18',
  user: 'M12 12a4 4 0 100-8 4 4 0 000 8zM4 21a8 8 0 0116 0',
  cloud: 'M7 18a5 5 0 01-.6-10A6.5 6.5 0 0119 9.5 4.3 4.3 0 0118 18z',
  cloudOff: 'M3 3l18 18M8.5 8.4A6.4 6.4 0 0119 9.5a4.3 4.3 0 012.2 6.9M17 18H7a5 5 0 01-1.2-9.9',
  arrow: 'M5 12h14M13 6l6 6-6 6',
} as const;

export type IconName = keyof typeof PATHS;

export function Icon({ name, size, className }: { name: IconName; size?: 'sm'; className?: string }) {
  const filled = name === 'play';
  return (
    <svg
      className={`icon${size ? ` icon-${size}` : ''}${className ? ` ${className}` : ''}`}
      viewBox="0 0 24 24"
      aria-hidden
      fill={filled ? 'currentColor' : 'none'}
      stroke="currentColor"
      strokeWidth={filled ? 0 : 2}
      strokeLinecap="round"
      strokeLinejoin="round"
    >
      <path d={PATHS[name]} />
    </svg>
  );
}
