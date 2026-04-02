# Bridge Master

A repetition-based bridge training tool for studying the play of the cards.

## Motivation

Existing bridge software and literature typically illustrate one hand per technique. It's difficult to internalize a concept without sufficient repetition. Bridge Master groups hands by theme so you can practice the same technique (finesses, squeezes, endplays, etc.) across many different deals until it becomes second nature.

## Features

- **370 teaching hands** across 22 themed categories, from beginner to advanced
- **GUI application** — Built with arcade 3.x, card images rendered on a green felt table
- **Themed hand collections** — Hands grouped by technique for deliberate practice
- **Hand editor** — Graphical editor for constructing and curating teaching deals
- **PBN support** — Import/export in standard Portable Bridge Notation format
- **Play mode** — Play through themed hands interactively, controlling declarer and dummy
- **Validation utilities** — Verify hand correctness (52 cards, no duplicates, valid suits)

## Quick start

```bash
conda activate arcade
python bridge.py
```

## Validate hands

```bash
python -X utf8 -m bridge.utils.validate
```

## Project structure

```
bridge/
  models/       Core classes: Card, Hand, Deal, Trick, GameState, Contract
  formats/      PBN parser/writer, JSON themed collections
  editor/       Hand editor logic
  gui/          Arcade GUI views (menu, play, editor, theme browser)
  utils/        Validation utilities
data/
  themes/       22 JSON theme collections (370 hands total)
cards/          Card image assets (100x140 PNG)
bridge.py       GUI entry point
```

## Theme categories

| Category | Hands | Difficulty |
|----------|-------|------------|
| Absolute Beginner Declarer Play | 10 | Beginner |
| Basic Counting | 10 | Beginner |
| Entries and Communications | 15 | Beginner-Intermediate |
| Finesse Themes | 25 | Beginner-Advanced |
| Suit Establishment | 20 | Beginner-Intermediate |
| Hold-Up Play and Ducking | 15 | Beginner-Advanced |
| Trump Basics | 22 | Beginner-Advanced |
| Ruffing and Side-Suit Management | 19 | Beginner-Advanced |
| Loser Handling | 14 | Beginner-Advanced |
| Notrump Play | 20 | Beginner-Advanced |
| Combination Plays | 20 | Beginner-Advanced |
| Safety Plays | 10 | Intermediate-Advanced |
| Endplay and Elimination | 15 | Advanced |
| Squeeze Foundations | 15 | Advanced |
| Trump Coups | 10 | Advanced |
| Dummy Reversal | 8 | Advanced |
| Defensive Themes | 36 | Beginner-Advanced |
| Opening Lead | 16 | Beginner-Intermediate |
| Declarer Play by Contract Type | 10 | Beginner-Advanced |
| Suit Combinations | 30 | Beginner-Advanced |
| Bidding-Play Connection | 10 | Intermediate |
| Error Prevention | 20 | Beginner-Intermediate |

## Data format

Hands are stored in JSON theme collections:

```json
{
  "theme": "Finesse Themes",
  "description": "Practice taking finesses...",
  "difficulty": 3,
  "hands": [
    {
      "title": "Simple Finesse",
      "deal_pbn": "S:AKQ.JT9.876.5432 ...",
      "contract": "4H",
      "declarer": "S",
      "notes": "Lead toward the queen..."
    }
  ]
}
```

Also supports PBN (Portable Bridge Notation) for import/export.

## Requirements

- Python 3.11+
- arcade 3.x (via conda: `conda activate arcade`)
