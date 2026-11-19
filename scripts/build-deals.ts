// Build the app's deal files from the scraped BBO Bridge Master data.
//
//   npm run deals            (vite-node scripts/build-deals.ts)
//
// For every deal:
//  1. Rebuild the review's play line and layouts from its snapshots (lib/raw).
//  2. Pick the solution: of the lines the review plays out (each line just
//     before a rewind, and the last one), the longest after which declarer can
//     still make the contract double dummy on the layout shown. Its layout is
//     the one the hand is dealt with.
//  3. Keep the review's other layouts (North / South unchanged) on which the
//     solution still makes at every point the hand's own layout does — the
//     defenders may switch to those to beat other lines (src/game/rig.ts).
//  4. Compact the review steps for the solution player.
// Writes src/data/sets/L<level><set>.json and src/data/catalog.json.

import fs from 'node:fs';
import path from 'node:path';
import { SEATS, cardValue, isDeclarerSide, sortCards, type Seat } from '@/bridge/cards';
import { hcp, layoutKey, layoutToPbn, parsePbn, type Layout } from '@/bridge/deal';
import { legalPlays, replay, type Play } from '@/bridge/play';
import type { Catalog, CatalogLevel, Deal, ReviewStep, Vulnerability } from '@/data/types';
import { DdSolver } from '@/dd/solver';
import { parseContract, readRaw, reconstruct, type RawDeal, type StepState } from './lib/raw';

const RAW = 'data/bbo_bridgemaster';
const OUT = 'src/data';

const dd = await DdSolver.create();
const raws = readRaw(RAW);
const index = JSON.parse(fs.readFileSync(path.join(RAW, 'index.json'), 'utf8')) as {
  levels: Array<{ level: number; level_name: string }>;
};

const report: string[] = [];
const stats = { deals: 0, noScript: 0, repaired: 0, unplayable: 0, scriptedDefence: 0, withAlts: 0, alts: 0, altsRejected: 0, literalCommentary: 0, steps: 0 };
const sets = new Map<string, Deal[]>();

for (const { deal: d, set } of raws) {
  const tag = `${d.level}${d.deal_id}`;
  const { strain } = parseContract(d.contract);
  const need = d.par_tricks;
  const states = reconstruct(d);

  // ---- 2. the solution line and its layout
  const good = states.filter((s) => !s.foreign);
  const leaves: StepState[] = [];
  good.forEach((s, i) => {
    const next = good[i + 1];
    if (!next || next.rewound > 0) leaves.push(s);
  });
  let best: { line: Play[]; layout: Layout } | null = null;
  for (const leaf of leaves) {
    if (!leaf.line.some((p) => isDeclarerSide(p.seat))) continue;
    if (leaf.line[0]?.card !== d.opening_lead) continue;
    let view;
    try {
      view = replay(leaf.layout, strain, leaf.line);
    } catch {
      continue;
    }
    const ok = view.done ? view.ns >= need : dd.canMake(view, strain, need);
    if (ok && (!best || leaf.line.length > best.line.length)) best = { line: leaf.line, layout: leaf.layout };
  }
  let repaired = false;
  if (!best) {
    // No review line makes: no script. Deal a review layout that makes double
    // dummy after the lead, or failing that a nearby one (repair()).
    stats.noScript++;
    const leadOnly: Play[] = [{ seat: 'W', card: d.opening_lead }];
    const makes = (l: Layout) => dd.canMake(replay(l, strain, leadOnly), strain, need);
    const pool = [parsePbn(d.deal_pbn), ...good.map((s) => s.layout)].filter((l) => l.W.includes(d.opening_lead));
    const ok = pool.find(makes);
    if (ok) {
      best = { line: leadOnly, layout: ok };
      report.push(`${tag}: no review line makes; no script, a review layout that makes`);
    } else {
      const fixed = repair(parsePbn(d.deal_pbn), d.opening_lead, makes);
      if (fixed) {
        repaired = true;
        stats.repaired++;
        best = { line: leadOnly, layout: fixed.layout };
        report.push(`${tag}: no layout makes double dummy; repaired by swapping ${fixed.swap}`);
      } else {
        stats.unplayable++;
        best = { line: leadOnly, layout: parsePbn(d.deal_pbn) };
        report.push(`${tag}: UNPLAYABLE — nothing makes double dummy, no single swap fixes it`);
      }
    }
  }
  const { line, layout } = best;
  const cards = line.map((p) => p.card);

  // Double-dummy verdict after each declarer play along the line on the hand's own layout.
  const verdicts = (l: Layout): Array<boolean | null> => {
    const out: Array<boolean | null> = [];
    let view = replay(l, strain, []);
    for (let i = 0; i < cards.length; i++) {
      const seat = view.turn!;
      if (!legalPlays(view).includes(cards[i]!)) {
        // A defender doesn't hold the scripted card here: this layout drops out of the script.
        for (let j = i; j < cards.length; j++) out.push(null);
        return out;
      }
      view = replay(l, strain, line.slice(0, i + 1));
      out.push(isDeclarerSide(seat) ? dd.canMake(view, strain, need) : null);
    }
    return out;
  };
  const own = verdicts(layout);
  const startView = replay(layout, strain, line.slice(0, 1));
  const scriptedDefence = !dd.canMake(startView, strain, need) || own.some((v) => v === false);
  if (scriptedDefence) stats.scriptedDefence++;

  // ---- 3. alternative layouts
  const seen = new Set([layoutKey(layout)]);
  const alts: string[] = [];
  const hasScript = cards.length > 1;
  for (const l of hasScript ? [parsePbn(d.deal_pbn), ...good.map((s) => s.layout)] : []) {
    const key = layoutKey(l);
    if (seen.has(key)) continue;
    seen.add(key);
    if (!l.W.includes(d.opening_lead)) continue;
    const theirs = verdicts(l);
    const fair = theirs.every((v, i) => v !== false || own[i] === false);
    if (fair) alts.push(layoutToPbn(l, 'N'));
    else stats.altsRejected++;
  }
  if (alts.length) stats.withAlts++;
  stats.alts += alts.length;

  // ---- 4. review steps
  const review = compactReview(d);
  stats.steps += review.length;

  const deal: Deal = {
    id: tag,
    level: d.level,
    set,
    num: Number(d.deal_id.split('-')[1]),
    contract: d.contract,
    need,
    dealer: d.dealer,
    vul: d.vulnerability as Vulnerability,
    auction: d.auction.map(normaliseCall),
    lead: d.opening_lead,
    layout: layoutToPbn(layout, 'N'),
    alts,
    line: cards,
    ...(scriptedDefence && hasScript ? { scriptedDefence: true } : {}),
    ...(repaired ? { repaired: true } : {}),
    notes: d.commentary_paragraphs,
    review,
  };
  const key = `${d.level}${set}`;
  sets.set(key, [...(sets.get(key) ?? []), deal]);
  stats.deals++;
}

/**
 * The nearest layout that makes: swap one defender card between West and East
 * within a suit (suit lengths, and so the bidding's shape clues, unchanged),
 * moving as few high-card points as possible. The opening lead stays put.
 */
function repair(base: Layout, lead: string, makes: (l: Layout) => boolean): { layout: Layout; swap: string } | null {
  const options: Array<{ layout: Layout; swap: string; cost: number }> = [];
  for (const w of base.W) {
    if (w === lead) continue;
    for (const e of base.E) {
      if (e[0] !== w[0]) continue;
      const layout = { ...base, W: sortCards([...base.W.filter((c) => c !== w), e]), E: sortCards([...base.E.filter((c) => c !== e), w]) };
      options.push({ layout, swap: `W ${w} / E ${e}`, cost: Math.abs(hcp([w]) - hcp([e])) * 10 + Math.abs(cardValue(w) - cardValue(e)) });
    }
  }
  options.sort((a, b) => a.cost - b.cost);
  return options.find((o) => makes(o.layout)) ?? null;
}

function normaliseCall(c: string): string {
  const t = c.trim();
  if (/^pass$/i.test(t) || t === 'P') return 'Pass';
  if (/^(x|dbl|double)$/i.test(t)) return 'X';
  if (/^(xx|rdbl|redouble)$/i.test(t)) return 'XX';
  return t.replace(/^([1-7])N$/, '$1NT');
}

function compactReview(d: RawDeal): ReviewStep[] {
  const out: ReviewStep[] = [];
  let prevH = '';
  let para = 0;
  for (const st of d.solution_steps) {
    const h = layoutToPbn(parsePbn(st.hands_pbn), 'N');
    const t = SEATS.filter((s) => st.trick_cards[s]).map((s) => s + st.trick_cards[s]).join(' ');
    const hl: string[] = [];
    for (const s of SEATS) {
      const bySuit = st.highlighted[s as Seat];
      if (!bySuit) continue;
      for (const [suit, ranks] of Object.entries(bySuit)) for (const r of ranks ?? []) hl.push(s + suit + r);
    }
    const text = st.commentary.trim();
    let c: ReviewStep['c'] = text;
    if (text === '') c = [para, 0];
    else {
      for (let p = para; p < d.commentary_paragraphs.length; p++) {
        if (d.commentary_paragraphs[p]!.startsWith(text)) {
          para = p;
          c = [p, text.length];
          break;
        }
      }
    }
    if (typeof c === 'string') stats.literalCommentary++;
    const step: ReviewStep = { t, d: st.declarer_tricks, f: st.defense_tricks, c };
    if (h !== prevH) step.h = h;
    if (hl.length) step.hl = hl.join(' ');
    prevH = h;
    out.push(step);
  }
  return out;
}

// ---- write
fs.mkdirSync(path.join(OUT, 'sets'), { recursive: true });
for (const f of fs.readdirSync(path.join(OUT, 'sets'))) fs.rmSync(path.join(OUT, 'sets', f));
const levels: CatalogLevel[] = [];
for (const [key, deals] of sets) {
  fs.writeFileSync(path.join(OUT, 'sets', `L${key}.json`), JSON.stringify(deals));
  const level = deals[0]!.level;
  let lv = levels.find((l) => l.level === level);
  if (!lv) {
    lv = { level, name: index.levels.find((l) => l.level === level)?.level_name ?? `Level ${level}`, sets: [] };
    levels.push(lv);
  }
  lv.sets.push({ key, level, set: deals[0]!.set, deals: deals.map((x) => ({ id: x.id, num: x.num, contract: x.contract })) });
}
const catalog: Catalog = { total: stats.deals, levels };
fs.writeFileSync(path.join(OUT, 'catalog.json'), JSON.stringify(catalog, null, 1));

console.log(stats);
console.log(report.join('\n'));
const calls = new Set<string>();
for (const deals of sets.values()) for (const x of deals) for (const c of x.auction) calls.add(c);
console.log('calls:', [...calls].sort().join(' '));
