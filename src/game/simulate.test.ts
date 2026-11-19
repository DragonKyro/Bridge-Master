// Every deal, end to end with real DDS: the solution must make (the rigging
// never beats the right line), and a sample of other first decisions is
// reported (how often the rigging beats them).

import { describe, expect, it } from 'vitest';
import type { Deal } from '@/data/types';
import { DdSolver } from '@/dd/solver';
import { localApi } from './engine';
import { firstDecision, playOut } from '@/test/simulate';

const sets = import.meta.glob<Deal[]>('../data/sets/*.json', { eager: true, import: 'default' });
const deals = Object.values(sets).flat();

describe('all deals', () => {
  it('has the 540 deals', () => {
    expect(deals.length).toBe(540);
  });

  it('the solution makes on every deal', async () => {
    const api = localApi(await DdSolver.create());
    const failed: string[] = [];
    for (const deal of deals) {
      const r = await playOut(deal, api);
      if (!r.made || r.state.switches > 0) failed.push(`${deal.id}: ${r.tricks}/${deal.need} switches ${r.state.switches}`);
    }
    expect(failed).toEqual([]);
  });

  it('reports how often a different first decision fails', async () => {
    const api = localApi(await DdSolver.create());
    let tried = 0;
    let beaten = 0;
    let bySwitch = 0;
    for (const deal of deals) {
      const d = firstDecision(deal);
      if (!d) continue;
      for (const option of d.options.slice(0, 3)) {
        const r = await playOut(deal, api, (_h, i) => (i === d.at ? option : null));
        tried++;
        if (!r.made) beaten++;
        if (!r.made && r.state.switches > 0) bySwitch++;
      }
    }
    console.log(`first-decision alternatives: ${tried}, beaten ${beaten} (${bySwitch} by a layout switch)`);
    expect(tried).toBeGreaterThan(0);
  });
});
