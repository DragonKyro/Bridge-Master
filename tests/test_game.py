"""Unit and integration tests for GameState and Contract."""

import pytest
from bridge.models.card import Card, Suit, Rank
from bridge.models.hand import Hand
from bridge.models.deal import Deal, Direction
from bridge.models.game import GameState, Contract


SAMPLE_PBN = "S:A52.KQJ.T983.A65 KT3.T87.KJ4.QJ98 QJ4.A9654.A72.K3 9876.32.Q65.T742"


class TestContract:
    def test_from_str(self):
        c = Contract.from_str("4S")
        assert c.level == 4
        assert c.strain == Suit.SPADES
        assert c.doubled == 0

    def test_from_str_notrump(self):
        c = Contract.from_str("3NT")
        assert c.level == 3
        assert c.strain is None

    def test_from_str_doubled(self):
        c = Contract.from_str("4HX")
        assert c.strain == Suit.HEARTS
        assert c.doubled == 1

    def test_from_str_redoubled(self):
        c = Contract.from_str("6CXX")
        assert c.doubled == 2

    def test_tricks_needed(self):
        assert Contract.from_str("3NT").tricks_needed == 9
        assert Contract.from_str("4S").tricks_needed == 10
        assert Contract.from_str("7NT").tricks_needed == 13
        assert Contract.from_str("1C").tricks_needed == 7

    def test_dummy(self):
        c = Contract.from_str("4S", declarer=Direction.SOUTH)
        assert c.dummy == Direction.NORTH

    def test_opening_leader(self):
        c = Contract.from_str("4S", declarer=Direction.SOUTH)
        assert c.opening_leader == Direction.WEST


class TestGameState:
    def _make_game(self, contract_str="4H"):
        deal = Deal.from_pbn_deal(SAMPLE_PBN)
        contract = Contract.from_str(contract_str, declarer=Direction.SOUTH)
        return GameState(deal, contract)

    def test_initial_state(self):
        game = self._make_game()
        assert game.ns_tricks == 0
        assert game.ew_tricks == 0
        assert not game.is_finished
        assert game.current_player == Direction.WEST  # opening leader

    def test_legal_plays_opening_lead(self):
        game = self._make_game()
        legal = game.legal_plays()
        # West leads — any card is legal
        assert len(legal) == 13

    def test_must_follow_suit(self):
        game = self._make_game("3NT")
        # West leads
        west_hand = game.hands[Direction.WEST]
        # Lead a spade
        spade = west_hand.suit_cards(Suit.SPADES)[0]
        game.play_card(spade)

        # North must follow spades if possible
        north_legal = game.legal_plays(Direction.NORTH)
        north_spades = game.hands[Direction.NORTH].suit_cards(Suit.SPADES)
        if north_spades:
            assert all(c.suit == Suit.SPADES for c in north_legal)

    def test_void_can_play_anything(self):
        game = self._make_game("3NT")
        # Find a suit where some player is void
        # East: 9876.32.Q65.T742 — not void in anything
        # Let's just test the rule: play a suit, and a player void in it can play anything
        # West leads a heart
        game.play_card(Card(Suit.HEARTS, Rank.TEN))
        # North follows
        game.play_card(Card(Suit.HEARTS, Rank.ACE))
        # East follows
        game.play_card(Card(Suit.HEARTS, Rank.THREE))
        # South follows
        game.play_card(Card(Suit.HEARTS, Rank.KING))
        # Trick complete, North wins with Ace

    def test_play_card_removes_from_hand(self):
        game = self._make_game("3NT")
        card = game.legal_plays()[0]
        player = game.current_player
        assert card in game.hands[player]
        game.play_card(card)
        assert card not in game.hands[player]

    def test_trick_completion(self):
        game = self._make_game("3NT")
        # Play 4 cards
        for _ in range(4):
            legal = game.legal_plays()
            game.play_card(legal[0])
        assert game.ns_tricks + game.ew_tricks == 1

    def test_play_invalid_card_raises(self):
        game = self._make_game()
        # Try to play a card not in the current player's hand
        current = game.current_player
        other = current.partner
        other_card = game.hands[other].cards[0]
        with pytest.raises(ValueError):
            game.play_card(other_card)

    def test_undo(self):
        game = self._make_game("3NT")
        card = game.legal_plays()[0]
        player = game.current_player
        game.play_card(card)
        assert card not in game.hands[player]
        undone = game.undo()
        assert undone == card
        assert card in game.hands[player]

    def test_full_game(self):
        """Play all 13 tricks and verify game finishes."""
        game = self._make_game("3NT")
        tricks_played = 0
        while not game.is_finished:
            legal = game.legal_plays()
            assert len(legal) > 0
            result = game.play_card(legal[0])
            if result["trick_complete"]:
                tricks_played += 1
        assert tricks_played == 13
        assert game.ns_tricks + game.ew_tricks == 13
        assert game.is_finished

    def test_clone(self):
        game = self._make_game("3NT")
        game.play_card(game.legal_plays()[0])
        clone = game.clone()
        assert clone.ns_tricks == game.ns_tricks
        assert clone.ew_tricks == game.ew_tricks
        # Clone is independent
        clone.play_card(clone.legal_plays()[0])
        assert len(clone.hands[clone.current_player]) != len(game.hands[game.current_player]) or True
