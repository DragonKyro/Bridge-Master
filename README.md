# Bridge Master

A repetition-based bridge training tool for studying the play of the cards.

## Motivation

Existing bridge software and literature typically illustrate one hand per technique. It's difficult to internalize a concept without sufficient repetition. Bridge Master groups hands by theme so you can practice the same technique (finesses, squeezes, endplays, etc.) across many different deals until it becomes second nature.

## Features

- **GUI application** — Built with arcade 3.x, card images rendered on a green felt table
- **Themed hand collections** — Hands grouped by technique with multiple hands per theme for deliberate practice
- **Hand editor** — Graphical editor for constructing and curating teaching deals
- **PBN support** — Import/export in standard Portable Bridge Notation format
- **Play mode** — Play through themed hands interactively, controlling declarer and dummy

## Quick start

```bash
conda activate arcade
python bridge.py
```

## Project structure

```
bridge/
  models/       Core classes: Card, Hand, Deal, Trick, GameState, Contract
  formats/      PBN parser/writer, JSON themed collections
  editor/       Hand editor logic
  gui/          Arcade GUI views (menu, play, editor, theme browser)
data/
  themes/       JSON theme collections (one file per technique)
cards/          Card image assets (100x140 PNG)
bridge.py       GUI entry point
```

## Data format

Hands are stored in JSON theme collections:

```json
{
  "theme": "Simple Finesses",
  "description": "Practice taking basic finesses...",
  "difficulty": 1,
  "hands": [
    {
      "title": "Finesse Against the King",
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
