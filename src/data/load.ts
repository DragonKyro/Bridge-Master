// The deals: the catalog is bundled; each set's file (≈30–45 KB gzipped) is
// fetched the first time one of its deals is opened.

import catalogJson from './catalog.json';
import type { Catalog, CatalogDeal, CatalogSet, Deal } from './types';

export const catalog = catalogJson as Catalog;

const loaders = import.meta.glob<Deal[]>('./sets/*.json', { import: 'default' });
const cache = new Map<string, Promise<Deal[]>>();

/** "1A-7" → "1A". */
export const setKeyOf = (id: string) => id.split('-')[0]!;

export function loadSet(key: string): Promise<Deal[]> {
  let p = cache.get(key);
  if (!p) {
    const loader = loaders[`./sets/L${key}.json`];
    if (!loader) return Promise.reject(new Error(`no set ${key}`));
    p = loader();
    p.catch(() => cache.delete(key));
    cache.set(key, p);
  }
  return p;
}

export async function loadDeal(id: string): Promise<Deal> {
  const deal = (await loadSet(setKeyOf(id))).find((d) => d.id === id);
  if (!deal) throw new Error(`no deal ${id}`);
  return deal;
}

export function findSet(key: string): CatalogSet | undefined {
  for (const l of catalog.levels) for (const s of l.sets) if (s.key === key) return s;
  return undefined;
}

/** Every deal in catalog order. */
export const allDeals: CatalogDeal[] = catalog.levels.flatMap((l) => l.sets.flatMap((s) => s.deals));

/** The deal after `id` (crossing into the next set / level), or null at the very end. */
export function nextDealId(id: string): string | null {
  const i = allDeals.findIndex((d) => d.id === id);
  return i >= 0 && i + 1 < allDeals.length ? allDeals[i + 1]!.id : null;
}

export const levelName = (level: number) => catalog.levels.find((l) => l.level === level)?.name ?? `Level ${level}`;
