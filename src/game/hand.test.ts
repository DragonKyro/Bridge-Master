import { describe, expect, it } from 'vitest';
import type { Deal } from '@/data/types';
import { applyPlay, handView, scriptedCard, startHand } from './hand';

const sets = import.meta.glob<Deal[]>('../data/sets/L1A.json', { eager: true, import: 'default' });
const deal = Object.values(sets)[0]!.find((d) => d.id === '1A-1')!;

describe('the script', () => {
  it('starts with the opening lead down and the defenders on the script', () => {
    const h = startHand(deal);
    expect(h.plays).toEqual([{ seat: 'W', card: 'ST' }]);
    expect(handView(h).turn).toBe('N');
    const afterDuck = applyPlay(h, 'S4');
    expect(afterDuck.onScript).toBe(true);
    expect(scriptedCard(afterDuck)).toBe('SA');
  });

  it('an equivalent card stays on the script', () => {
    let h = startHand(deal);
    h = applyPlay(h, 'S4');
    h = applyPlay(h, 'SA');
    // The script has South drop the ♠2; the ♠3 is the same card here.
    h = applyPlay(h, 'S3');
    expect(h.onScript).toBe(true);
    expect(h.script[3]).toBe('S3');
    expect(h.script).toContain('S2');
  });

  it('a different card leaves the script', () => {
    const h = applyPlay(startHand(deal), 'SQ');
    expect(h.onScript).toBe(false);
    expect(h.deviatedAt).toBe(1);
    expect(scriptedCard(h)).toBeNull();
  });
});
