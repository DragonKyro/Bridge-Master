"""GameState: manages playing a bridge hand under the rules of the game."""

from __future__ import annotations
from dataclasses import dataclass
from copy import deepcopy
from .card import Card, Suit
from .hand import Hand
from .deal import Deal, Direction
from .trick import Trick


@dataclass
class Contract:
    """A bridge contract.

    Attributes:
        level: 1-7
        strain: trump suit, or None for notrump
        declarer: who declared
        doubled: 0=undoubled, 1=doubled, 2=redoubled
    """
    level: int
    strain: Suit | None  # None = notrump
    declarer: Direction
    doubled: int = 0

    @property
    def tricks_needed(self) -> int:
        """Tricks declarer needs to make the contract."""
        return self.level + 6

    @property
    def dummy(self) -> Direction:
        return self.declarer.partner

    @property
    def opening_leader(self) -> Direction:
        return self.declarer.lho

    def display(self) -> str:
        strain_str = "NT" if self.strain is None else self.strain.symbol
        dbl = {0: "", 1: "X", 2: "XX"}[self.doubled]
        return f"{self.level}{strain_str}{dbl} by {self.declarer}"

    @classmethod
    def from_str(cls, s: str, declarer: Direction = Direction.SOUTH) -> "Contract":
        """Parse e.g. '4S', '3NT', '6HX' into a Contract."""
        s = s.strip().upper()
        doubled = 0
        if s.endswith("XX"):
            doubled = 2
            s = s[:-2]
        elif s.endswith("X"):
            doubled = 1
            s = s[:-1]

        level = int(s[0])
        strain_str = s[1:]
        if strain_str == "NT" or strain_str == "N":
            strain = None
        else:
            strain = Suit.from_char(strain_str)

        return cls(level=level, strain=strain, declarer=declarer, doubled=doubled)


class GameState:
    """Tracks the complete state of play for one deal.

    This is the core engine that enforces bridge playing rules:
    - Must follow suit if able
    - Trick winner leads to next trick
    - Tracks tricks won by each side
    """

    def __init__(self, deal: Deal, contract: Contract):
        self.deal = deal
        self.contract = contract
        self.trump = contract.strain

        # Working copies of hands (cards are removed as played)
        self.hands: dict[Direction, Hand] = deepcopy(deal.hands)

        # Trick history
        self.completed_tricks: list[Trick] = []
        self.current_trick: Trick | None = None

        # Score tracking
        self.ns_tricks = 0
        self.ew_tricks = 0

        # Start with opening lead
        self._start_new_trick(contract.opening_leader)

    # --- State queries ---

    @property
    def current_player(self) -> Direction:
        if self.current_trick is None:
            raise ValueError("Game is over")
        return self.current_trick.current_player

    @property
    def is_finished(self) -> bool:
        return self.ns_tricks + self.ew_tricks == 13

    @property
    def declarer_tricks(self) -> int:
        return self.ns_tricks if self.contract.declarer.is_ns else self.ew_tricks

    @property
    def made(self) -> bool:
        return self.declarer_tricks >= self.contract.tricks_needed

    def legal_plays(self, direction: Direction | None = None) -> list[Card]:
        """Return the list of legal cards for the given direction (default: current player)."""
        if direction is None:
            direction = self.current_player
        hand = self.hands[direction]

        if self.current_trick is None or not self.current_trick.plays:
            # Leading: any card is legal
            return hand.cards

        led_suit = self.current_trick.led_suit
        in_suit = hand.suit_cards(led_suit)
        if in_suit:
            return in_suit  # must follow suit
        return hand.cards  # void: can play anything

    # --- Play ---

    def play_card(self, card: Card) -> dict:
        """Play a card for the current player. Returns a result dict.

        Result keys:
            player: who played
            card: what was played
            trick_complete: bool
            trick_winner: Direction or None
            game_over: bool
        """
        if self.is_finished:
            raise ValueError("Game is already finished")

        direction = self.current_player
        hand = self.hands[direction]

        if card not in hand:
            raise ValueError(f"{direction} does not hold {card}")
        if card not in self.legal_plays(direction):
            raise ValueError(f"{card} is not a legal play (must follow suit)")

        # Play the card
        hand.remove(card)
        self.current_trick.play(direction, card)

        result = {
            "player": direction,
            "card": card,
            "trick_complete": False,
            "trick_winner": None,
            "game_over": False,
        }

        # Check if trick is complete
        if self.current_trick.is_complete:
            winner = self.current_trick.winner()
            result["trick_complete"] = True
            result["trick_winner"] = winner

            if winner.is_ns:
                self.ns_tricks += 1
            else:
                self.ew_tricks += 1

            self.completed_tricks.append(self.current_trick)

            if self.is_finished:
                self.current_trick = None
                result["game_over"] = True
            else:
                self._start_new_trick(winner)

        return result

    def undo(self) -> Card | None:
        """Undo the last card played. Returns the card, or None if nothing to undo."""
        if self.current_trick and self.current_trick.plays:
            direction, card = self.current_trick.plays.pop()
            self.hands[direction].add(card)
            return card

        if not self.completed_tricks:
            return None

        # Reopen last completed trick
        last_trick = self.completed_tricks.pop()
        winner = last_trick.winner()
        if winner.is_ns:
            self.ns_tricks -= 1
        else:
            self.ew_tricks -= 1

        self.current_trick = last_trick
        direction, card = self.current_trick.plays.pop()
        self.hands[direction].add(card)
        return card

    # --- Internals ---

    def _start_new_trick(self, leader: Direction) -> None:
        self.current_trick = Trick(leader=leader, trump=self.trump)

    # --- Snapshot for solver ---

    def clone(self) -> "GameState":
        """Deep copy the game state (used by solver for search)."""
        new = GameState.__new__(GameState)
        new.deal = self.deal
        new.contract = self.contract
        new.trump = self.trump
        new.hands = {d: Hand(list(h.cards)) for d, h in self.hands.items()}
        new.completed_tricks = list(self.completed_tricks)  # shallow is fine
        new.ns_tricks = self.ns_tricks
        new.ew_tricks = self.ew_tricks
        if self.current_trick:
            new.current_trick = Trick(
                leader=self.current_trick.leader, trump=self.trump
            )
            for d, c in self.current_trick.plays:
                new.current_trick.plays.append((d, c))
        else:
            new.current_trick = None
        return new

    # --- Display ---

    def display_status(self) -> str:
        lines = [
            f"Contract: {self.contract.display()}",
            f"Tricks: NS={self.ns_tricks} EW={self.ew_tricks}",
            f"Needed: {self.contract.tricks_needed}",
        ]
        if self.current_trick and self.current_trick.plays:
            lines.append(f"Current trick: {self.current_trick}")
        if not self.is_finished:
            lines.append(f"To play: {self.current_player}")
        else:
            lines.append(f"Result: {'Made' if self.made else 'Down'}")
        return "\n".join(lines)
