// Home: the title, a floating fan, your stars, "continue", and the five levels.

import { useState, type CSSProperties } from 'react';
import { allDeals, catalog } from '@/data/load';
import { useCloud } from '@/net/cloud';
import { useProgress, type ProgressMap } from '@/store/progressStore';
import { CardImg } from '../cards/CardView';
import { go, paths } from '../router';
import { Icon } from '../shared/Icon';
import { SettingsModal } from '../shared/Settings';
import { Star } from '../shared/Stars';

const LEVEL_BLURB: Record<number, string> = {
  1: 'Counting tricks, timing, the first plans',
  2: 'Entries, hold-ups, finesses done right',
  3: 'Safety plays, avoidance, trump control',
  4: 'Endplays, squeezes, coups',
  5: 'The deals that stump the experts',
};

export function countStars(deals: ProgressMap, ids: readonly string[]) {
  let gold = 0;
  let silver = 0;
  for (const id of ids) {
    const b = deals[id]?.b;
    if (b === 2) gold++;
    else if (b === 1) silver++;
  }
  return { gold, silver, solved: gold + silver, total: ids.length };
}

export function Home() {
  const deals = useProgress((s) => s.deals);
  const cloud = useCloud();
  const [settings, setSettings] = useState(false);
  const all = countStars(deals, allDeals.map((d) => d.id));
  const nextUp = allDeals.find((d) => !deals[d.id]?.b);
  const fan = ['SA', 'HK', 'DQ', 'CJ', 'ST'];

  return (
    <div className="home">
      <div className="home-top">
        <span className={`sync-dot${cloud.status === 'signedIn' ? ' is-on' : ''}${cloud.online ? '' : ' is-offline'}`} title={cloud.online ? (cloud.status === 'signedIn' ? 'Synced' : 'Saved on this device') : 'Offline'}>
          <Icon name={cloud.online ? 'cloud' : 'cloudOff'} size="sm" />
          {!cloud.online ? 'Offline' : cloud.status === 'signedIn' ? (cloud.pending ? 'Syncing' : 'Synced') : 'Local'}
        </span>
        <button type="button" className="icon-btn" onClick={() => setSettings(true)} aria-label="Settings and account">
          {cloud.user?.photo ? <img className="home-avatar" src={cloud.user.photo} alt="" referrerPolicy="no-referrer" /> : <Icon name="gear" />}
        </button>
      </div>

      <section className="hero">
        <div className="hero-sky" aria-hidden>
          {['♠', '♥', '♦', '♣', '♠', '♥', '♦', '♣'].map((s, i) => (
            <span key={i} className={`hero-suit suit-${'SHDC'[i % 4]}`} style={{ '--x': `${(i * 13 + 7) % 92}%`, '--y': `${(i * 29 + 11) % 80}%`, '--n': i } as CSSProperties}>
              {s}
            </span>
          ))}
        </div>
        <div className="hero-fan" aria-hidden>
          {fan.map((c, i) => (
            <span key={c} className="hero-fan-card" style={{ '--k': i - 2 } as CSSProperties}>
              <span className="hero-fan-float card">
                <CardImg card={c} layout="full" />
              </span>
            </span>
          ))}
        </div>
        <h1 className="hero-title">Bridge Master</h1>
        <p className="hero-tag">540 declarer-play deals. The defenders see every card — and shift theirs to beat any line but the best.</p>
        <div className="hero-stats">
          <span className="chip">
            <Star kind={2} /> {all.gold}
          </span>
          <span className="chip">
            <Star kind={1} /> {all.silver}
          </span>
          <span className="chip muted">
            {all.solved} / {all.total} solved
          </span>
        </div>
        {nextUp && (
          <button type="button" className="btn btn-lg btn-shine hero-go" onClick={() => go(paths.deal(nextUp.id))}>
            <Icon name="play" size="sm" /> {all.solved === 0 ? 'Start with deal 1' : `Continue · Level ${nextUp.id[0]} deal ${nextUp.id.slice(1)}`}
          </button>
        )}
      </section>

      <section className="levels">
        {catalog.levels.map((lv, k) => {
          const ids = lv.sets.flatMap((s) => s.deals.map((d) => d.id));
          const c = countStars(deals, ids);
          const pct = (n: number) => `${(n / c.total) * 100}%`;
          return (
            <button key={lv.level} type="button" className={`level-card level-${lv.level}`} style={{ '--k': k } as CSSProperties} onClick={() => go(paths.level(lv.level))}>
              <span className="level-badge">{lv.level}</span>
              <span className="level-body">
                <span className="level-name">{lv.name}</span>
                <span className="level-blurb">{LEVEL_BLURB[lv.level]}</span>
                <span className="level-bar" aria-hidden>
                  <span className="level-bar-gold" style={{ width: pct(c.gold) }} />
                  <span className="level-bar-silver" style={{ width: pct(c.silver) }} />
                </span>
              </span>
              <span className="level-count">
                <b>{c.solved}</b>
                <span className="faint">/{c.total}</span>
              </span>
            </button>
          );
        })}
      </section>

      <footer className="home-foot faint">
        Deals, auctions and commentary from Fred Gitelman’s Bridge Master, as published on Bridge Base Online. Double-dummy analysis by Bo Haglund’s DDS.
      </footer>
      {settings && <SettingsModal onClose={() => setSettings(false)} />}
    </div>
  );
}
