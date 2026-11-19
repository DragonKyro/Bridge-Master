// The bidding and the tricks so far, for looking back while you play: a
// side panel on wide screens, a sheet (tabs: Tricks / Auction) on phones.

import { useEffect, useRef, useState } from 'react';
import { isDeclarerSide, type Seat, type Strain } from '@/bridge/cards';
import { trickWinner, type PlayView, type Trick } from '@/bridge/play';
import type { Deal } from '@/data/types';
import { Icon } from '../shared/Icon';
import { CardText } from '../shared/text';
import { AuctionBox, vulText } from './Auction';

const COLS: Seat[] = ['W', 'N', 'E', 'S'];

export function TrickHistory({ view, strain, hideLead }: { view: PlayView; strain: Strain; hideLead?: boolean }) {
  const rows: Array<{ trick: Trick; n: number; open: boolean }> = view.tricks.map((t, i) => ({ trick: t, n: i + 1, open: false }));
  if (view.current.plays.length > 0 && !(hideLead && view.tricks.length === 0)) rows.push({ trick: view.current, n: view.tricks.length + 1, open: true });
  const end = useRef<HTMLDivElement | null>(null);
  useEffect(() => {
    end.current?.scrollIntoView({ block: 'nearest' });
  }, [rows.length, view.current.plays.length]);

  if (rows.length === 0) return <p className="history-empty muted">No cards played yet.</p>;
  return (
    <div className="tricks-table" role="table" aria-label="Tricks played">
      <div className="tricks-row tricks-head" role="row">
        <span>#</span>
        {COLS.map((s) => (
          <span key={s} className={isDeclarerSide(s) ? 'is-us' : ''}>
            {s}
          </span>
        ))}
        <span>Won</span>
      </div>
      {rows.map(({ trick, n, open }) => {
        const winner = open ? null : (trick.winner ?? trickWinner(trick.plays, strain));
        return (
          <div key={n} className={`tricks-row${winner ? (isDeclarerSide(winner) ? ' won-us' : ' won-them') : ' is-open'}`} role="row">
            <span className="tricks-n">{n}</span>
            {COLS.map((s) => {
              const p = trick.plays.find((x) => x.seat === s);
              return (
                <span key={s} className={`tricks-cell${p && trick.plays[0]!.seat === s ? ' is-lead' : ''}${winner === s ? ' is-winner' : ''}`}>
                  {p ? <CardText card={p.card} /> : <span className="faint">·</span>}
                </span>
              );
            })}
            <span className="tricks-won">{winner ? (isDeclarerSide(winner) ? 'Us' : 'Them') : '…'}</span>
          </div>
        );
      })}
      <div ref={end} />
    </div>
  );
}

export function HistoryPanel({ deal, view, strain, hideLead }: { deal: Deal; view: PlayView; strain: Strain; hideLead: boolean }) {
  return (
    <aside className="history-aside panel" aria-label="Auction and tricks">
      <h3>Auction</h3>
      <p className="muted history-sub">
        {vulText(deal)} · Dealer {({ N: 'North', E: 'East', S: 'South', W: 'West' } as const)[deal.dealer]}
      </p>
      <AuctionBox deal={deal} animate={false} />
      <h3 className="history-h-tricks">
        Tricks{' '}
        <span className="muted">
          {view.ns} – {view.ew}
        </span>
      </h3>
      <TrickHistory view={view} strain={strain} hideLead={hideLead} />
    </aside>
  );
}

export function HistorySheet({
  deal,
  view,
  strain,
  hideLead,
  initialTab,
  onClose,
}: {
  deal: Deal;
  view: PlayView;
  strain: Strain;
  hideLead: boolean;
  initialTab: 'tricks' | 'auction';
  onClose: () => void;
}) {
  const [tab, setTab] = useState(initialTab);
  return (
    <div className="backdrop history-backdrop" onClick={(e) => e.target === e.currentTarget && onClose()}>
      <div className="modal panel history-sheet" role="dialog" aria-label="Auction and tricks">
        <h2>
          <span className="segmented history-tabs">
            <button type="button" aria-pressed={tab === 'tricks'} onClick={() => setTab('tricks')}>
              Tricks {view.ns}–{view.ew}
            </button>
            <button type="button" aria-pressed={tab === 'auction'} onClick={() => setTab('auction')}>
              Auction
            </button>
          </span>
          <button type="button" className="icon-btn modal-close" onClick={onClose} aria-label="Close">
            <Icon name="close" />
          </button>
        </h2>
        {tab === 'tricks' ? (
          <TrickHistory view={view} strain={strain} hideLead={hideLead} />
        ) : (
          <>
            <p className="muted modal-sub">
              {vulText(deal)} · Dealer {({ N: 'North', E: 'East', S: 'South', W: 'West' } as const)[deal.dealer]}
            </p>
            <AuctionBox deal={deal} animate={false} />
          </>
        )}
      </div>
    </div>
  );
}
