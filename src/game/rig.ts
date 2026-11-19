// The defenders' "cheating": after declarer leaves the solution, look for a
// layout they could equally well hold (one of the deal's alternatives that
// fits every card seen) on which declarer can no longer make — and if the
// current layout still lets declarer make, switch to it. Runs in the solver
// worker.

import type { Strain } from '@/bridge/cards';
import { parsePbn } from '@/bridge/deal';
import { replay, type Play } from '@/bridge/play';
import type { DdSolver } from '@/dd/solver';

/**
 * Index into `alternatives` of a layout that beats declarer from here, or -1
 * (declarer is already beaten on `current`, or no alternative beats them).
 */
export function findPunisher(dd: DdSolver, current: string, alternatives: readonly string[], strain: Strain, plays: readonly Play[], need: number): number {
  if (!dd.canMake(replay(parsePbn(current), strain, plays), strain, need)) return -1;
  for (let i = 0; i < alternatives.length; i++) {
    let view;
    try {
      view = replay(parsePbn(alternatives[i]!), strain, plays);
    } catch {
      continue; // doesn't fit the cards seen
    }
    if (!dd.canMake(view, strain, need)) return i;
  }
  return -1;
}
