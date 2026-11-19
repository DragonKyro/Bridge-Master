// The solution, as BBO's review plays it: step by step, the four hands with
// the cards the commentary is talking about lit up, the trick in the middle,
// and the commentary growing a phrase at a time. Autoplay, or step with the
// buttons / arrow keys / the scrubber.

import { useEffect, useMemo, useState, type CSSProperties } from 'react';
import { SEATS, type Card, type Seat } from '@/bridge/cards';
import { parsePbn, type Layout } from '@/bridge/deal';
import type { Deal } from '@/data/types';
import { CardImg } from '../cards/CardView';
import { DealDiagram } from '../shared/HandDiagram';
import { Icon } from '../shared/Icon';
import { Contract, SuitText } from '../shared/text';

interface Frame {
  layout: Layout;
  trick: Partial<Record<Seat, Card>>;
  declarer: number;
  defence: number;
  highlight: Set<Card>;
  paragraph: number;
  /** Commentary shown, and how much of it is new at this step. */
  text: string;
  fresh: number;
}

function frames(deal: Deal): Frame[] {
  const out: Frame[] = [];
  let h = deal.review[0]?.h ?? deal.layout;
  let prevText = '';
  for (const st of deal.review) {
    if (st.h) h = st.h;
    const trick: Partial<Record<Seat, Card>> = {};
    for (const t of st.t.split(' ').filter(Boolean)) trick[t[0] as Seat] = t.slice(1);
    const text = typeof st.c === 'string' ? st.c : deal.notes[st.c[0]]!.slice(0, st.c[1]);
    const paragraph = typeof st.c === 'string' ? -1 : st.c[0];
    const fresh = text.startsWith(prevText) ? text.length - prevText.length : text.length;
    out.push({ layout: parsePbn(h), trick, declarer: st.d, defence: st.f, highlight: new Set((st.hl ?? '').split(' ').filter(Boolean).map((x) => x.slice(1))), paragraph, text, fresh });
    prevText = text;
  }
  return out;
}

export function SolutionPlayer({ deal, onClose }: { deal: Deal; onClose: () => void }) {
  const all = useMemo(() => frames(deal), [deal]);
  const [i, setI] = useState(0);
  const [playing, setPlaying] = useState(false);
  const [notes, setNotes] = useState(false);
  const f = all[Math.min(i, all.length - 1)];

  useEffect(() => {
    if (!playing) return;
    if (i >= all.length - 1) {
      setPlaying(false);
      return;
    }
    const nextFresh = all[i + 1]?.fresh ?? 0;
    const t = setTimeout(() => setI((x) => Math.min(all.length - 1, x + 1)), 700 + Math.min(3200, (f?.fresh ?? 0) * 28 + nextFresh * 4));
    return () => clearTimeout(t);
  }, [playing, i, all, f]);

  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if (e.key === 'ArrowRight') setI((x) => Math.min(all.length - 1, x + 1));
      else if (e.key === 'ArrowLeft') setI((x) => Math.max(0, x - 1));
      else if (e.key === ' ') {
        e.preventDefault();
        setPlaying((p) => !p);
      } else if (e.key === 'Escape') onClose();
      else return;
    };
    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  }, [all.length, onClose]);

  if (!f) return null;
  const step = (d: number) => {
    setPlaying(false);
    setI((x) => Math.max(0, Math.min(all.length - 1, x + d)));
  };
  const old = f.text.slice(0, f.text.length - f.fresh);
  const fresh = f.text.slice(f.text.length - f.fresh);

  return (
    <div className="solution-backdrop">
      <div className="solution panel" role="dialog" aria-label="Solution">
        <header className="solution-head">
          <div>
            <h2>Solution</h2>
            <span className="muted">
              Deal {deal.set}-{deal.num} · <Contract contract={deal.contract} /> by South
            </span>
          </div>
          <button type="button" className="icon-btn" onClick={onClose} aria-label="Close the solution">
            <Icon name="close" />
          </button>
        </header>

        <div className="solution-board">
          <DealDiagram
            layout={f.layout}
            highlight={f.highlight}
            center={
              <div className="solution-trick">
                {SEATS.map((s) =>
                  f.trick[s] ? (
                    <span key={`${s}${f.trick[s]}${f.declarer + f.defence}`} className={`solution-trick-card sol-${s} card`}>
                      <CardImg card={f.trick[s]!} />
                    </span>
                  ) : null,
                )}
              </div>
            }
          />
          <span className="solution-score">
            Tricks <b>{f.declarer}</b> · <b className="sol-def">{f.defence}</b>
          </span>
        </div>

        <div className="solution-text">
          {notes ? (
            deal.notes.map((p, k) => (
              <p key={k}>
                <SuitText text={p} />
              </p>
            ))
          ) : (
            <p>
              <span className="sol-old">
                <SuitText text={old} />
              </span>
              <span key={i} className="sol-fresh">
                <SuitText text={fresh} />
              </span>
            </p>
          )}
        </div>

        <div className="solution-controls">
          <input
            type="range"
            min={0}
            max={all.length - 1}
            value={i}
            onChange={(e) => {
              setPlaying(false);
              setI(Number(e.target.value));
            }}
            aria-label="Step"
            style={{ '--p': `${(i / Math.max(1, all.length - 1)) * 100}%` } as CSSProperties}
          />
          <div className="solution-buttons">
            <button type="button" className="icon-btn" onClick={() => step(-all.length)} aria-label="First step">
              <Icon name="first" />
            </button>
            <button type="button" className="icon-btn" onClick={() => step(-1)} aria-label="Previous step">
              <Icon name="prev" />
            </button>
            <button
              type="button"
              className="icon-btn solution-play"
              onClick={() => {
                if (i >= all.length - 1) setI(0);
                setPlaying((p) => !p);
              }}
              aria-label={playing ? 'Pause' : 'Play'}
            >
              <Icon name={playing ? 'pause' : 'play'} />
            </button>
            <button type="button" className="icon-btn" onClick={() => step(1)} aria-label="Next step">
              <Icon name="next" />
            </button>
            <button type="button" className="icon-btn" onClick={() => step(all.length)} aria-label="Last step">
              <Icon name="last" />
            </button>
            <button type="button" className={`chip solution-notes${notes ? ' is-on' : ''}`} onClick={() => setNotes((n) => !n)}>
              All notes
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
