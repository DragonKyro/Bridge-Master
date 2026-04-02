"""Interactive CLI hand editor for constructing teaching deals.

Provides a step-by-step interface to:
1. Assign cards to each of the four hands
2. Set the contract and declarer
3. Add teaching notes and theme tags
4. Validate the deal
5. Save to a themed collection
"""

from __future__ import annotations
from pathlib import Path
from ..models.card import Card, Suit, Rank, full_deck
from ..models.hand import Hand
from ..models.deal import Deal, Direction
from ..models.game import Contract
from ..formats.collection import ThemeCollection, HandEntry


class HandEditor:
    """Interactive editor for constructing bridge teaching deals."""

    def __init__(self, data_dir: str | Path = "data/themes"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self._reset()

    def _reset(self):
        """Reset to a blank deal."""
        self.deal = Deal()
        self.contract: Contract | None = None
        self.title = ""
        self.notes = ""
        self.theme = ""

    # === CARD ASSIGNMENT ===

    def set_hand(self, direction: Direction, pbn: str) -> list[str]:
        """Set a hand from PBN string. Returns validation issues."""
        try:
            hand = Hand.from_pbn(pbn)
        except ValueError as e:
            return [str(e)]

        self.deal.hands[direction] = hand
        return self._check_conflicts()

    def set_card(self, direction: Direction, card: Card) -> str | None:
        """Add a single card to a hand. Returns error string or None."""
        # Check card isn't already assigned
        for d in Direction:
            if card in self.deal.hands[d]:
                if d == direction:
                    return f"{card} already in {direction}'s hand"
                return f"{card} already assigned to {direction}"

        if len(self.deal.hands[direction]) >= 13:
            return f"{direction}'s hand is full (13 cards)"

        self.deal.hands[direction].add(card)
        return None

    def remove_card(self, direction: Direction, card: Card) -> str | None:
        """Remove a card from a hand. Returns error string or None."""
        if card not in self.deal.hands[direction]:
            return f"{card} not in {direction}'s hand"
        self.deal.hands[direction].remove(card)
        return None

    def unassigned_cards(self) -> list[Card]:
        """Return cards not yet assigned to any hand."""
        assigned = set()
        for d in Direction:
            for c in self.deal.hands[d]:
                assigned.add(c)
        return [c for c in full_deck() if c not in assigned]

    def auto_complete(self) -> None:
        """Randomly assign remaining cards to hands that need them.

        Distributes unassigned cards to fill each hand to 13 cards.
        """
        import random
        remaining = self.unassigned_cards()
        random.shuffle(remaining)

        for d in Direction:
            need = 13 - len(self.deal.hands[d])
            for _ in range(need):
                if remaining:
                    self.deal.hands[d].add(remaining.pop())

    # === METADATA ===

    def set_contract(self, contract_str: str, declarer: str = "S") -> str | None:
        """Set the contract. Returns error string or None."""
        try:
            self.contract = Contract.from_str(contract_str, Direction.from_char(declarer))
            return None
        except (ValueError, KeyError) as e:
            return f"Invalid contract: {e}"

    # === VALIDATION ===

    def validate(self) -> list[str]:
        """Full validation of the deal."""
        issues = self.deal.validate()
        if self.contract is None:
            issues.append("No contract set")
        if not self.title:
            issues.append("No title set")
        return issues

    def _check_conflicts(self) -> list[str]:
        """Check for duplicate cards across hands."""
        seen: dict[Card, Direction] = {}
        issues = []
        for d in Direction:
            for c in self.deal.hands[d]:
                if c in seen:
                    issues.append(f"{c} assigned to both {seen[c]} and {d}")
                seen[c] = d
        return issues

    # === SAVE / LOAD ===

    def to_hand_entry(self) -> HandEntry | str:
        """Convert current state to a HandEntry. Returns error string on failure."""
        issues = self.validate()
        if issues:
            return f"Cannot save: {'; '.join(issues)}"

        # Build the PBN deal string
        hand_strs = []
        start = self.deal.dealer
        for i in range(4):
            d = Direction((start.value + i) % 4)
            hand_strs.append(self.deal.hand(d).pbn_string())
        deal_pbn = f"{start.letter}:{' '.join(hand_strs)}"

        return HandEntry(
            title=self.title,
            deal_pbn=deal_pbn,
            contract=self.contract.display().split(" by ")[0].replace("\u2660", "S").replace("\u2665", "H").replace("\u2666", "D").replace("\u2663", "C"),
            declarer=self.contract.declarer.letter,
            dealer=self.deal.dealer.letter,
            vulnerability=self.deal.vulnerability,
            notes=self.notes,
            par_tricks=None,
        )

    def save_to_collection(self, theme_file: str) -> str:
        """Save current hand to a theme collection. Returns status message."""
        entry = self.to_hand_entry()
        if isinstance(entry, str):
            return entry

        path = self.data_dir / f"{theme_file}.json"
        if path.exists():
            collection = ThemeCollection.load(path)
        else:
            collection = ThemeCollection(
                theme=self.theme or theme_file,
                description="",
                difficulty=1,
            )

        collection.add_hand(entry)
        collection.save(path)
        return f"Saved '{self.title}' to {path} ({len(collection.hands)} hands in collection)"

    # === DISPLAY ===

    def display(self) -> str:
        """Show current state of the editor."""
        lines = []
        lines.append("=" * 50)
        if self.title:
            lines.append(f"Title: {self.title}")
        if self.theme:
            lines.append(f"Theme: {self.theme}")
        if self.contract:
            lines.append(f"Contract: {self.contract.display()}")
        lines.append("")
        lines.append(self.deal.display())
        lines.append("")

        for d in Direction:
            n = len(self.deal.hands[d])
            status = "OK" if n == 13 else f"{n}/13"
            hcp = self.deal.hands[d].hcp
            lines.append(f"  {d}: {status} ({hcp} HCP)")

        remaining = len(self.unassigned_cards())
        if remaining:
            lines.append(f"\n  {remaining} cards unassigned")

        lines.append("=" * 50)
        return "\n".join(lines)

    # === INTERACTIVE CLI ===

    def run_interactive(self) -> None:
        """Run the interactive CLI editor."""
        print("\n=== Bridge Master Hand Editor ===")
        print("Commands: hand, contract, title, theme, notes,")
        print("          auto, validate, show, save, new, quit\n")

        while True:
            try:
                cmd = input("editor> ").strip().lower()
            except (EOFError, KeyboardInterrupt):
                print()
                break

            if not cmd:
                continue
            elif cmd == "quit" or cmd == "q":
                break
            elif cmd == "show":
                print(self.display())
            elif cmd == "hand":
                self._interactive_set_hand()
            elif cmd == "contract":
                self._interactive_set_contract()
            elif cmd == "title":
                self.title = input("  Title: ").strip()
                self.deal.title = self.title
            elif cmd == "theme":
                self.theme = input("  Theme: ").strip()
            elif cmd == "notes":
                self.notes = input("  Notes: ").strip()
                self.deal.notes = self.notes
            elif cmd == "auto":
                self.auto_complete()
                print("  Remaining cards distributed randomly.")
                print(self.display())
            elif cmd == "validate":
                issues = self.validate()
                if issues:
                    for issue in issues:
                        print(f"  ! {issue}")
                else:
                    print("  Deal is valid.")
            elif cmd == "save":
                filename = input("  Theme filename (no extension): ").strip()
                if filename:
                    print(f"  {self.save_to_collection(filename)}")
            elif cmd == "new":
                self._reset()
                print("  Reset to blank deal.")
            else:
                print(f"  Unknown command: {cmd}")

    def _interactive_set_hand(self):
        d_str = input("  Direction (N/E/S/W): ").strip().upper()
        try:
            d = Direction.from_char(d_str)
        except KeyError:
            print(f"  Invalid direction: {d_str}")
            return

        print("  Enter cards as PBN: Spades.Hearts.Diamonds.Clubs")
        print("  Example: AKQ.JT9.876.5432")
        pbn = input("  Cards: ").strip()
        issues = self.set_hand(d, pbn)
        if issues:
            for issue in issues:
                print(f"  ! {issue}")
        else:
            print(f"  {d}: {self.deal.hands[d].pbn_string()}")

    def _interactive_set_contract(self):
        c_str = input("  Contract (e.g. 4S, 3NT): ").strip()
        d_str = input("  Declarer (N/E/S/W) [S]: ").strip().upper() or "S"
        err = self.set_contract(c_str, d_str)
        if err:
            print(f"  ! {err}")
        else:
            print(f"  Contract: {self.contract.display()}")
