"""Unit tests for Deal and Direction."""

import pytest
from bridge.models.card import Card, Suit, Rank
from bridge.models.hand import Hand
from bridge.models.deal import Deal, Direction


class TestDirection:
    def test_partner(self):
        assert Direction.NORTH.partner == Direction.SOUTH
        assert Direction.EAST.partner == Direction.WEST

    def test_lho(self):
        assert Direction.SOUTH.lho == Direction.WEST
        assert Direction.WEST.lho == Direction.NORTH

    def test_rho(self):
        assert Direction.SOUTH.rho == Direction.EAST

    def test_is_ns(self):
        assert Direction.NORTH.is_ns
        assert Direction.SOUTH.is_ns
        assert not Direction.EAST.is_ns
        assert not Direction.WEST.is_ns

    def test_from_char(self):
        assert Direction.from_char("N") == Direction.NORTH
        assert Direction.from_char("s") == Direction.SOUTH


class TestDeal:
    SAMPLE_PBN = "S:A52.KQJ.T983.A65 KT3.T87.KJ4.QJ98 QJ4.A9654.A72.K3 9876.32.Q65.T742"

    def test_from_pbn_deal(self):
        deal = Deal.from_pbn_deal(self.SAMPLE_PBN)
        assert deal.is_complete()
        assert len(deal.validate()) == 0

    def test_hand_access(self):
        deal = Deal.from_pbn_deal(self.SAMPLE_PBN)
        south = deal.hand(Direction.SOUTH)
        assert len(south) == 13
        assert Card(Suit.SPADES, Rank.ACE) in south

    def test_all_52_cards(self):
        deal = Deal.from_pbn_deal(self.SAMPLE_PBN)
        all_cards = set()
        for d in Direction:
            for c in deal.hands[d]:
                all_cards.add(c)
        assert len(all_cards) == 52

    def test_validate_incomplete(self):
        deal = Deal()  # empty deal
        issues = deal.validate()
        assert len(issues) > 0

    def test_pbn_with_dealer_prefix(self):
        deal = Deal.from_pbn_deal("N:AKQ.JT9.876.5432 T987.876.KJ4.QJ9 J654.AQ54.AT9.AK 32.K32.Q532.T876")
        assert deal.is_complete()


class TestDealDisplay:
    def test_display_not_empty(self):
        deal = Deal.from_pbn_deal(TestDeal.SAMPLE_PBN)
        text = deal.display()
        assert "South" not in text or len(text) > 50  # just check it produces output
        assert len(text) > 0
