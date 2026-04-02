"""PBN (Portable Bridge Notation) parser and writer.

PBN is the standard interchange format for bridge hands. A PBN file
contains tag-value pairs in square brackets, e.g.:

    [Event "Bridge Master"]
    [Board "1"]
    [Dealer "S"]
    [Vulnerable "None"]
    [Deal "N:AKQ.JT9.876.5432 ..."]
    [Contract "4S"]
    [Declarer "S"]

This module handles parsing and writing individual deals as well as
multi-deal PBN files.
"""

from __future__ import annotations
import re
from pathlib import Path
from ..models import Deal, Direction, Contract


class PBNParser:
    """Parse and write PBN format."""

    TAG_PATTERN = re.compile(r'\[(\w+)\s+"(.*)"\]')

    @classmethod
    def parse_file(cls, path: str | Path) -> list[dict]:
        """Parse a PBN file into a list of tag dictionaries.

        Each dict represents one board with keys like:
            'Event', 'Board', 'Dealer', 'Deal', 'Contract', etc.
        """
        path = Path(path)
        text = path.read_text(encoding="utf-8")
        return cls.parse_string(text)

    @classmethod
    def parse_string(cls, text: str) -> list[dict]:
        """Parse PBN text into a list of board tag-dicts."""
        boards: list[dict] = []
        current: dict = {}

        for line in text.splitlines():
            line = line.strip()
            if not line or line.startswith("%"):
                if current:
                    boards.append(current)
                    current = {}
                continue

            match = cls.TAG_PATTERN.match(line)
            if match:
                tag, value = match.group(1), match.group(2)
                current[tag] = value

        if current:
            boards.append(current)

        return boards

    @classmethod
    def tags_to_deal(cls, tags: dict) -> Deal:
        """Convert a PBN tag dict into a Deal object."""
        deal_str = tags.get("Deal", "")
        dealer_str = tags.get("Dealer", "N")
        vuln = tags.get("Vulnerable", "None")

        dealer = Direction.from_char(dealer_str)
        deal = Deal.from_pbn_deal(deal_str, dealer=dealer)
        deal.vulnerability = vuln

        return deal

    @classmethod
    def load_deals(cls, path: str | Path) -> list[Deal]:
        """Load a PBN file and return Deal objects."""
        boards = cls.parse_file(path)
        return [cls.tags_to_deal(b) for b in boards]

    # --- Writing ---

    @classmethod
    def deal_to_pbn_string(cls, deal: Deal, contract: Contract | None = None, board_num: int = 1) -> str:
        """Serialize a Deal (and optional Contract) to PBN text."""
        lines = []

        if deal.title:
            lines.append(f'[Event "{deal.title}"]')
        lines.append(f'[Board "{board_num}"]')
        lines.append(f'[Dealer "{deal.dealer.letter}"]')
        lines.append(f'[Vulnerable "{deal.vulnerability}"]')

        # Build deal string starting from dealer
        hand_strs = []
        for i in range(4):
            d = Direction((deal.dealer.value + i) % 4)
            hand_strs.append(deal.hand(d).pbn_string())

        deal_str = f"{deal.dealer.letter}:{' '.join(hand_strs)}"
        lines.append(f'[Deal "{deal_str}"]')

        if contract:
            strain_str = "NT" if contract.strain is None else contract.strain.letter
            lines.append(f'[Contract "{contract.level}{strain_str}"]')
            lines.append(f'[Declarer "{contract.declarer.letter}"]')

        if deal.notes:
            lines.append(f'{{{deal.notes}}}')

        return "\n".join(lines)

    @classmethod
    def write_file(cls, path: str | Path, deals: list[tuple[Deal, Contract | None]]) -> None:
        """Write multiple deals to a PBN file."""
        path = Path(path)
        sections = []
        for i, (deal, contract) in enumerate(deals, 1):
            sections.append(cls.deal_to_pbn_string(deal, contract, board_num=i))
        path.write_text("\n\n".join(sections) + "\n", encoding="utf-8")
