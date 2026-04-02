"""Validation utilities for bridge deals and hand collections.

Checks:
- Each deal has exactly 52 unique cards
- Each player has exactly 13 cards
- Each suit has exactly 13 cards across all players
- PBN format is parseable
- Contract is valid

Usage:
    python -m bridge.utils.validate             # validate all themes
    python -m bridge.utils.validate <file.json> # validate one file
"""

import sys
import json
from pathlib import Path
from ..models.card import Suit, Rank
from ..models.deal import Deal, Direction
from ..models.game import Contract


DATA_DIR = Path("data/themes")
FULL_SUIT = set(Rank)


def validate_deal_pbn(deal_pbn: str, title: str = "") -> list[str]:
    """Validate a PBN deal string. Returns list of issues (empty = valid)."""
    issues = []
    label = f"[{title}] " if title else ""

    try:
        deal = Deal.from_pbn_deal(deal_pbn)
    except Exception as e:
        return [f"{label}Parse error: {e}"]

    # Check 13 cards per hand
    for d in Direction:
        n = len(deal.hands[d])
        if n != 13:
            issues.append(f"{label}{d.name} has {n} cards (need 13)")

    # Check no duplicates and full deck
    all_cards = []
    for d in Direction:
        all_cards.extend(deal.hands[d].cards)

    if len(all_cards) != len(set(all_cards)):
        seen = set()
        for c in all_cards:
            if c in seen:
                issues.append(f"{label}Duplicate card: {c.short}")
            seen.add(c)

    if len(set(all_cards)) != 52:
        issues.append(f"{label}{len(set(all_cards))} unique cards (need 52)")

    # Check each suit has 13 cards
    for suit in Suit:
        suit_cards = [c for c in all_cards if c.suit == suit]
        ranks = set(c.rank for c in suit_cards)
        if ranks != FULL_SUIT:
            missing = FULL_SUIT - ranks
            if missing:
                issues.append(f"{label}{suit.letter} missing ranks: {[r.symbol for r in missing]}")
            if len(suit_cards) != 13:
                issues.append(f"{label}{suit.letter} has {len(suit_cards)} cards (need 13)")

    return issues


def validate_collection(path: Path) -> tuple[int, int, list[str]]:
    """Validate a theme collection JSON file.

    Returns:
        (total_hands, valid_hands, list_of_issues)
    """
    issues = []

    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception as e:
        return 0, 0, [f"JSON parse error: {e}"]

    hands = data.get("hands", [])
    total = len(hands)
    valid = 0

    for hand in hands:
        title = hand.get("title", "?")
        deal_pbn = hand.get("deal_pbn", "")
        contract_str = hand.get("contract", "")

        hand_issues = validate_deal_pbn(deal_pbn, title)

        if contract_str:
            try:
                Contract.from_str(contract_str)
            except Exception as e:
                hand_issues.append(f"[{title}] Invalid contract '{contract_str}': {e}")

        if hand_issues:
            issues.extend(hand_issues)
        else:
            valid += 1

    return total, valid, issues


def main():
    """CLI entry point for validation."""
    # Optional: validate a specific file
    if len(sys.argv) > 1:
        target = Path(sys.argv[1])
        if not target.exists():
            target = DATA_DIR / sys.argv[1]
        if not target.exists():
            print(f"File not found: {sys.argv[1]}")
            return
        total, valid, issues = validate_collection(target)
        print(f"{target.name}: {valid}/{total} valid")
        for issue in issues:
            print(f"  {issue}")
        return

    # Validate all theme files
    print("=== Bridge Hand Validation ===\n")

    total_hands = 0
    total_valid = 0
    all_issues = []

    for path in sorted(DATA_DIR.glob("*.json")):
        total, valid, issues = validate_collection(path)
        total_hands += total
        total_valid += valid
        status = "OK" if not issues else f"{len(issues)} issues"
        print(f"  {path.name}: {valid}/{total} valid ({status})")
        if issues:
            for issue in issues[:5]:
                print(f"    {issue}")
            if len(issues) > 5:
                print(f"    ... and {len(issues) - 5} more")
        all_issues.extend(issues)

    print(f"\n  TOTAL: {total_valid}/{total_hands} hands valid")
    if all_issues:
        print(f"  {len(all_issues)} total issues found")
    else:
        print("  All hands valid!")


if __name__ == "__main__":
    main()
