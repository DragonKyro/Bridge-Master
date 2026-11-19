// The end of an attempt: made or beaten, the star, the defenders' cards
// revealed, and where to go next.

import { useMemo, type CSSProperties } from 'react';
import type { Deal } from '@/data/types';
import type { HandState } from '@/game/hand';
import type { Outcome } from '@/store/playStore';
import { DealDiagram } from '../shared/HandDiagram';
import { Icon } from '../shared/Icon';
import { Star } from '../shared/Stars';
import { Contract } from '../shared/text';

export function ResultSheet({
  deal,
  hand,
  outcome,
  hasNext,
  onRetry,
  onSolution,
  onNext,
  onClose,
}: {
  deal: Deal;
  hand: HandState;
  outcome: Outcome;
  hasNext: boolean;
  onRetry: () => void;
  onSolution: () => void;
  onNext: () => void;
  onClose: () => void;
}) {
  const earned = outcome.made ? (outcome.clean ? 2 : 1) : 0;
  const best = outcome.progress.b ?? 0;
  const burst = useMemo(() => Array.from({ length: 14 }, (_, i) => ({ a: (i / 14) * 360 + (i % 2) * 9, d: 60 + (i % 3) * 18 })), []);
  return (
    <div className="result-backdrop">
      <div className={`result panel ${outcome.made ? 'result-made' : 'result-down'}`} role="dialog" aria-label="Result">
        <button type="button" className="icon-btn result-close" onClick={onClose} aria-label="Hide the result and look at the table">
          <Icon name="close" />
        </button>
        <div className="result-head">
          <div className="result-star-wrap">
            {outcome.made &&
              burst.map((b, i) => <span key={i} className="result-spark" style={{ '--a': `${b.a}deg`, '--d': `${b.d}px`, '--i': i } as CSSProperties} />)}
            <Star kind={earned as 0 | 1 | 2} className="result-star" />
          </div>
          <div>
            <h2 className="result-title">{outcome.made ? 'Contract made!' : 'Contract defeated'}</h2>
            <p className="result-sub">
              <Contract contract={deal.contract} /> ·{' '}
              {outcome.made ? `${deal.need} tricks secured` : `the defence took ${14 - deal.need} tricks`}
            </p>
          </div>
        </div>
        <p className="result-note">
          {outcome.made
            ? earned === 2
              ? 'A clean solve — gold star.'
              : best === 2
                ? 'Solved again — your gold star stands.'
                : 'Solved with help (undo or the solution) — silver star. Solve it cleanly for gold.'
            : outcome.switched
              ? 'The defenders shifted their cards to beat that line — only the best line survives every layout. The solution shows it.'
              : 'Every line but the best one comes up short against these defenders. Try again, or study the solution.'}
        </p>
        <div className="result-deal">
          <DealDiagram layout={hand.layout} center={<span className="result-center">Their cards</span>} />
        </div>
        <div className="result-actions">
          <button type="button" className="btn btn-ghost" onClick={onRetry}>
            <Icon name="restart" size="sm" /> Try again
          </button>
          <button type="button" className="btn btn-ghost" onClick={onSolution}>
            <Icon name="book" size="sm" /> Solution
          </button>
          {hasNext && (
            <button type="button" className={`btn${outcome.made ? ' btn-shine' : ''}`} onClick={onNext}>
              Next deal <Icon name="arrow" size="sm" />
            </button>
          )}
        </div>
      </div>
    </div>
  );
}
