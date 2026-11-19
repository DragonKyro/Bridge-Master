// Cards flying from a hand to the trick. Just before the human's card is
// played, its spot in the fan is measured (launch); when the card mounts in
// the trick (same update) it animates in from there (land). UI only.

import type { Card } from '@/bridge/cards';

const launches = new Map<Card, { rect: DOMRect; at: number }>();
const FRESH_MS = 1500;

export function launch(card: Card, rect: DOMRect): void {
  launches.set(card, { rect, at: performance.now() });
}

/** Where `card` left the hand from (taken once), or null. */
export function land(card: Card): DOMRect | null {
  const l = launches.get(card);
  launches.delete(card);
  return l && performance.now() - l.at < FRESH_MS ? l.rect : null;
}

export function prefersReducedMotion(): boolean {
  return typeof window !== 'undefined' && !!window.matchMedia?.('(prefers-reduced-motion: reduce)').matches;
}
