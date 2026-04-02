"""A Deal represents all four hands plus metadata about the board."""

from __future__ import annotations
from enum import IntEnum
from .card import Card, Suit, full_deck
from .hand import Hand


class Direction(IntEnum):
    """Compass directions / seats at the table."""
    NORTH = 0
    EAST = 1
    SOUTH = 2
    WEST = 3

    @property
    def partner(self) -> "Direction":
        return Direction((self.value + 2) % 4)

    @property
    def lho(self) -> "Direction":
        """Left-hand opponent (next to play in clockwise order)."""
        return Direction((self.value + 1) % 4)

    @property
    def rho(self) -> "Direction":
        """Right-hand opponent."""
        return Direction((self.value + 3) % 4)

    @property
    def is_ns(self) -> bool:
        return self in (Direction.NORTH, Direction.SOUTH)

    @property
    def letter(self) -> str:
        return self.name[0]

    def __str__(self) -> str:
        return self.name.capitalize()

    @classmethod
    def from_char(cls, c: str) -> "Direction":
        mapping = {"N": cls.NORTH, "E": cls.EAST, "S": cls.SOUTH, "W": cls.WEST}
        return mapping[c.upper()]


class Deal:
    """Complete deal: four hands plus optional metadata.

    Attributes:
        hands: dict mapping Direction -> Hand
        dealer: who dealt
        vulnerability: 'None', 'NS', 'EW', 'Both'
        theme: teaching category (e.g. 'Simple Finesse')
        title: descriptive name for this deal
        notes: teaching notes / explanation of the correct line
    """

    def __init__(
        self,
        hands: dict[Direction, Hand] | None = None,
        dealer: Direction = Direction.SOUTH,
        vulnerability: str = "None",
    ):
        self.hands: dict[Direction, Hand] = hands or {d: Hand() for d in Direction}
        self.dealer = dealer
        self.vulnerability = vulnerability
        self.theme: str = ""
        self.title: str = ""
        self.notes: str = ""

    def hand(self, direction: Direction) -> Hand:
        return self.hands[direction]

    # --- Validation ---

    def is_complete(self) -> bool:
        """Check all 52 cards are dealt, 13 per hand."""
        if any(len(h) != 13 for h in self.hands.values()):
            return False
        all_cards = set()
        for h in self.hands.values():
            for c in h:
                all_cards.add(c)
        return len(all_cards) == 52

    def validate(self) -> list[str]:
        """Return a list of issues (empty = valid)."""
        issues = []
        for d in Direction:
            n = len(self.hands[d])
            if n != 13:
                issues.append(f"{d} has {n} cards (expected 13)")
        all_cards = []
        for h in self.hands.values():
            all_cards.extend(h.cards)
        if len(all_cards) != len(set(all_cards)):
            issues.append("Duplicate cards detected")
        if len(set(all_cards)) != 52:
            issues.append(f"Only {len(set(all_cards))} unique cards (expected 52)")
        return issues

    # --- Display ---

    def display(self) -> str:
        """Diagram-style display with North on top."""
        n = self.hands[Direction.NORTH].display().split("\n")
        s = self.hands[Direction.SOUTH].display().split("\n")
        w = self.hands[Direction.WEST].display().split("\n")
        e = self.hands[Direction.EAST].display().split("\n")

        lines = []
        # Title
        if self.title:
            lines.append(f"  {self.title}")
            lines.append("")
        # North
        for line in n:
            lines.append(f"        {line}")
        lines.append("")
        # West and East side by side
        for wl, el in zip(w, e):
            lines.append(f"{wl:<20s}{el}")
        lines.append("")
        # South
        for line in s:
            lines.append(f"        {line}")
        return "\n".join(lines)

    def __repr__(self) -> str:
        return f"Deal(dealer={self.dealer}, complete={self.is_complete()})"

    # --- Factory ---

    @classmethod
    def from_pbn_deal(cls, pbn_deal: str, dealer: Direction = Direction.NORTH) -> "Deal":
        """Parse PBN [Deal] field: 'N:AKQ.JT9.876.5432 ... ... ...'

        The first character is the starting direction, then four hands
        separated by spaces, in clockwise order.
        """
        parts = pbn_deal.strip().split(":")
        if len(parts) == 2:
            dealer = Direction.from_char(parts[0])
            hands_str = parts[1]
        else:
            hands_str = pbn_deal.strip()

        hand_parts = hands_str.strip().split()
        if len(hand_parts) != 4:
            raise ValueError(f"Expected 4 hands, got {len(hand_parts)}")

        hands = {}
        for i, hp in enumerate(hand_parts):
            direction = Direction((dealer.value + i) % 4)
            hands[direction] = Hand.from_pbn(hp)

        return cls(hands=hands, dealer=dealer)
