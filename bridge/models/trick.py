"""Trick: tracks the four cards played in a single trick."""

from __future__ import annotations
from .card import Card, Suit
from .deal import Direction


class Trick:
    """A single trick in progress or completed.

    Attributes:
        leader: direction that led to this trick
        trump: trump suit (None for notrump)
        plays: list of (direction, card) tuples in play order
    """

    def __init__(self, leader: Direction, trump: Suit | None = None):
        self.leader = leader
        self.trump = trump
        self.plays: list[tuple[Direction, Card]] = []

    @property
    def led_suit(self) -> Suit | None:
        """The suit that was led (None if no cards played yet)."""
        if self.plays:
            return self.plays[0][1].suit
        return None

    @property
    def is_complete(self) -> bool:
        return len(self.plays) == 4

    @property
    def current_player(self) -> Direction:
        """Who plays next."""
        return Direction((self.leader.value + len(self.plays)) % 4)

    def play(self, direction: Direction, card: Card) -> None:
        if self.is_complete:
            raise ValueError("Trick is already complete")
        if direction != self.current_player:
            raise ValueError(f"Expected {self.current_player} to play, not {direction}")
        self.plays.append((direction, card))

    def winner(self) -> Direction:
        """Determine who won the trick. Only valid when complete."""
        if not self.plays:
            raise ValueError("No cards played")

        led_suit = self.plays[0][1].suit
        best_dir, best_card = self.plays[0]

        for direction, card in self.plays[1:]:
            if card.suit == best_card.suit and card.rank > best_card.rank:
                # Same suit, higher rank
                best_dir, best_card = direction, card
            elif self.trump is not None and card.suit == self.trump and best_card.suit != self.trump:
                # Trumped
                best_dir, best_card = direction, card

        return best_dir

    def __repr__(self) -> str:
        plays_str = " ".join(f"{d.letter}:{c}" for d, c in self.plays)
        return f"Trick({plays_str})"
