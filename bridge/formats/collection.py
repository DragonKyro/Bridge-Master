"""Themed hand collections stored as JSON.

This is the core data format for Bridge Master's teaching approach:
hands are grouped by theme (technique) so players get repeated practice
on the same concept.

JSON structure:
{
    "theme": "Simple Finesse",
    "description": "Taking a finesse when ...",
    "difficulty": 1,
    "hands": [
        {
            "title": "Finesse against the King",
            "deal": "N:AQ.xxx.xxxx.xxxx ...",
            "contract": "3NT",
            "declarer": "S",
            "dealer": "S",
            "vulnerability": "None",
            "notes": "Lead low to the queen...",
            "par_tricks": 9
        },
        ...
    ]
}
"""

from __future__ import annotations
import json
from pathlib import Path
from dataclasses import dataclass, field, asdict
from ..models import Deal, Direction, Contract


@dataclass
class HandEntry:
    """A single teaching hand within a theme."""
    title: str
    deal_pbn: str          # PBN deal string e.g. "N:AKQ.JT9.876.5432 ..."
    contract: str          # e.g. "4S", "3NT"
    declarer: str = "S"
    dealer: str = "S"
    vulnerability: str = "None"
    notes: str = ""
    par_tricks: int | None = None  # expected tricks with double-dummy play

    def to_deal(self) -> Deal:
        deal = Deal.from_pbn_deal(self.deal_pbn)
        deal.dealer = Direction.from_char(self.dealer)
        deal.vulnerability = self.vulnerability
        deal.title = self.title
        deal.notes = self.notes
        return deal

    def to_contract(self) -> Contract:
        return Contract.from_str(self.contract, declarer=Direction.from_char(self.declarer))


@dataclass
class ThemeCollection:
    """A collection of hands grouped by teaching theme."""
    theme: str
    description: str = ""
    difficulty: int = 1           # 1 (beginner) to 5 (expert)
    hands: list[HandEntry] = field(default_factory=list)

    def add_hand(self, entry: HandEntry) -> None:
        self.hands.append(entry)

    def save(self, path: str | Path) -> None:
        """Save collection to JSON file."""
        path = Path(path)
        data = {
            "theme": self.theme,
            "description": self.description,
            "difficulty": self.difficulty,
            "hands": [asdict(h) for h in self.hands],
        }
        path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")

    @classmethod
    def load(cls, path: str | Path) -> "ThemeCollection":
        """Load collection from JSON file."""
        path = Path(path)
        data = json.loads(path.read_text(encoding="utf-8"))
        collection = cls(
            theme=data["theme"],
            description=data.get("description", ""),
            difficulty=data.get("difficulty", 1),
        )
        for h in data.get("hands", []):
            collection.add_hand(HandEntry(**h))
        return collection

    @classmethod
    def list_themes(cls, data_dir: str | Path) -> list[str]:
        """List all theme JSON files in a directory."""
        data_dir = Path(data_dir)
        return [f.stem for f in data_dir.glob("*.json")]

    def __repr__(self) -> str:
        return f"ThemeCollection({self.theme!r}, {len(self.hands)} hands, difficulty={self.difficulty})"
