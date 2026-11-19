import { describe, expect, it } from 'vitest';
import { mergeDeal, mergeProgress } from './progressStore';

describe('progress merging (local ⇄ cloud)', () => {
  it('keeps the better star, the most attempts, and when the best star was first earned', () => {
    expect(mergeDeal({ b: 1, t: 3, at: 100 }, { b: 2, t: 1, at: 200 })).toEqual({ b: 2, t: 3, at: 200 });
    expect(mergeDeal({ b: 2, t: 2, at: 300 }, { b: 2, t: 5, at: 150 })).toEqual({ b: 2, t: 5, at: 150 });
    expect(mergeDeal({ t: 4 }, { b: 1, t: 1, at: 50 })).toEqual({ b: 1, t: 4, at: 50 });
    expect(mergeDeal({ t: 2 }, undefined)).toEqual({ t: 2 });
  });

  it('merges whole maps', () => {
    const merged = mergeProgress({ '1A-1': { b: 1, t: 1, at: 1 } }, { '1A-1': { b: 2, t: 1, at: 2 }, '1A-2': { t: 3 } });
    expect(merged).toEqual({ '1A-1': { b: 2, t: 1, at: 2 }, '1A-2': { t: 3 } });
  });
});
