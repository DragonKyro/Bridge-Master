// The table: top bar (deal, contract, trick meter), dummy across the top of
// the felt, the trick and the defenders in the middle, your hand at the
// bottom, and the actions under it. The auction is up until you start.

import { useEffect, useMemo, useState, type CSSProperties } from 'react';
import { isDeclarerSide, type Card } from '@/bridge/cards';
import { legalPlays } from '@/bridge/play';
import { levelName, loadDeal, nextDealId } from '@/data/load';
import type { Deal } from '@/data/types';
import { warmUpSolver } from '@/dd/client';
import { handView } from '@/game/hand';
import { usePlay } from '@/store/playStore';
import { useProgress } from '@/store/progressStore';
import { usePrefs } from '@/store/prefsStore';
import { back, go, paths } from '../router';
import { Icon } from '../shared/Icon';
import { SettingsModal } from '../shared/Settings';
import { Star } from '../shared/Stars';
import { Contract } from '../shared/text';
import { SolutionPlayer } from '../solution/SolutionPlayer';
import { AuctionBox, vulText } from './Auction';
import { HandFan } from './HandFan';
import { ResultSheet } from './Result';
import { DefenderSeat, Trick } from './Trick';

export function TablePage({ id, solution }: { id: string; solution: boolean }) {
  const [deal, setDeal] = useState<Deal | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    warmUpSolver();
  }, []);

  useEffect(() => {
    let live = true;
    setError(null);
    loadDeal(id)
      .then((d) => {
        if (!live) return;
        usePlay.getState().open(d);
        setDeal(d);
      })
      .catch((e: Error) => live && setError(e.message));
    return () => {
      live = false;
    };
  }, [id]);

  if (error) {
    return (
      <div className="page-center">
        <p>Couldn’t open deal {id}: {error}</p>
        <button type="button" className="btn" onClick={() => go(paths.home)}>
          Home
        </button>
      </div>
    );
  }
  if (!deal) return <div className="page-center muted">Shuffling…</div>;
  return <Table deal={deal} solution={solution} />;
}

function Table({ deal, solution }: { deal: Deal; solution: boolean }) {
  const { hand, phase, busy, outcome, history, error } = usePlay();
  const fourColor = usePrefs((s) => s.fourColor);
  const star = useProgress((s) => s.deals[deal.id]?.b ?? 0);
  const [showAuction, setShowAuction] = useState(false);
  const [showSettings, setShowSettings] = useState(false);
  const [resultClosed, setResultClosed] = useState(false);

  useEffect(() => setResultClosed(false), [outcome]);
  useEffect(() => {
    if (solution) usePlay.getState().notePeek();
  }, [solution]);

  const view = useMemo(() => (hand ? handView(hand) : null), [hand]);
  if (!hand || !view || hand.dealId !== deal.id) return <div className="page-center muted">Shuffling…</div>;

  const turn = view.turn;
  const humanTurn = phase === 'play' && !busy && turn !== null && isDeclarerSide(turn);
  const legal = new Set<Card>(humanTurn ? legalPlays(view) : []);
  const play = (c: Card) => usePlay.getState().play(c);
  const next = nextDealId(deal.id);
  const setLabel = `${deal.set}-${deal.num}`;
  const turnLabel = phase !== 'play' || turn === null ? null : turn === 'S' ? 'Your turn' : turn === 'N' ? 'Play from dummy' : null;

  return (
    <div className={`table-page${fourColor ? '' : ' suits-two'}`}>
      <header className="topbar">
        <button type="button" className="icon-btn" onClick={() => back(paths.level(deal.level))} aria-label="Back to the level">
          <Icon name="back" />
        </button>
        <div className="topbar-title">
          <span className="topbar-level">
            Level {deal.level} · {levelName(deal.level)}
          </span>
          <span className="topbar-deal">
            Deal {setLabel} {star ? <Star kind={star} /> : null}
          </span>
        </div>
        <button type="button" className="contract-chip" onClick={() => setShowAuction(true)} aria-label="Show the auction">
          <Contract contract={deal.contract} />
          <span className="contract-chip-need">need {deal.need}</span>
        </button>
        <TrickMeter won={view.ns} lost={view.ew} need={deal.need} />
      </header>

      <main className="felt">
        <div className="felt-texture" aria-hidden />
        <section className={`seat-zone seat-zone-N${turn === 'N' && phase === 'play' ? ' is-turn' : ''}`}>
          <span className="seat-tag">
            North · dummy{turnLabel && turn === 'N' && <em>{turnLabel}</em>}
          </span>
          <HandFan seat="N" dealKey={deal.id} cards={view.remaining.N} strain={hand.strain} active={humanTurn && turn === 'N'} legal={legal} onPlay={play} />
        </section>

        <section className="middle">
          <DefenderSeat seat="W" count={view.remaining.W.length + (phase === 'auction' ? 1 : 0)} active={phase === 'play' && turn === 'W'} thinking={busy} />
          <Trick view={view} strain={hand.strain} hideLead={phase === 'auction'} over={phase === 'done'} turn={phase === 'play' ? turn : null} thinking={busy} />
          <DefenderSeat seat="E" count={view.remaining.E.length} active={phase === 'play' && turn === 'E'} thinking={busy} />
          {phase === 'auction' && (
            <div className="auction-overlay">
              <div className="auction-card panel">
                <div className="auction-card-head">
                  <span className="muted">{vulText(deal)}</span>
                  <span className="muted">Dealer {({ N: 'North', E: 'East', S: 'South', W: 'West' } as const)[deal.dealer]}</span>
                </div>
                <AuctionBox deal={deal} />
                <button type="button" className="btn btn-lg btn-shine auction-go" style={{ '--k': deal.auction.length + 1 } as CSSProperties} onClick={() => usePlay.getState().begin()}>
                  <Icon name="play" size="sm" /> Play the hand
                </button>
              </div>
            </div>
          )}
        </section>

        <section className={`seat-zone seat-zone-S${turn === 'S' && phase === 'play' ? ' is-turn' : ''}`}>
          <HandFan seat="S" dealKey={deal.id} cards={view.remaining.S} strain={hand.strain} active={humanTurn && turn === 'S'} legal={legal} onPlay={play} />
          <span className="seat-tag">
            South · you{turnLabel && turn === 'S' && <em>{turnLabel}</em>}
          </span>
        </section>
      </main>

      <nav className="actionbar">
        <button type="button" className="action" disabled={history.length === 0 || phase === 'auction'} onClick={() => usePlay.getState().undo()}>
          <Icon name="undo" />
          <span>Undo</span>
        </button>
        <button type="button" className="action" disabled={phase === 'auction'} onClick={() => usePlay.getState().restart()}>
          <Icon name="restart" />
          <span>Restart</span>
        </button>
        <button type="button" className="action" onClick={() => setShowAuction(true)}>
          <Icon name="auction" />
          <span>Auction</span>
        </button>
        <button type="button" className="action" onClick={() => go(paths.solution(deal.id))}>
          <Icon name="book" />
          <span>Solution</span>
        </button>
        <button type="button" className="action" onClick={() => setShowSettings(true)}>
          <Icon name="gear" />
          <span>Settings</span>
        </button>
      </nav>

      {error && <div className="toast">Solver error: {error}</div>}

      {showAuction && (
        <div className="backdrop" onClick={(e) => e.target === e.currentTarget && setShowAuction(false)}>
          <div className="modal panel" role="dialog" aria-label="Auction">
            <h2>
              Auction
              <button type="button" className="icon-btn modal-close" onClick={() => setShowAuction(false)} aria-label="Close">
                <Icon name="close" />
              </button>
            </h2>
            <p className="muted modal-sub">
              {vulText(deal)} · Dealer {({ N: 'North', E: 'East', S: 'South', W: 'West' } as const)[deal.dealer]}
            </p>
            <AuctionBox deal={deal} animate={false} />
          </div>
        </div>
      )}
      {showSettings && <SettingsModal onClose={() => setShowSettings(false)} />}

      {phase === 'done' && outcome && !resultClosed && !solution && (
        <ResultSheet
          deal={deal}
          hand={hand}
          outcome={outcome}
          hasNext={!!next}
          onRetry={() => usePlay.getState().restart()}
          onSolution={() => go(paths.solution(deal.id))}
          onNext={() => next && go(paths.deal(next), true)}
          onClose={() => setResultClosed(true)}
        />
      )}
      {phase === 'done' && outcome && resultClosed && (
        <button type="button" className="result-reopen btn" onClick={() => setResultClosed(false)}>
          Result
        </button>
      )}

      {solution && <SolutionPlayer deal={deal} onClose={() => back(paths.deal(deal.id))} />}
    </div>
  );
}

/** Thirteen slots: tricks won fill from the left, lost from the right; the slots the contract needs are tinted gold. */
function TrickMeter({ won, lost, need }: { won: number; lost: number; need: number }) {
  return (
    <div className="meter" role="img" aria-label={`${won} tricks won, ${lost} lost, ${need} needed`}>
      <div className="meter-slots">
        {Array.from({ length: 13 }, (_, i) => {
          const cls = i < won ? 'is-won' : i >= 13 - lost ? 'is-lost' : '';
          return <span key={i} className={`meter-slot ${cls}${i < need ? ' is-goal' : ''}`} />;
        })}
      </div>
      <div className="meter-nums">
        <span className="meter-won">{won}</span>
        <span className="faint">/</span>
        <span className="meter-lost">{lost}</span>
      </div>
    </div>
  );
}
