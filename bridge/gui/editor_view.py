"""Hand editor view — graphical interface for constructing teaching deals."""

from __future__ import annotations
from pathlib import Path
import arcade
from .constants import *
from .card_sprites import CardSprite, create_hand_sprites
from ..models.card import Card, Suit, Rank, full_deck
from ..models.hand import Hand
from ..models.deal import Deal, Direction
from ..models.game import Contract
from ..editor.hand_editor import HandEditor


DATA_DIR = Path("data/themes")

# Layout for the card palette (all 52 cards to pick from)
PALETTE_X_START = 80
PALETTE_Y_START = SCREEN_HEIGHT - 80
PALETTE_X_SPACING = 26
PALETTE_Y_SPACING = 50


class EditorView(arcade.View):
    """Graphical hand editor for constructing bridge teaching deals."""

    def __init__(self):
        super().__init__()
        self.editor = HandEditor(data_dir=DATA_DIR)
        self.selected_direction: Direction = Direction.SOUTH
        self.mode = "assign"
        self.message = ""
        self.input_active = False
        self.input_field = ""
        self.input_value = ""
        self.input_callback = None

        self._mouse_x = 0
        self._mouse_y = 0

        # Card palette sprites
        self.palette_sprites: arcade.SpriteList = arcade.SpriteList()
        self.assigned_cards: set[Card] = set()

        # Hand display sprites
        self.hand_sprites: dict[Direction, arcade.SpriteList] = {
            d: arcade.SpriteList() for d in Direction
        }

        self._build_palette()
        self._rebuild_hand_sprites()

        # Static text objects for metadata panel
        panel_x = SCREEN_WIDTH - 180
        self.meta_title_text = arcade.Text(
            "Metadata", panel_x, SCREEN_HEIGHT - 80,
            TEXT_COLOR, FONT_SIZE_MEDIUM, anchor_x="center", bold=True,
        )

        # Direction label texts (updated dynamically)
        self.dir_texts: dict[Direction, arcade.Text] = {}
        label_positions = {
            Direction.SOUTH: (SCREEN_WIDTH // 2, 30),
            Direction.NORTH: (SCREEN_WIDTH // 2, 430),
            Direction.WEST: (200, 290),
            Direction.EAST: (SCREEN_WIDTH - 200, 290),
        }
        for d, (lx, ly) in label_positions.items():
            self.dir_texts[d] = arcade.Text(
                "", lx, ly, TEXT_COLOR, FONT_SIZE_SMALL, anchor_x="center",
            )

        # Metadata value texts
        self.meta_labels: list[arcade.Text] = []
        self.meta_values: list[arcade.Text] = []
        my = SCREEN_HEIGHT - 120
        for label in ["Title:", "Theme:", "Contract:", "Notes:"]:
            self.meta_labels.append(arcade.Text(
                label, panel_x - 80, my, TEXT_COLOR, FONT_SIZE_SMALL,
            ))
            self.meta_values.append(arcade.Text(
                "(none)", panel_x - 80, my - 18, (180, 180, 255), FONT_SIZE_SMALL,
            ))
            my -= 50

        # Action hint texts
        self.action_texts: list[arcade.Text] = []
        hints = [
            "1-4: Select Dir", "A: Auto-fill", "V: Validate",
            "T: Set Title", "C: Set Contract", "H: Set Theme",
            "N: Set Notes", "S: Save", "R: Reset", "ESC: Back",
        ]
        for i, label in enumerate(hints):
            self.action_texts.append(arcade.Text(
                label, panel_x - 80, my - 20 - i * 30,
                (180, 220, 180), FONT_SIZE_SMALL,
            ))

        # Message bar text
        self.message_text = arcade.Text(
            "", 10, 10, (255, 200, 100), FONT_SIZE_SMALL,
        )

        # Input overlay texts
        self.input_text = arcade.Text(
            "", SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2,
            TEXT_COLOR, FONT_SIZE_MEDIUM,
            anchor_x="center", anchor_y="center",
        )
        self.input_hint = arcade.Text(
            "Enter to confirm, Escape to cancel",
            SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 30,
            (150, 150, 150), FONT_SIZE_SMALL,
            anchor_x="center", anchor_y="center",
        )

    def _build_palette(self):
        self.palette_sprites = arcade.SpriteList()
        suits_order = [Suit.SPADES, Suit.HEARTS, Suit.DIAMONDS, Suit.CLUBS]
        for row, suit in enumerate(suits_order):
            for col, rank in enumerate(reversed(list(Rank))):
                card = Card(suit, rank)
                sprite = CardSprite(card, face_up=True, scale=0.55)
                sprite.center_x = PALETTE_X_START + col * PALETTE_X_SPACING
                sprite.center_y = PALETTE_Y_START - row * PALETTE_Y_SPACING
                self.palette_sprites.append(sprite)

    def _rebuild_hand_sprites(self):
        self.assigned_cards.clear()
        positions = {
            Direction.SOUTH: (SCREEN_WIDTH // 2, 80),
            Direction.NORTH: (SCREEN_WIDTH // 2, 380),
            Direction.WEST: (200, 230),
            Direction.EAST: (SCREEN_WIDTH - 200, 230),
        }
        for d in Direction:
            cards = self.editor.deal.hands[d].cards
            for c in cards:
                self.assigned_cards.add(c)
            cx, cy = positions[d]
            self.hand_sprites[d] = create_hand_sprites(
                cards, cx, cy, fan_offset=22, face_up=True, scale=0.55,
            )
        for sprite in self.palette_sprites:
            sprite.alpha = 80 if sprite.card in self.assigned_cards else 255

    def on_show_view(self):
        arcade.set_background_color(BG_COLOR)

    def on_draw(self):
        self.clear()

        # Palette and hands
        self.palette_sprites.draw()
        for d in Direction:
            self.hand_sprites[d].draw()

        # Direction labels
        for d in Direction:
            n = len(self.editor.deal.hands[d])
            hcp = self.editor.deal.hands[d].hcp
            txt = self.dir_texts[d]
            txt.text = f"{d.name} ({n}/13, {hcp} HCP)"
            txt.color = (255, 255, 100) if d == self.selected_direction else TEXT_COLOR
            txt.bold = (d == self.selected_direction)
            txt.draw()

        # Metadata panel
        self.meta_title_text.draw()

        meta_values = [
            self.editor.title or "(none)",
            self.editor.theme or "(none)",
            self.editor.contract.display() if self.editor.contract else "(none)",
            (self.editor.notes[:20] + "...") if len(self.editor.notes) > 20 else (self.editor.notes or "(none)"),
        ]
        for i in range(4):
            self.meta_labels[i].draw()
            self.meta_values[i].text = meta_values[i]
            self.meta_values[i].draw()

        for txt in self.action_texts:
            txt.draw()

        # Message bar
        if self.message:
            rect = arcade.XYWH(SCREEN_WIDTH // 2, 15, SCREEN_WIDTH, 28)
            arcade.draw_rect_filled(rect, (0, 0, 0, 160))
            self.message_text.text = self.message
            self.message_text.draw()

        # Text input overlay
        if self.input_active:
            rect = arcade.XYWH(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2, 500, 100)
            arcade.draw_rect_filled(rect, (30, 30, 60, 230))
            arcade.draw_rect_outline(rect, TEXT_COLOR, 2)
            self.input_text.text = f"{self.input_field}: {self.input_value}_"
            self.input_text.draw()
            self.input_hint.draw()

    def on_key_press(self, key, modifiers):
        if self.input_active:
            self._handle_text_input(key, modifiers)
            return

        if key == arcade.key.ESCAPE:
            from .menu_view import MenuView
            self.window.show_view(MenuView())
        elif key == arcade.key.KEY_1:
            self.selected_direction = Direction.SOUTH
        elif key == arcade.key.KEY_2:
            self.selected_direction = Direction.NORTH
        elif key == arcade.key.KEY_3:
            self.selected_direction = Direction.WEST
        elif key == arcade.key.KEY_4:
            self.selected_direction = Direction.EAST
        elif key == arcade.key.A:
            self.editor.auto_complete()
            self._rebuild_hand_sprites()
            self.message = "Auto-filled remaining cards"
        elif key == arcade.key.V:
            issues = self.editor.validate()
            self.message = "Valid!" if not issues else "; ".join(issues)
        elif key == arcade.key.T:
            self._start_input("Title", self.editor.title, self._set_title)
        elif key == arcade.key.C:
            self._start_input("Contract (e.g. 4S)", "", self._set_contract)
        elif key == arcade.key.H:
            self._start_input("Theme", self.editor.theme, self._set_theme)
        elif key == arcade.key.N:
            self._start_input("Notes", self.editor.notes, self._set_notes)
        elif key == arcade.key.S:
            self._start_input("Save to filename",
                              self.editor.theme.lower().replace(" ", "_") or "untitled",
                              self._save)
        elif key == arcade.key.R:
            self.editor._reset()
            self._rebuild_hand_sprites()
            self.message = "Reset to blank deal"

    def on_mouse_press(self, x, y, button, modifiers):
        if self.input_active:
            return

        clicked = arcade.get_sprites_at_point((x, y), self.palette_sprites)
        if clicked:
            sprite = clicked[-1]
            card = sprite.card
            if card in self.assigned_cards:
                for d in Direction:
                    if card in self.editor.deal.hands[d]:
                        self.editor.deal.hands[d].remove(card)
                        self.message = f"Removed {card} from {d.name}"
                        break
            else:
                err = self.editor.set_card(self.selected_direction, card)
                if err:
                    self.message = err
                else:
                    self.message = f"Added {card} to {self.selected_direction.name}"
            self._rebuild_hand_sprites()
            return

        for d in Direction:
            clicked = arcade.get_sprites_at_point((x, y), self.hand_sprites[d])
            if clicked:
                sprite = clicked[-1]
                self.editor.deal.hands[d].remove(sprite.card)
                self.message = f"Removed {sprite.card} from {d.name}"
                self._rebuild_hand_sprites()
                return

    # --- Text input handling ---

    def _start_input(self, field: str, initial: str, callback):
        self.input_active = True
        self.input_field = field
        self.input_value = initial
        self.input_callback = callback

    def _handle_text_input(self, key, modifiers):
        if key == arcade.key.ESCAPE:
            self.input_active = False
            return
        if key == arcade.key.ENTER or key == arcade.key.RETURN:
            if self.input_callback:
                self.input_callback(self.input_value)
            self.input_active = False
            return
        if key == arcade.key.BACKSPACE:
            self.input_value = self.input_value[:-1]
            return
        char = self._key_to_char(key, modifiers)
        if char:
            self.input_value += char

    def _key_to_char(self, key, modifiers) -> str:
        shift = modifiers & arcade.key.MOD_SHIFT
        if arcade.key.A <= key <= arcade.key.Z:
            c = chr(key)
            return c.upper() if shift else c.lower()
        if arcade.key.KEY_0 <= key <= arcade.key.KEY_9:
            return chr(key)
        char_map = {
            arcade.key.SPACE: " ", arcade.key.PERIOD: ".",
            arcade.key.COMMA: ",", arcade.key.MINUS: "-",
            arcade.key.SLASH: "/",
        }
        return char_map.get(key, "")

    # --- Callbacks ---

    def _set_title(self, value: str):
        self.editor.title = value
        self.editor.deal.title = value
        self.message = f"Title: {value}"

    def _set_contract(self, value: str):
        err = self.editor.set_contract(value)
        self.message = err if err else f"Contract: {self.editor.contract.display()}"

    def _set_theme(self, value: str):
        self.editor.theme = value
        self.message = f"Theme: {value}"

    def _set_notes(self, value: str):
        self.editor.notes = value
        self.editor.deal.notes = value
        self.message = f"Notes set"

    def _save(self, filename: str):
        result = self.editor.save_to_collection(filename)
        self.message = result
