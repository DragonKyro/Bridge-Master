# Bridge Master

## Project overview
A repetition-based bridge training tool. Hands are grouped by theme (technique) so players get repeated practice on the same concept — unlike existing software that gives a single hand per theme.

## Architecture
- **Python 3.11+**, arcade 3.x for GUI
- `bridge/models/` — Core OOP: Card, Suit, Rank, Hand, Deal, Trick, GameState, Contract
- `bridge/formats/` — PBN parser/writer + JSON themed collection format
- `bridge/editor/` — Hand editor logic (used by GUI)
- `bridge/gui/` — Arcade GUI views: menu, play, editor, theme browser
- `bridge/utils/` — Validation utilities for deals and collections
- `data/themes/` — 22 JSON theme files, 370 hands total covering all categories
- `cards/` — Card image PNGs (100x140, e.g. `as.png`, `10h.png`)

## Key conventions
- South is always declarer unless specified otherwise
- PBN deal format: `S:spades.hearts.diamonds.clubs` for South West North East (clockwise)
- PBN suit order within a hand: Spades.Hearts.Diamonds.Clubs
- Use `conda activate arcade` then `python bridge.py` to run
- Card image keys: rank + suit lowercase (e.g. `as.png`, `10h.png`, `kd.png`)
- Arcade 3.x API: use `arcade.Text` objects (not `arcade.draw_text`), `self.clear()` (not `arcade.start_render()`), `arcade.draw_rect_filled` with `arcade.XYWH`, `on_show_view()` (not `on_show()`)

## Validation
- Run `python -X utf8 -m bridge.utils.validate` to validate all 370 hands
- Run `python -X utf8 -m bridge.utils.validate <file.json>` to validate one file

## Theme categories (22 files, 370 hands)
Beginner through advanced: absolute beginner, basic counting, entries, finesses, suit establishment, hold-up play, trump basics, ruffing, loser handling, notrump play, combination plays, safety plays, endplay, squeeze, trump coups, dummy reversal, defensive, opening lead, declarer by contract type, suit combinations, bidding-play connection, error prevention.

## GUI views
- **MenuView** — Main menu with Play, Edit, Browse, Quit buttons
- **ThemeBrowserView** — Lists theme collections, click to play
- **PlayView** — Play hands: click cards for declarer/dummy, defense auto-plays
- **EditorView** — Assign cards from palette to hands, set metadata, save to collection
