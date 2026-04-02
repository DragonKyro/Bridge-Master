"""Unit tests for Trick."""

import pytest
from bridge.models.card import Card, Suit, Rank
from bridge.models.deal import Direction
from bridge.models.trick import Trick


class TestTrick:
    def test_empty_trick(self):
        t = Trick(leader=Direction.WEST, trump=Suit.SPADES)
        assert not t.is_complete
        assert t.led_suit is None
        assert t.current_player == Direction.WEST

    def test_play_order(self):
        t = Trick(leader=Direction.WEST, trump=None)
        t.play(Direction.WEST, Card(Suit.HEARTS, Rank.KING))
        assert t.current_player == Direction.NORTH
        t.play(Direction.NORTH, Card(Suit.HEARTS, Rank.ACE))
        assert t.current_player == Direction.EAST
        t.play(Direction.EAST, Card(Suit.HEARTS, Rank.TWO))
        assert t.current_player == Direction.SOUTH
        t.play(Direction.SOUTH, Card(Suit.HEARTS, Rank.THREE))
        assert t.is_complete

    def test_led_suit(self):
        t = Trick(leader=Direction.SOUTH, trump=None)
        t.play(Direction.SOUTH, Card(Suit.DIAMONDS, Rank.ACE))
        assert t.led_suit == Suit.DIAMONDS

    def test_winner_highest_in_suit(self):
        t = Trick(leader=Direction.SOUTH, trump=None)
        t.play(Direction.SOUTH, Card(Suit.HEARTS, Rank.KING))
        t.play(Direction.WEST, Card(Suit.HEARTS, Rank.ACE))
        t.play(Direction.NORTH, Card(Suit.HEARTS, Rank.QUEEN))
        t.play(Direction.EAST, Card(Suit.HEARTS, Rank.JACK))
        assert t.winner() == Direction.WEST

    def test_winner_trump_wins(self):
        t = Trick(leader=Direction.SOUTH, trump=Suit.SPADES)
        t.play(Direction.SOUTH, Card(Suit.HEARTS, Rank.ACE))
        t.play(Direction.WEST, Card(Suit.SPADES, Rank.TWO))  # trumps
        t.play(Direction.NORTH, Card(Suit.HEARTS, Rank.KING))
        t.play(Direction.EAST, Card(Suit.HEARTS, Rank.QUEEN))
        assert t.winner() == Direction.WEST

    def test_winner_higher_trump_wins(self):
        t = Trick(leader=Direction.SOUTH, trump=Suit.SPADES)
        t.play(Direction.SOUTH, Card(Suit.HEARTS, Rank.ACE))
        t.play(Direction.WEST, Card(Suit.SPADES, Rank.TWO))
        t.play(Direction.NORTH, Card(Suit.SPADES, Rank.FIVE))  # higher trump
        t.play(Direction.EAST, Card(Suit.HEARTS, Rank.KING))
        assert t.winner() == Direction.NORTH

    def test_off_suit_loses(self):
        t = Trick(leader=Direction.SOUTH, trump=None)
        t.play(Direction.SOUTH, Card(Suit.HEARTS, Rank.TWO))
        t.play(Direction.WEST, Card(Suit.DIAMONDS, Rank.ACE))  # off suit
        t.play(Direction.NORTH, Card(Suit.HEARTS, Rank.THREE))
        t.play(Direction.EAST, Card(Suit.HEARTS, Rank.FOUR))
        assert t.winner() == Direction.EAST  # highest in led suit

    def test_wrong_player_raises(self):
        t = Trick(leader=Direction.SOUTH, trump=None)
        with pytest.raises(ValueError):
            t.play(Direction.NORTH, Card(Suit.HEARTS, Rank.ACE))

    def test_play_after_complete_raises(self):
        t = Trick(leader=Direction.SOUTH, trump=None)
        t.play(Direction.SOUTH, Card(Suit.HEARTS, Rank.TWO))
        t.play(Direction.WEST, Card(Suit.HEARTS, Rank.THREE))
        t.play(Direction.NORTH, Card(Suit.HEARTS, Rank.FOUR))
        t.play(Direction.EAST, Card(Suit.HEARTS, Rank.FIVE))
        with pytest.raises(ValueError):
            t.play(Direction.SOUTH, Card(Suit.HEARTS, Rank.SIX))
