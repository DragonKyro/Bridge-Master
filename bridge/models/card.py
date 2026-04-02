"""Card, Suit, and Rank definitions for bridge."""

from enum import IntEnum
from functools import total_ordering


class Suit(IntEnum):
    """Bridge suits ordered by rank (clubs lowest, spades highest)."""
    CLUBS = 0
    DIAMONDS = 1
    HEARTS = 2
    SPADES = 3

    @property
    def symbol(self) -> str:
        return {0: "\u2663", 1: "\u2666", 2: "\u2665", 3: "\u2660"}[self.value]

    @property
    def letter(self) -> str:
        return {0: "C", 1: "D", 2: "H", 3: "S"}[self.value]

    def __str__(self) -> str:
        return self.symbol

    @classmethod
    def from_char(cls, c: str) -> "Suit":
        mapping = {"C": cls.CLUBS, "D": cls.DIAMONDS, "H": cls.HEARTS, "S": cls.SPADES}
        return mapping[c.upper()]


class Rank(IntEnum):
    """Card ranks. 2=2, ..., 10=10, J=11, Q=12, K=13, A=14."""
    TWO = 2
    THREE = 3
    FOUR = 4
    FIVE = 5
    SIX = 6
    SEVEN = 7
    EIGHT = 8
    NINE = 9
    TEN = 10
    JACK = 11
    QUEEN = 12
    KING = 13
    ACE = 14

    @property
    def symbol(self) -> str:
        if self.value <= 10:
            return str(self.value)
        return {11: "J", 12: "Q", 13: "K", 14: "A"}[self.value]

    def __str__(self) -> str:
        return self.symbol

    @classmethod
    def from_char(cls, c: str) -> "Rank":
        mapping = {
            "2": cls.TWO, "3": cls.THREE, "4": cls.FOUR, "5": cls.FIVE,
            "6": cls.SIX, "7": cls.SEVEN, "8": cls.EIGHT, "9": cls.NINE,
            "T": cls.TEN, "10": cls.TEN,
            "J": cls.JACK, "Q": cls.QUEEN, "K": cls.KING, "A": cls.ACE,
        }
        return mapping[c.upper()]


@total_ordering
class Card:
    """A single playing card with a suit and rank."""

    __slots__ = ("suit", "rank")

    def __init__(self, suit: Suit, rank: Rank):
        self.suit = suit
        self.rank = rank

    # --- Display ---

    @property
    def short(self) -> str:
        """Short notation like 'AS' for Ace of Spades."""
        return f"{self.rank.symbol}{self.suit.letter}"

    @property
    def image_key(self) -> str:
        """Key matching the card image filenames (e.g. 'as', '10h')."""
        return f"{self.rank.symbol.lower()}{self.suit.letter.lower()}"

    def __repr__(self) -> str:
        return f"Card({self.rank.symbol}{self.suit.symbol})"

    def __str__(self) -> str:
        return f"{self.rank.symbol}{self.suit.symbol}"

    # --- Comparison (by rank only; suit is contextual) ---

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Card):
            return NotImplemented
        return self.suit == other.suit and self.rank == other.rank

    def __lt__(self, other: object) -> bool:
        if not isinstance(other, Card):
            return NotImplemented
        return (self.suit, self.rank) < (other.suit, other.rank)

    def __hash__(self) -> int:
        return hash((self.suit, self.rank))

    # --- Factory ---

    @classmethod
    def from_str(cls, s: str) -> "Card":
        """Parse a card from a string like 'AS', 'TH', '10C'."""
        s = s.strip().upper()
        if len(s) == 3 and s[:2] == "10":
            rank = Rank.TEN
            suit = Suit.from_char(s[2])
        elif len(s) == 2:
            rank = Rank.from_char(s[0])
            suit = Suit.from_char(s[1])
        else:
            raise ValueError(f"Cannot parse card: {s!r}")
        return cls(suit, rank)

    # --- HCP ---

    @property
    def hcp(self) -> int:
        """High card points: A=4, K=3, Q=2, J=1."""
        return max(0, self.rank.value - 10)


def full_deck() -> list[Card]:
    """Return a standard 52-card deck."""
    return [Card(suit, rank) for suit in Suit for rank in Rank]
