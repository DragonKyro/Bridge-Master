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
- Arcade 3.x: individual sprites have no `.draw()` method — always use `SpriteList.draw()`. For single sprites, wrap in a temp `SpriteList`.

## Validation
- Run `python -X utf8 -m bridge.utils.validate` to validate all 370 hands
- Run `python -X utf8 -m bridge.utils.validate <file.json>` to validate one file

## Theme categories (22 files, 370 hands)
Beginner through advanced: absolute beginner, basic counting, entries, finesses, suit establishment, hold-up play, trump basics, ruffing, loser handling, notrump play, combination plays, safety plays, endplay, squeeze, trump coups, dummy reversal, defensive, opening lead, declarer by contract type, suit combinations, bidding-play connection, error prevention.

## GUI views
- **MenuView** — Main menu with Play, Edit, Browse, Quit buttons
- **ThemeBrowserView** — Scrollable theme list with completion status (green=done, count shown); scrollbar
- **HandSelectView** — Scrollable list of hands within a theme; shows DONE status; R to resume next incomplete
- **PlayView** — Play hands with card animations, hover highlighting, 1s trick pause, trick history panel (bottom-left), undo; marks hand complete on finish; ESC returns to hand selection
- **EditorView** — Assign cards from palette to hands, set metadata, save to collection

## Progress tracking
- `bridge/progress.py` — `ProgressTracker` saves completed hand indices per theme to `data/progress.json`
- Flow: Theme Browser → Hand Selection → Play → (mark done) → Hand Selection
- Completed themes shown green with "ALL DONE"; partial themes show "X/Y" count

## PlayView animation architecture
- Cards animate from hand to trick center with ease-out motion
- `_anim_card` tracks which card is mid-flight so `_rebuild_sprites()` excludes it from trick_sprites (prevents duplicate)
- On trick completion: only `_rebuild_hand_sprites()` is called (not full rebuild) to preserve the 3 earlier trick cards on screen
- `_place_card_in_trick()` adds the 4th card after animation, then 1s pause shows all 4 cards
- `_finish_trick()` does full rebuild after pause ends
- Hover: shifts the actual sprite in-place before SpriteList.draw(), restores after; no copy created
