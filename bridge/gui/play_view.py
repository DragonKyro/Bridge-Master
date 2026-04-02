"""Play view — play through hands in a themed collection."""

from __future__ import annotations
from pathlib import Path
import arcade
from .constants import *
from .card_sprites import CardSprite, create_hand_sprites
from ..models.card import Card, Suit
from ..models.deal import Direction
from ..models.game import GameState, Contract
from ..formats.collection import ThemeCollection


DATA_DIR = Path("data/themes")


class PlayView(arcade.View):
    """Play through a themed collection of bridge hands."""

    def __init__(self, theme_file: str):
        super().__init__()
        self.theme_file = theme_file
        self.collection = ThemeCollection.load(DATA_DIR / f"{theme_file}.json")
        self.hand_index = 0
        self.game: GameState | None = None
        self.message = ""
        self.show_notes = False

        # Sprite lists
        self.south_sprites: arcade.SpriteList = arcade.SpriteList()
        self.north_sprites: arcade.SpriteList = arcade.SpriteList()
        self.west_sprites: arcade.SpriteList = arcade.SpriteList()
        self.east_sprites: arcade.SpriteList = arcade.SpriteList()
        self.trick_sprites: arcade.SpriteList = arcade.SpriteList()

        self._mouse_x = 0
        self._mouse_y = 0

        # Static text objects
        self.south_label = arcade.Text(
            "South", SCREEN_WIDTH // 2, SOUTH_Y - 55,
            TEXT_COLOR, FONT_SIZE_SMALL, anchor_x="center",
        )
        self.north_label = arcade.Text(
            "North", SCREEN_WIDTH // 2, NORTH_Y + 55,
            TEXT_COLOR, FONT_SIZE_SMALL, anchor_x="center",
        )
        self.west_label = arcade.Text(
            "West", WEST_X, SCREEN_HEIGHT // 2 + 160,
            TEXT_COLOR, FONT_SIZE_SMALL, anchor_x="center",
        )
        self.east_label = arcade.Text(
            "East", EAST_X, SCREEN_HEIGHT // 2 + 160,
            TEXT_COLOR, FONT_SIZE_SMALL, anchor_x="center",
        )
        self.back_text = arcade.Text(
            "ESC: Back", 60, SCREEN_HEIGHT - 25, BUTTON_TEXT,
            FONT_SIZE_SMALL, anchor_x="center", anchor_y="center",
        )
        self.undo_text = arcade.Text(
            "U: Undo", 170, SCREEN_HEIGHT - 25, BUTTON_TEXT,
            FONT_SIZE_SMALL, anchor_x="center", anchor_y="center",
        )

        # Dynamic text objects
        self.status_text = arcade.Text(
            "", 10, SCREEN_HEIGHT - 25,
            TEXT_COLOR, FONT_SIZE_SMALL,
        )
        self.player_text = arcade.Text(
            "", SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 140,
            (255, 255, 100), FONT_SIZE_MEDIUM,
            anchor_x="center", anchor_y="center",
        )
        self.result_text = arcade.Text(
            "", SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2,
            (100, 255, 100), FONT_SIZE_LARGE,
            anchor_x="center", anchor_y="center", bold=True,
        )
        self.hint_text = arcade.Text(
            "Click anywhere for next hand  |  N = Show notes  |  ESC = Menu",
            SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 40,
            TEXT_COLOR, FONT_SIZE_SMALL,
            anchor_x="center", anchor_y="center",
        )
        self.center_text = arcade.Text(
            "", SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2,
            TEXT_COLOR, FONT_SIZE_LARGE,
            anchor_x="center", anchor_y="center",
        )
        self.notes_text = arcade.Text(
            "", 30, 50,
            (200, 200, 255), FONT_SIZE_SMALL,
            anchor_y="center", multiline=True, width=SCREEN_WIDTH - 60,
        )

        self._load_hand()

    def _load_hand(self):
        """Load the current hand and set up the game."""
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
        self._rebuild_sprites()

    def _rebuild_sprites(self):
        """Rebuild all card sprites from current game state."""
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

        self.trick_sprites = arcade.SpriteList()
        if self.game.current_trick:
            for direction, card in self.game.current_trick.plays:
                sprite = CardSprite(card, face_up=True)
                dx, dy = TRICK_OFFSETS[direction.name]
                sprite.center_x = TRICK_CENTER_X + dx
                sprite.center_y = TRICK_CENTER_Y + dy
                self.trick_sprites.append(sprite)

    def on_show_view(self):
        arcade.set_background_color(BG_COLOR)

    def on_draw(self):
        self.clear()

        # Draw hands and trick
        self.south_sprites.draw()
        self.north_sprites.draw()
        self.west_sprites.draw()
        self.east_sprites.draw()
        self.trick_sprites.draw()

        # Direction labels
        self.south_label.draw()
        self.north_label.draw()
        self.west_label.draw()
        self.east_label.draw()

        # Status bar
        if self.game:
            contract = self.game.contract
            strain = "NT" if contract.strain is None else contract.strain.symbol
            self.status_text.text = (
                f"{self.message}  |  Contract: {contract.level}{strain}  |  "
                f"NS: {self.game.ns_tricks}  EW: {self.game.ew_tricks}  |  "
                f"Need: {contract.tricks_needed}"
            )
            self.status_text.draw()

            if not self.game.is_finished:
                self.player_text.text = f"{self.game.current_player} to play"
                self.player_text.draw()
            else:
                if self.game.made:
                    self.result_text.text = "CONTRACT MADE!"
                    self.result_text.color = (100, 255, 100)
                else:
                    self.result_text.text = f"Down {contract.tricks_needed - self.game.declarer_tricks}"
                    self.result_text.color = (255, 100, 100)
                self.result_text.draw()
                self.hint_text.draw()
        else:
            self.center_text.text = self.message
            self.center_text.draw()

        # Teaching notes overlay
        if self.show_notes and self.hand_index < len(self.collection.hands):
            entry = self.collection.hands[self.hand_index]
            if entry.notes:
                rect = arcade.XYWH(SCREEN_WIDTH // 2, 50, SCREEN_WIDTH - 40, 80)
                arcade.draw_rect_filled(rect, (0, 0, 0, 180))
                self.notes_text.text = entry.notes
                self.notes_text.draw()

        # Toolbar buttons
        rect = arcade.XYWH(60, SCREEN_HEIGHT - 25, 100, 30)
        arcade.draw_rect_filled(rect, BUTTON_COLOR)
        self.back_text.draw()

        rect = arcade.XYWH(170, SCREEN_HEIGHT - 25, 100, 30)
        arcade.draw_rect_filled(rect, BUTTON_COLOR)
        self.undo_text.draw()

    def on_key_press(self, key, modifiers):
        if key == arcade.key.ESCAPE:
            from .menu_view import MenuView
            self.window.show_view(MenuView())
        elif key == arcade.key.U:
            self._undo()
        elif key == arcade.key.N:
            self.show_notes = not self.show_notes

    def on_mouse_motion(self, x, y, dx, dy):
        self._mouse_x = x
        self._mouse_y = y

    def on_mouse_press(self, x, y, button, modifiers):
        if not self.game:
            from .menu_view import MenuView
            self.window.show_view(MenuView())
            return

        if self.game.is_finished:
            self.hand_index += 1
            self._load_hand()
            return

        current = self.game.current_player

        if current == Direction.SOUTH:
            clicked = arcade.get_sprites_at_point((x, y), self.south_sprites)
        elif current == Direction.NORTH:
            clicked = arcade.get_sprites_at_point((x, y), self.north_sprites)
        else:
            self._auto_play_defense()
            return

        if clicked:
            sprite = clicked[-1]
            card = sprite.card
            try:
                self.game.play_card(card)
                self._rebuild_sprites()
                if not self.game.is_finished and not self.game.current_player.is_ns:
                    self._auto_play_defense()
            except ValueError as e:
                self.message = f"Invalid: {e}"

    def _auto_play_defense(self):
        if not self.game or self.game.is_finished:
            return
        while not self.game.is_finished and not self.game.current_player.is_ns:
            legal = self.game.legal_plays()
            if legal:
                self.game.play_card(legal[0])
        self._rebuild_sprites()

    def _undo(self):
        if self.game and not self.game.is_finished:
            card = self.game.undo()
            if card:
                self._rebuild_sprites()
