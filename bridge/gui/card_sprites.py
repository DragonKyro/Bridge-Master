"""Card sprite management — loads PNGs and creates clickable card sprites."""

from __future__ import annotations
from pathlib import Path
import arcade
from ..models.card import Card, Suit, Rank
from .constants import CARD_SCALE


CARDS_DIR = Path("cards")


def card_image_path(card: Card) -> str:
    """Get the image file path for a card."""
    return str(CARDS_DIR / f"{card.image_key}.png")


def card_back_path() -> str:
    return str(CARDS_DIR / "cardback.png")


class CardSprite(arcade.Sprite):
    """A sprite representing a single playing card."""

    def __init__(self, card: Card, face_up: bool = True, scale: float = CARD_SCALE):
        self.card = card
        self.face_up = face_up
        path = card_image_path(card) if face_up else card_back_path()
        super().__init__(path_or_texture=path, scale=scale)

    def flip(self):
        """Toggle face up/down."""
        self.face_up = not self.face_up
        path = card_image_path(self.card) if self.face_up else card_back_path()
        self.texture = arcade.load_texture(path)


def create_hand_sprites(
    cards: list[Card],
    center_x: float,
    center_y: float,
    fan_offset: float = 28,
    face_up: bool = True,
    vertical: bool = False,
    scale: float = CARD_SCALE,
) -> arcade.SpriteList:
    """Create a fanned sprite list for a hand of cards."""
    sprite_list = arcade.SpriteList()
    n = len(cards)
    if n == 0:
        return sprite_list

    # Center the fan
    if vertical:
        total_height = (n - 1) * fan_offset
        start_y = center_y + total_height / 2
        for i, card in enumerate(cards):
            sprite = CardSprite(card, face_up=face_up, scale=scale)
            sprite.center_x = center_x
            sprite.center_y = start_y - i * fan_offset
            sprite_list.append(sprite)
    else:
        total_width = (n - 1) * fan_offset
        start_x = center_x - total_width / 2
        for i, card in enumerate(cards):
            sprite = CardSprite(card, face_up=face_up, scale=scale)
            sprite.center_x = start_x + i * fan_offset
            sprite.center_y = center_y
            sprite_list.append(sprite)

    return sprite_list
