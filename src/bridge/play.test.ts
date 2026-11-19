import { describe, expect, it } from 'vitest';
import { layoutToPbn, parsePbn } from './deal';
import { IllegalPlay, equivalent, legalFrom, playsFromCards, replay, trickWinner } from './play';

const A1 = 'S:J32.A32.K32.AQ32 KT987.9876.QJT.T Q4.K54.A654.KJ54 A65.QJT.987.9876';

describe('deal', () => {
  it('parses PBN from any seat and writes it back from North', () => {
    const l = parsePbn(A1);
    expect(l.S).toEqual(['SJ', 'S3', 'S2', 'HA', 'H3', 'H2', 'DK', 'D3', 'D2', 'CA', 'CQ', 'C3', 'C2']);
    expect(layoutToPbn(l, 'N')).toBe('N:Q4.K54.A654.KJ54 A65.QJT.987.9876 J32.A32.K32.AQ32 KT987.9876.QJT.T');
    expect(parsePbn(layoutToPbn(l, 'N'))).toEqual(l);
  });
});

describe('tricks', () => {
  it('highest of the led suit wins in notrump; a trump beats it in a suit contract', () => {
    const plays = [
      { seat: 'W' as const, card: 'S5' },
      { seat: 'N' as const, card: 'SK' },
      { seat: 'E' as const, card: 'H2' },
      { seat: 'S' as const, card: 'SA' },
    ];
    expect(trickWinner(plays, 'N')).toBe('S');
    expect(trickWinner(plays, 'H')).toBe('E');
    expect(trickWinner(plays, 'D')).toBe('S');
  });

  it('must follow suit when able', () => {
    expect(legalFrom(['SA', 'H2', 'H3'], 'H')).toEqual(['H2', 'H3']);
    expect(legalFrom(['SA', 'D2'], 'H')).toEqual(['SA', 'D2']);
    expect(legalFrom(['SA', 'D2'], null)).toEqual(['SA', 'D2']);
  });

  it('replays the play and refuses revokes and cards out of turn', () => {
    const l = parsePbn(A1);
    const v = replay(l, 'N', [
      { seat: 'W', card: 'ST' },
      { seat: 'N', card: 'S4' },
      { seat: 'E', card: 'SA' },
      { seat: 'S', card: 'S2' },
    ]);
    expect(v.ew).toBe(1);
    expect(v.turn).toBe('E');
    expect(() => replay(l, 'N', [{ seat: 'N', card: 'S4' }])).toThrow(IllegalPlay);
    expect(() => replay(l, 'N', [{ seat: 'W', card: 'ST' }, { seat: 'N', card: 'HK' }])).toThrow(IllegalPlay);
  });

  it('works out the seats of a list of cards', () => {
    const plays = playsFromCards(parsePbn(A1), 'N', ['ST', 'S4', 'SA', 'S2', 'S6']);
    expect(plays.map((p) => p.seat).join('')).toBe('WNESE');
  });

  it('treats touching cards in one hand as equivalent', () => {
    const v = replay(parsePbn(A1), 'N', [{ seat: 'W', card: 'ST' }]);
    // South's ♠3 and ♠2: nothing between them outside South.
    expect(equivalent(v, 'S', 'S3', 'S2')).toBe(true);
    // South's ♠J and ♠3: East's ♠6 and ♠5 lie between.
    expect(equivalent(v, 'S', 'SJ', 'S3')).toBe(false);
  });
});
