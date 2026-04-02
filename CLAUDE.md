# Bridge Master

## Project overview
A repetition-based bridge training tool. Hands are grouped by theme (technique) so players get repeated practice on the same concept — unlike existing software that gives a single hand per theme.

## Architecture
- **Python 3.11+**, arcade 3.x for GUI
- `bridge/models/` — Core OOP: Card, Suit, Rank, Hand, Deal, Trick, GameState, Contract
- `bridge/formats/` — PBN parser/writer + JSON themed collection format
- `bridge/editor/` — Hand editor logic (used by GUI)
- `bridge/gui/` — Arcade GUI views: menu, play, editor, theme browser
- `data/themes/` — JSON files, one per theme, containing grouped hands
- `cards/` — Card image PNGs (100x140, e.g. `as.png`, `10h.png`)

## Key conventions
- South is always declarer unless specified otherwise
- PBN suit order: Spades.Hearts.Diamonds.Clubs
- Use `conda activate arcade` then `python bridge.py` to run
- Card image keys: rank + suit lowercase (e.g. `as.png`, `10h.png`, `kd.png`)
- Arcade 3.x API: use `arcade.Text` objects (not `arcade.draw_text`), `self.clear()` (not `arcade.start_render()`), `arcade.draw_rect_filled` with `arcade.XYWH`, `on_show_view()` (not `on_show()`)

## GUI views
- **MenuView** — Main menu with Play, Edit, Browse, Quit buttons
- **ThemeBrowserView** — Lists theme collections, click to play
- **PlayView** — Play hands: click cards for declarer/dummy, defense auto-plays
- **EditorView** — Assign cards from palette to hands, set metadata, save to collection
