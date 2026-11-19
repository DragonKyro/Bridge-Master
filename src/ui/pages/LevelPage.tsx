// A level: its sets, each a grid of deal tiles (number, contract, star).

import type { CSSProperties } from 'react';
import { catalog } from '@/data/load';
import { useProgress } from '@/store/progressStore';
import { back, go, paths } from '../router';
import { Icon } from '../shared/Icon';
import { Star } from '../shared/Stars';
import { Contract } from '../shared/text';
import { countStars } from './Home';

export function LevelPage({ level }: { level: number }) {
  const deals = useProgress((s) => s.deals);
  const lv = catalog.levels.find((l) => l.level === level);
  if (!lv) return null;
  const ids = lv.sets.flatMap((s) => s.deals.map((d) => d.id));
  const c = countStars(deals, ids);
  const nextUp = ids.find((id) => !deals[id]?.b);

  return (
    <div className="level-page">
      <header className="page-head">
        <button type="button" className="icon-btn" onClick={() => back(paths.home)} aria-label="Home">
          <Icon name="back" />
        </button>
        <div className="page-head-title">
          <span className="muted">Level {lv.level}</span>
          <h1>{lv.name}</h1>
        </div>
        <span className="page-head-stats">
          <span className="chip">
            <Star kind={2} /> {c.gold}
          </span>
          <span className="chip">
            <Star kind={1} /> {c.silver}
          </span>
        </span>
      </header>

      {lv.sets.map((set) => {
        const sc = countStars(deals, set.deals.map((d) => d.id));
        return (
          <section key={set.key} className="set">
            <div className="set-head">
              <h2>Set {set.set}</h2>
              <span className="muted">
                {sc.solved} of {sc.total} solved
              </span>
            </div>
            <div className="tiles">
              {set.deals.map((d, i) => {
                const p = deals[d.id];
                const star = p?.b ?? 0;
                return (
                  <button
                    key={d.id}
                    type="button"
                    className={`tile${star ? ` tile-${star === 2 ? 'gold' : 'silver'}` : ''}${!star && p?.t ? ' tile-tried' : ''}${d.id === nextUp ? ' tile-next' : ''}`}
                    style={{ '--i': i } as CSSProperties}
                    onClick={() => go(paths.deal(d.id))}
                    aria-label={`Deal ${set.set}-${d.num}, ${d.contract}${star ? ', solved' : ''}`}
                  >
                    <span className="tile-num">{d.num}</span>
                    <span className="tile-contract">
                      <Contract contract={d.contract} />
                    </span>
                    <Star kind={star} className="tile-star" />
                  </button>
                );
              })}
            </div>
          </section>
        );
      })}
    </div>
  );
}
