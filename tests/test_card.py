"""Unit tests for Card, Suit, Rank."""

import pytest
from bridge.models.card import Card, Suit, Rank, full_deck


class TestRank:
    def test_values(self):
        assert Rank.TWO == 2
        assert Rank.ACE == 14

    def test_symbol(self):
        assert Rank.ACE.symbol == "A"
        assert Rank.TEN.symbol == "10"
        assert Rank.FIVE.symbol == "5"

    def test_from_char(self):
        assert Rank.from_char("A") == Rank.ACE
        assert Rank.from_char("T") == Rank.TEN
        assert Rank.from_char("10") == Rank.TEN
        assert Rank.from_char("2") == Rank.TWO


class TestSuit:
    def test_ordering(self):
        assert Suit.CLUBS < Suit.DIAMONDS < Suit.HEARTS < Suit.SPADES

    def test_letter(self):
        assert Suit.SPADES.letter == "S"
        assert Suit.CLUBS.letter == "C"

    def test_from_char(self):
        assert Suit.from_char("S") == Suit.SPADES
        assert Suit.from_char("h") == Suit.HEARTS


class TestCard:
    def test_creation(self):
        c = Card(Suit.SPADES, Rank.ACE)
        assert c.suit == Suit.SPADES
        assert c.rank == Rank.ACE

    def test_from_str(self):
        assert Card.from_str("AS") == Card(Suit.SPADES, Rank.ACE)
        assert Card.from_str("10H") == Card(Suit.HEARTS, Rank.TEN)
        assert Card.from_str("TH") == Card(Suit.HEARTS, Rank.TEN)
        assert Card.from_str("2c") == Card(Suit.CLUBS, Rank.TWO)

    def test_from_str_invalid(self):
        with pytest.raises((ValueError, KeyError)):
            Card.from_str("XY")

    def test_hcp(self):
        assert Card(Suit.SPADES, Rank.ACE).hcp == 4
        assert Card(Suit.HEARTS, Rank.KING).hcp == 3
        assert Card(Suit.DIAMONDS, Rank.QUEEN).hcp == 2
        assert Card(Suit.CLUBS, Rank.JACK).hcp == 1
        assert Card(Suit.SPADES, Rank.TEN).hcp == 0
        assert Card(Suit.HEARTS, Rank.TWO).hcp == 0

    def test_equality(self):
        a = Card(Suit.SPADES, Rank.ACE)
        b = Card(Suit.SPADES, Rank.ACE)
        assert a == b
        assert a != Card(Suit.HEARTS, Rank.ACE)

    def test_hash(self):
        a = Card(Suit.SPADES, Rank.ACE)
        b = Card(Suit.SPADES, Rank.ACE)
        assert hash(a) == hash(b)
        assert len({a, b}) == 1

    def test_ordering(self):
        low = Card(Suit.CLUBS, Rank.TWO)
        high = Card(Suit.SPADES, Rank.ACE)
        assert low < high

    def test_short(self):
        assert Card(Suit.SPADES, Rank.ACE).short == "AS"
        assert Card(Suit.HEARTS, Rank.TEN).short == "10H"

    def test_image_key(self):
        assert Card(Suit.SPADES, Rank.ACE).image_key == "as"
        assert Card(Suit.HEARTS, Rank.TEN).image_key == "10h"


class TestFullDeck:
    def test_length(self):
        assert len(full_deck()) == 52

    def test_unique(self):
        deck = full_deck()
        assert len(set(deck)) == 52

    def test_suits(self):
        deck = full_deck()
        for suit in Suit:
            count = sum(1 for c in deck if c.suit == suit)
            assert count == 13
