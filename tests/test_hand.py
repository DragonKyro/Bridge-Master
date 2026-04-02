"""Unit tests for Hand."""

import pytest
from bridge.models.card import Card, Suit, Rank
from bridge.models.hand import Hand


class TestHand:
    def test_empty(self):
        h = Hand()
        assert len(h) == 0

    def test_add_remove(self):
        h = Hand()
        c = Card(Suit.SPADES, Rank.ACE)
        h.add(c)
        assert len(h) == 1
        assert c in h
        h.remove(c)
        assert len(h) == 0
        assert c not in h

    def test_from_pbn(self):
        h = Hand.from_pbn("AKQ.JT9.876.5432")
        assert len(h) == 13
        assert Card(Suit.SPADES, Rank.ACE) in h
        assert Card(Suit.HEARTS, Rank.JACK) in h
        assert Card(Suit.DIAMONDS, Rank.EIGHT) in h
        assert Card(Suit.CLUBS, Rank.FIVE) in h

    def test_from_pbn_void(self):
        h = Hand.from_pbn("AKQJT98765432.-.-.--")
        assert len(h) == 13
        assert h.void_in(Suit.HEARTS)
        assert h.void_in(Suit.DIAMONDS)

    def test_pbn_roundtrip(self):
        original = "AKQ.JT9.876.5432"
        h = Hand.from_pbn(original)
        assert h.pbn_string() == "AKQ.JT9.876.5432"

    def test_suit_cards(self):
        h = Hand.from_pbn("AKQ.JT9.876.5432")
        spades = h.suit_cards(Suit.SPADES)
        assert len(spades) == 3
        assert spades[0].rank == Rank.ACE  # sorted high to low

    def test_suit_length(self):
        h = Hand.from_pbn("AKQ.JT9.876.5432")
        assert h.suit_length(Suit.SPADES) == 3
        assert h.suit_length(Suit.CLUBS) == 4

    def test_hcp(self):
        h = Hand.from_pbn("AKQ.JT9.876.5432")
        # A=4, K=3, Q=2, J=1 = 10
        assert h.hcp == 10

    def test_from_pbn_invalid(self):
        with pytest.raises(ValueError):
            Hand.from_pbn("AKQ.JT9")  # only 2 suits
