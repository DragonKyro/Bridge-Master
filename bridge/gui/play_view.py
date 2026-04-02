"""Play view — play through hands in a themed collection.

Features:
- Card hover highlighting (valid cards only)
- Card play animation
- End-of-trick pause to see all 4 cards
- Trick history panel with paging and bridge orientation
- Trick tracker showing which side won each trick
"""

from __future__ import annotations
from pathlib import Path
import math
import arcade
from .constants import *
from .card_sprites import CardSprite, create_hand_sprites
from ..models.card import Card, Suit
from ..models.deal import Direction
from ..models.game import GameState, Contract
from ..formats.collection import ThemeCollection
from ..progress import ProgressTracker


DATA_DIR = Path("data/themes")


class PlayView(arcade.View):
    """Play through a themed collection of bridge hands."""

    def __init__(self, theme_file: str, progress: ProgressTracker | None = None,
                 start_index: int = 0):
        super().__init__()
        self.theme_file = theme_file
        self.progress = progress or ProgressTracker()
        self.collection = ThemeCollection.load(DATA_DIR / f"{theme_file}.json")
        self.hand_index = start_index
        self.game: GameState | None = None
        self.message = ""
        self.show_notes = False
        self._hand_marked_done = False

        # Sprite lists
        self.south_sprites: arcade.SpriteList = arcade.SpriteList()
        self.north_sprites: arcade.SpriteList = arcade.SpriteList()
        self.west_sprites: arcade.SpriteList = arcade.SpriteList()
        self.east_sprites: arcade.SpriteList = arcade.SpriteList()
        self.trick_sprites: arcade.SpriteList = arcade.SpriteList()

        self._mouse_x = 0
        self._mouse_y = 0

        # Hover state — store the card, not the sprite reference
        self._hovered_card: Card | None = None
        self._valid_cards: set[Card] = set()

        # Animation state
        self._animating = False
        self._anim_list: arcade.SpriteList = arcade.SpriteList()
        self._anim_start_x = 0.0
        self._anim_start_y = 0.0
        self._anim_end_x = 0.0
        self._anim_end_y = 0.0
        self._anim_progress = 0.0
        self._anim_card: Card | None = None  # card being animated (excluded from trick_sprites)
        self._anim_callback = None

        # Trick pause state
        self._trick_paused = False
        self._trick_pause_timer = 0.0

        # Trick history
        self._trick_history: list[dict] = []
        self._history_page = 0
        self._tricks_per_page = 7

        # --- Text objects ---
        self.south_label = arcade.Text(
            "South (You)", SCREEN_WIDTH // 2, LABEL_SOUTH_Y,
            TEXT_COLOR, FONT_SIZE_SMALL, anchor_x="center",
        )
        self.north_label = arcade.Text(
            "North (Dummy)", SCREEN_WIDTH // 2, LABEL_NORTH_Y,
            TEXT_COLOR, FONT_SIZE_SMALL, anchor_x="center",
        )
        self.west_label = arcade.Text(
            "West", WEST_X, LABEL_WEST_Y,
            TEXT_COLOR, FONT_SIZE_SMALL, anchor_x="center",
        )
        self.east_label = arcade.Text(
            "East", EAST_X, LABEL_EAST_Y,
            TEXT_COLOR, FONT_SIZE_SMALL, anchor_x="center",
        )

        self.status_text = arcade.Text(
            "", SCREEN_WIDTH // 2, STATUS_BAR_Y,
            TEXT_COLOR, FONT_SIZE_SMALL, anchor_x="center", anchor_y="center",
        )
        self.back_text = arcade.Text(
            "ESC: Back", 60, TOOLBAR_Y, BUTTON_TEXT,
            FONT_SIZE_SMALL, anchor_x="center", anchor_y="center",
        )
        self.undo_text = arcade.Text(
            "U: Undo", 170, TOOLBAR_Y, BUTTON_TEXT,
            FONT_SIZE_SMALL, anchor_x="center", anchor_y="center",
        )
        self.notes_btn_text = arcade.Text(
            "N: Notes", 280, TOOLBAR_Y, BUTTON_TEXT,
            FONT_SIZE_SMALL, anchor_x="center", anchor_y="center",
        )
        self.player_text = arcade.Text(
            "", SCREEN_WIDTH // 2, TRICK_CENTER_Y - 140,
            (255, 255, 100), FONT_SIZE_MEDIUM,
            anchor_x="center", anchor_y="center",
        )
        self.result_text = arcade.Text(
            "", SCREEN_WIDTH // 2, TRICK_CENTER_Y + 20,
            (100, 255, 100), FONT_SIZE_LARGE,
            anchor_x="center", anchor_y="center", bold=True,
        )
        self.hint_text = arcade.Text(
            "Click to return to hand list  |  N = Notes  |  ESC = Back",
            SCREEN_WIDTH // 2, TRICK_CENTER_Y - 25,
            TEXT_COLOR, FONT_SIZE_SMALL,
            anchor_x="center", anchor_y="center",
        )
        self.center_text = arcade.Text(
            "", SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2,
            TEXT_COLOR, FONT_SIZE_LARGE,
            anchor_x="center", anchor_y="center",
        )
        self.notes_text = arcade.Text(
            "", SCREEN_WIDTH - 540, 45,
            (200, 200, 255), FONT_SIZE_SMALL,
            anchor_y="center", multiline=True, width=520,
        )

        # Trick history panel texts (bottom-left corner)
        px = TRICK_PANEL_X
        py = TRICK_PANEL_Y
        self.score_text = arcade.Text(
            "", px, py + TRICK_PANEL_H // 2 - 8,
            (220, 220, 100), FONT_SIZE_TINY, anchor_x="center", anchor_y="center",
        )
        self._tricks_per_page = 13  # show all tricks, compact rows

        self._load_hand()

    # === Hand loading ===

    def _load_hand(self):
        if self.hand_index >= len(self.collection.hands):
            self.message = "All hands completed!"
            self.game = None
            return

        entry = self.collection.hands[self.hand_index]
        deal = entry.to_deal()
        contract = entry.to_contract()
        self.game = GameState(deal, contract)
        self.message = f"Hand {self.hand_index + 1}/{len(self.collection.hands)}: {entry.title}"
        self.show_notes = False
        self._trick_history.clear()
        self._history_page = 0
        self._animating = False
        self._trick_paused = False
        self._anim_card = None
        self._hovered_card = None
        self._hand_marked_done = False
        self._rebuild_sprites()
        self._update_valid_cards()

    # === Sprite management ===

    def _rebuild_sprites(self):
        if not self.game:
            return

        self.south_sprites = create_hand_sprites(
            self.game.hands[Direction.SOUTH].cards,
            SCREEN_WIDTH // 2, SOUTH_Y,
            fan_offset=CARD_FAN_OFFSET, face_up=True,
        )
        self.north_sprites = create_hand_sprites(
            self.game.hands[Direction.NORTH].cards,
            SCREEN_WIDTH // 2, NORTH_Y,
            fan_offset=CARD_FAN_OFFSET, face_up=True,
        )
        self.west_sprites = create_hand_sprites(
            self.game.hands[Direction.WEST].cards,
            WEST_X, SCREEN_HEIGHT // 2,
            fan_offset=20, face_up=False, vertical=True,
        )
        self.east_sprites = create_hand_sprites(
            self.game.hands[Direction.EAST].cards,
            EAST_X, SCREEN_HEIGHT // 2,
            fan_offset=20, face_up=False, vertical=True,
        )

        # Build trick sprites, but EXCLUDE the card currently being animated
        self.trick_sprites = arcade.SpriteList()
        if self.game.current_trick:
            for direction, card in self.game.current_trick.plays:
                if self._animating and card == self._anim_card:
                    continue  # skip — animation sprite handles this card
                sprite = CardSprite(card, face_up=True)
                dx, dy = TRICK_OFFSETS[direction.name]
                sprite.center_x = TRICK_CENTER_X + dx
                sprite.center_y = TRICK_CENTER_Y + dy
                self.trick_sprites.append(sprite)

    def _rebuild_hand_sprites(self):
        """Rebuild only the four hand sprite lists (not trick sprites)."""
        if not self.game:
            return
        self.south_sprites = create_hand_sprites(
            self.game.hands[Direction.SOUTH].cards,
            SCREEN_WIDTH // 2, SOUTH_Y,
            fan_offset=CARD_FAN_OFFSET, face_up=True,
        )
        self.north_sprites = create_hand_sprites(
            self.game.hands[Direction.NORTH].cards,
            SCREEN_WIDTH // 2, NORTH_Y,
            fan_offset=CARD_FAN_OFFSET, face_up=True,
        )
        self.west_sprites = create_hand_sprites(
            self.game.hands[Direction.WEST].cards,
            WEST_X, SCREEN_HEIGHT // 2,
            fan_offset=20, face_up=False, vertical=True,
        )
        self.east_sprites = create_hand_sprites(
            self.game.hands[Direction.EAST].cards,
            EAST_X, SCREEN_HEIGHT // 2,
            fan_offset=20, face_up=False, vertical=True,
        )

    def _update_valid_cards(self):
        self._valid_cards.clear()
        if self.game and not self.game.is_finished:
            current = self.game.current_player
            if current.is_ns:
                for card in self.game.legal_plays():
                    self._valid_cards.add(card)

    # === Animation ===

    def _animate_card(self, card: Card, from_x: float, from_y: float,
                      to_x: float, to_y: float, callback=None):
        self._animating = True
        self._anim_card = card
        self._anim_list = arcade.SpriteList()
        anim_sprite = CardSprite(card, face_up=True)
        anim_sprite.center_x = from_x
        anim_sprite.center_y = from_y
        self._anim_list.append(anim_sprite)
        self._anim_start_x = from_x
        self._anim_start_y = from_y
        self._anim_end_x = to_x
        self._anim_end_y = to_y
        self._anim_progress = 0.0
        self._anim_callback = callback

    def _get_hand_center(self, direction: Direction) -> tuple[float, float]:
        if direction == Direction.SOUTH:
            return SCREEN_WIDTH // 2, SOUTH_Y
        elif direction == Direction.NORTH:
            return SCREEN_WIDTH // 2, NORTH_Y
        elif direction == Direction.WEST:
            return WEST_X, SCREEN_HEIGHT // 2
        else:
            return EAST_X, SCREEN_HEIGHT // 2

    def on_update(self, delta_time: float):
        if self._animating and self._anim_list:
            sprite = self._anim_list[0]
            dx = self._anim_end_x - self._anim_start_x
            dy = self._anim_end_y - self._anim_start_y
            dist = math.sqrt(dx * dx + dy * dy)
            if dist > 0:
                self._anim_progress = min(1.0, self._anim_progress + CARD_ANIM_SPEED * delta_time / dist)
            else:
                self._anim_progress = 1.0

            t = 1.0 - (1.0 - self._anim_progress) ** 2  # ease-out
            sprite.center_x = self._anim_start_x + dx * t
            sprite.center_y = self._anim_start_y + dy * t

            if self._anim_progress >= 1.0:
                self._animating = False
                self._anim_card = None
                cb = self._anim_callback
                self._anim_list = arcade.SpriteList()
                self._anim_callback = None
                if cb:
                    cb()

        if self._trick_paused:
            self._trick_pause_timer -= delta_time
            if self._trick_pause_timer <= 0:
                self._trick_paused = False
                self._finish_trick()

    # === Play logic ===

    def _place_card_in_trick(self, card: Card, direction: Direction):
        """Add a card sprite to the trick display at its final position."""
        sprite = CardSprite(card, face_up=True)
        dx, dy = TRICK_OFFSETS[direction.name]
        sprite.center_x = TRICK_CENTER_X + dx
        sprite.center_y = TRICK_CENTER_Y + dy
        self.trick_sprites.append(sprite)

    def _play_card_animated(self, card: Card, direction: Direction):
        # Find source position from the sprite
        src_x, src_y = self._get_hand_center(direction)
        for s in self._get_sprites_for_direction(direction):
            if hasattr(s, 'card') and s.card == card:
                src_x, src_y = s.center_x, s.center_y
                break

        # Target position
        dx, dy = TRICK_OFFSETS[direction.name]
        tgt_x = TRICK_CENTER_X + dx
        tgt_y = TRICK_CENTER_Y + dy

        # Play card in game state first
        result = self.game.play_card(card)

        if result["trick_complete"]:
            def on_anim_done():
                self._anim_card = None
                # Add final card to trick display — all 4 now visible
                self._place_card_in_trick(card, direction)
                self._record_trick(result)
                self._trick_paused = True
                self._trick_pause_timer = TRICK_PAUSE_DURATION
            self._animate_card(card, src_x, src_y, tgt_x, tgt_y, on_anim_done)
            # Only rebuild hands — preserve trick_sprites showing first 3 cards
            self._rebuild_hand_sprites()
            self._update_valid_cards()
        else:
            def on_anim_done():
                self._anim_card = None
                self._rebuild_sprites()
                if not self.game.is_finished and not self.game.current_player.is_ns:
                    self._auto_play_defense_step()
                else:
                    self._update_valid_cards()
            self._animate_card(card, src_x, src_y, tgt_x, tgt_y, on_anim_done)
            # Full rebuild — trick_sprites excludes animated card
            self._rebuild_sprites()
            self._update_valid_cards()

    def _auto_play_defense_step(self):
        if not self.game or self.game.is_finished or self.game.current_player.is_ns:
            self._update_valid_cards()
            return

        direction = self.game.current_player
        legal = self.game.legal_plays()
        if not legal:
            return

        card = legal[0]
        src_x, src_y = self._get_hand_center(direction)
        dx, dy = TRICK_OFFSETS[direction.name]
        tgt_x = TRICK_CENTER_X + dx
        tgt_y = TRICK_CENTER_Y + dy

        result = self.game.play_card(card)

        if result["trick_complete"]:
            def on_anim_done():
                self._anim_card = None
                # Add final card — all 4 visible during pause
                self._place_card_in_trick(card, direction)
                self._rebuild_hand_sprites()
                self._record_trick(result)
                self._trick_paused = True
                self._trick_pause_timer = TRICK_PAUSE_DURATION
            self._animate_card(card, src_x, src_y, tgt_x, tgt_y, on_anim_done)
            # Only rebuild hands — preserve trick_sprites showing first 3 cards
            self._rebuild_hand_sprites()
        else:
            def on_anim_done():
                self._anim_card = None
                self._rebuild_sprites()
                if not self.game.is_finished and not self.game.current_player.is_ns:
                    self._auto_play_defense_step()
                else:
                    self._update_valid_cards()
            self._animate_card(card, src_x, src_y, tgt_x, tgt_y, on_anim_done)
            # Full rebuild — trick excludes animated card
            self._rebuild_sprites()

    def _finish_trick(self):
        self._rebuild_sprites()
        self._update_valid_cards()
        if not self.game.is_finished and not self.game.current_player.is_ns:
            self._auto_play_defense_step()

    def _record_trick(self, result: dict):
        last_trick = self.game.completed_tricks[-1]
        self._trick_history.append({
            "number": len(self._trick_history) + 1,
            "leader": last_trick.leader,
            "plays": list(last_trick.plays),
            "winner": result["trick_winner"],
        })
        max_page = max(0, (len(self._trick_history) - 1) // self._tricks_per_page)
        self._history_page = max_page

    def _get_sprites_for_direction(self, direction: Direction) -> arcade.SpriteList:
        return {
            Direction.SOUTH: self.south_sprites,
            Direction.NORTH: self.north_sprites,
            Direction.WEST: self.west_sprites,
            Direction.EAST: self.east_sprites,
        }[direction]

    # === Drawing ===

    def on_show_view(self):
        arcade.set_background_color(BG_COLOR)

    def on_draw(self):
        self.clear()

        # Trick history panel first (behind cards)
        self._draw_trick_history()

        # Draw hands — shift hovered card in-place before drawing
        hovered_sprite = None
        hover_lift = 0
        if self._hovered_card and not self._animating and not self._trick_paused:
            current = self.game.current_player if self.game and not self.game.is_finished else None
            if current == Direction.SOUTH:
                for s in self.south_sprites:
                    if hasattr(s, 'card') and s.card == self._hovered_card:
                        hovered_sprite = s
                        hover_lift = 15
                        break
            elif current == Direction.NORTH:
                for s in self.north_sprites:
                    if hasattr(s, 'card') and s.card == self._hovered_card:
                        hovered_sprite = s
                        hover_lift = -15
                        break

        # Temporarily shift the hovered sprite
        if hovered_sprite:
            hovered_sprite.center_y += hover_lift

        self.south_sprites.draw()
        self.north_sprites.draw()
        self.west_sprites.draw()
        self.east_sprites.draw()

        # Restore position
        if hovered_sprite:
            hovered_sprite.center_y -= hover_lift
            # Draw glow behind the lifted position
            glow_rect = arcade.XYWH(
                hovered_sprite.center_x, hovered_sprite.center_y + hover_lift,
                hovered_sprite.width + 6, hovered_sprite.height + 6,
            )
            arcade.draw_rect_filled(glow_rect, HIGHLIGHT_COLOR)
            # Re-draw just that card on top of glow via temp list
            tmp = arcade.SpriteList()
            tmp.append(hovered_sprite)
            hovered_sprite.center_y += hover_lift
            tmp.draw()
            hovered_sprite.center_y -= hover_lift

        # Trick sprites (cards already played to current trick)
        self.trick_sprites.draw()

        # Animation sprite on top of everything
        if self._animating and self._anim_list:
            self._anim_list.draw()

        # Direction labels
        self.south_label.draw()
        self.north_label.draw()
        self.west_label.draw()
        self.east_label.draw()

        # Status bar
        rect = arcade.XYWH(SCREEN_WIDTH // 2, STATUS_BAR_Y, SCREEN_WIDTH, 28)
        arcade.draw_rect_filled(rect, (0, 0, 0, 140))

        if self.game:
            contract = self.game.contract
            strain = "NT" if contract.strain is None else contract.strain.symbol
            self.status_text.text = (
                f"{self.message}  |  Contract: {contract.level}{strain}  |  "
                f"NS: {self.game.ns_tricks}  EW: {self.game.ew_tricks}  |  "
                f"Need: {contract.tricks_needed}"
            )
            self.status_text.draw()

            if self.game.is_finished:
                # Mark completed on first finish
                if not self._hand_marked_done:
                    self.progress.mark_completed(self.theme_file, self.hand_index)
                    self._hand_marked_done = True
                if self.game.made:
                    self.result_text.text = "CONTRACT MADE!"
                    self.result_text.color = (100, 255, 100)
                else:
                    self.result_text.text = f"Down {contract.tricks_needed - self.game.declarer_tricks}"
                    self.result_text.color = (255, 100, 100)
                self.result_text.draw()
                self.hint_text.draw()
            elif not self._animating and not self._trick_paused:
                self.player_text.text = f"{self.game.current_player} to play"
                self.player_text.draw()
        else:
            self.center_text.text = self.message
            self.center_text.draw()

        # Toolbar
        for bx, txt in [(60, self.back_text), (170, self.undo_text), (280, self.notes_btn_text)]:
            r = arcade.XYWH(bx, TOOLBAR_Y, 100, 26)
            arcade.draw_rect_filled(r, BUTTON_COLOR)
            txt.draw()

        # Notes overlay
        if self.show_notes and self.hand_index < len(self.collection.hands):
            entry = self.collection.hands[self.hand_index]
            if entry.notes:
                notes_w = 560
                notes_cx = SCREEN_WIDTH - notes_w // 2 - 10
                rect = arcade.XYWH(notes_cx, 45, notes_w, 70)
                arcade.draw_rect_filled(rect, (0, 0, 0, 200))
                self.notes_text.text = entry.notes
                self.notes_text.draw()

    def _draw_trick_history(self):
        if not self.game:
            return

        px = TRICK_PANEL_X
        py = TRICK_PANEL_Y
        pw = TRICK_PANEL_W
        ph = TRICK_PANEL_H

        # Panel background
        panel_rect = arcade.XYWH(px, py, pw, ph)
        arcade.draw_rect_filled(panel_rect, PANEL_BG)
        arcade.draw_rect_outline(panel_rect, (80, 120, 80), 1)

        # Score at top of panel
        contract = self.game.contract
        needed = contract.tricks_needed
        got = self.game.declarer_tricks
        remaining = max(0, needed - got)
        self.score_text.text = f"NS:{self.game.ns_tricks}  EW:{self.game.ew_tricks}  Need:{remaining}"
        self.score_text.draw()

        if not self._trick_history:
            return

        # Compact rows: header + up to 13 trick lines
        left = px - pw // 2 + 8
        top_y = py + ph // 2 - 25
        row_h = 13  # pixels per row

        # Column positions
        c0 = left         # #
        c1 = left + 18    # N
        c2 = left + 55    # E
        c3 = left + 92    # S
        c4 = left + 129   # W
        cols = [c1, c2, c3, c4]

        # Header
        hdr_color = (150, 150, 150)
        arcade.draw_text("#", c0, top_y, hdr_color, 9, bold=True)
        arcade.draw_text("N", c1, top_y, hdr_color, 9, bold=True)
        arcade.draw_text("E", c2, top_y, hdr_color, 9, bold=True)
        arcade.draw_text("S", c3, top_y, hdr_color, 9, bold=True)
        arcade.draw_text("W", c4, top_y, hdr_color, 9, bold=True)

        dirs_order = [Direction.NORTH, Direction.EAST, Direction.SOUTH, Direction.WEST]

        for i, trick in enumerate(self._trick_history):
            y = top_y - (i + 1) * row_h
            if y < py - ph // 2 + 5:
                break  # out of panel space

            winner = trick["winner"]
            is_ns = winner.is_ns

            # Subtle row tint
            tint = (*NS_WIN_COLOR[:3], 20) if is_ns else (*EW_WIN_COLOR[:3], 20)
            row_rect = arcade.XYWH(px, y + 4, pw - 6, row_h)
            arcade.draw_rect_filled(row_rect, tint)

            # Trick number
            arcade.draw_text(str(trick["number"]), c0, y, TEXT_COLOR, 9)

            # Cards per direction
            plays_by_dir = {d: c for d, c in trick["plays"]}
            for j, d in enumerate(dirs_order):
                card = plays_by_dir.get(d)
                if card:
                    if d == winner:
                        arcade.draw_text(card.short, cols[j], y, (255, 255, 100), 9, bold=True)
                    elif card.suit in (Suit.HEARTS, Suit.DIAMONDS):
                        arcade.draw_text(card.short, cols[j], y, (255, 100, 100), 9)
                    else:
                        arcade.draw_text(card.short, cols[j], y, TEXT_COLOR, 9)

    # === Input ===

    def on_key_press(self, key, modifiers):
        if self._animating or self._trick_paused:
            return
        if key == arcade.key.ESCAPE:
            from .hand_select_view import HandSelectView
            self.window.show_view(HandSelectView(self.theme_file, self.progress))
        elif key == arcade.key.U:
            self._undo()
        elif key == arcade.key.N:
            self.show_notes = not self.show_notes
        elif key == arcade.key.LEFT:
            self._history_page = max(0, self._history_page - 1)
        elif key == arcade.key.RIGHT:
            max_page = max(0, (len(self._trick_history) - 1) // self._tricks_per_page)
            self._history_page = min(max_page, self._history_page + 1)

    def on_mouse_motion(self, x, y, dx, dy):
        self._mouse_x = x
        self._mouse_y = y
        self._update_hover(x, y)

    def _update_hover(self, x: float, y: float):
        self._hovered_card = None
        if not self.game or self.game.is_finished or self._animating or self._trick_paused:
            return
        current = self.game.current_player
        if current == Direction.SOUTH:
            sprites = self.south_sprites
        elif current == Direction.NORTH:
            sprites = self.north_sprites
        else:
            return
        clicked = arcade.get_sprites_at_point((x, y), sprites)
        if clicked:
            sprite = clicked[-1]
            if hasattr(sprite, 'card') and sprite.card in self._valid_cards:
                self._hovered_card = sprite.card

    def on_mouse_press(self, x, y, button, modifiers):
        if self._animating or self._trick_paused:
            return
        if not self.game:
            from .hand_select_view import HandSelectView
            self.window.show_view(HandSelectView(self.theme_file, self.progress))
            return
        if self.game.is_finished:
            # Return to hand selection
            from .hand_select_view import HandSelectView
            self.window.show_view(HandSelectView(self.theme_file, self.progress))
            return
        current = self.game.current_player
        if not current.is_ns:
            self._auto_play_defense_step()
            return
        if current == Direction.SOUTH:
            sprites = self.south_sprites
        elif current == Direction.NORTH:
            sprites = self.north_sprites
        else:
            return
        clicked = arcade.get_sprites_at_point((x, y), sprites)
        if clicked:
            sprite = clicked[-1]
            if hasattr(sprite, 'card') and sprite.card in self._valid_cards:
                self._hovered_card = None
                self._play_card_animated(sprite.card, current)

    def _undo(self):
        if not self.game or self.game.is_finished:
            return
        card = self.game.undo()
        if card:
            if self._trick_history and len(self.game.completed_tricks) < len(self._trick_history):
                self._trick_history.pop()
            self._rebuild_sprites()
            self._update_valid_cards()
