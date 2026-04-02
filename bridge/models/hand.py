"""A Hand represents the 13 cards held by one player."""

from __future__ import annotations
from .card import Card, Suit, Rank


class Hand:
    """One player's hand of cards."""

    def __init__(self, cards: list[Card] | None = None):
        self._cards: set[Card] = set(cards) if cards else set()

    # --- Card management ---

    def add(self, card: Card) -> None:
        self._cards.add(card)

    def remove(self, card: Card) -> None:
        self._cards.discard(card)

    def has(self, card: Card) -> bool:
        return card in self._cards

    @property
    def cards(self) -> list[Card]:
        """All cards sorted by suit (spades first) then rank (high first)."""
        return sorted(self._cards, key=lambda c: (-c.suit, -c.rank))

    def __len__(self) -> int:
        return len(self._cards)

    def __contains__(self, card: Card) -> bool:
        return card in self._cards

    def __iter__(self):
        return iter(self.cards)

    # --- Suit queries ---

    def suit_cards(self, suit: Suit) -> list[Card]:
        """Cards in a given suit, sorted high to low."""
        return sorted(
            [c for c in self._cards if c.suit == suit],
            key=lambda c: -c.rank,
        )

    def suit_length(self, suit: Suit) -> int:
        return sum(1 for c in self._cards if c.suit == suit)

    def void_in(self, suit: Suit) -> bool:
        return self.suit_length(suit) == 0

    # --- Points ---

    @property
    def hcp(self) -> int:
        return sum(c.hcp for c in self._cards)

    # --- Display ---

    def pbn_string(self) -> str:
        """PBN-style string: 'S.H.D.C' with ranks high-to-low per suit.
        Uses 'T' for ten (PBN standard), not '10'."""
        parts = []
        for suit in reversed(list(Suit)):  # spades, hearts, diamonds, clubs
            ranks = self.suit_cards(suit)
            parts.append("".join(
                "T" if c.rank == Rank.TEN else c.rank.symbol
                for c in ranks
            ))
        return ".".join(parts)

    def display(self) -> str:
        """Human-readable multi-line display."""
        lines = []
        for suit in reversed(list(Suit)):  # spades first
            ranks = self.suit_cards(suit)
            rank_str = " ".join(c.rank.symbol for c in ranks) if ranks else "--"
            lines.append(f"{suit.symbol} {rank_str}")
        return "\n".join(lines)

    def __repr__(self) -> str:
        return f"Hand({self.pbn_string()})"

    # --- Factory ---

    @classmethod
    def from_pbn(cls, pbn: str) -> "Hand":
        """Parse from PBN suit string like 'AKQ.JT9.876.5432'
        Order is Spades.Hearts.Diamonds.Clubs."""
        suits_order = [Suit.SPADES, Suit.HEARTS, Suit.DIAMONDS, Suit.CLUBS]
        parts = pbn.strip().split(".")
        if len(parts) != 4:
            raise ValueError(f"PBN hand must have 4 suit groups, got: {pbn!r}")
        cards = []
        for suit, ranks_str in zip(suits_order, parts):
            for ch in ranks_str:
                if ch == "-" or ch == "":
                    continue
                cards.append(Card(suit, Rank.from_char(ch)))
        return cls(cards)
