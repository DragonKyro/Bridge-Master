// The auction box: W N E S columns from the dealer on, the calls popping in one
// by one, vulnerable seats in red; then the contract and the opening lead.

import type { CSSProperties } from 'react';
import { SEAT_NAME, type Seat } from '@/bridge/cards';
import type { Deal } from '@/data/types';
import { Call, CardText, Contract } from '../shared/text';

const COLS: Seat[] = ['W', 'N', 'E', 'S'];

function vulnerable(deal: Deal, seat: Seat): boolean {
  if (deal.vul === 'Both') return true;
  if (deal.vul === 'NS') return seat === 'N' || seat === 'S';
  if (deal.vul === 'EW') return seat === 'E' || seat === 'W';
  return false;
}

export function AuctionBox({ deal, animate = true }: { deal: Deal; animate?: boolean }) {
  const offset = COLS.indexOf(deal.dealer);
  const cells: Array<string | null> = [...Array<null>(offset).fill(null), ...deal.auction];
  return (
    <div className={`auction${animate ? ' auction-animate' : ''}`}>
      <div className="auction-grid" role="table" aria-label="Auction">
        {COLS.map((s) => (
          <div key={s} className={`auction-head${vulnerable(deal, s) ? ' is-vul' : ''}${s === 'N' || s === 'S' ? ' is-us' : ''}`} role="columnheader">
            {SEAT_NAME[s]}
            {s === deal.dealer && <span className="auction-dealer" title="Dealer">D</span>}
          </div>
        ))}
        {cells.map((c, i) => (
          <div key={i} className="auction-cell" role="cell" style={{ '--k': i - offset } as CSSProperties}>
            {c && <Call call={c} />}
          </div>
        ))}
      </div>
      <div className="auction-summary" style={{ '--k': deal.auction.length } as CSSProperties}>
        <span>
          <Contract contract={deal.contract} /> by South
        </span>
        <span className="muted">
          West leads <CardText card={deal.lead} />
        </span>
      </div>
    </div>
  );
}

export function vulText(deal: Deal): string {
  return deal.vul === 'None' ? 'None vulnerable' : deal.vul === 'Both' ? 'Both vulnerable' : `${deal.vul} vulnerable`;
}
