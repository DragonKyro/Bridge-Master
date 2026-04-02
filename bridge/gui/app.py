"""Main application window."""

import arcade
from .constants import SCREEN_WIDTH, SCREEN_HEIGHT, SCREEN_TITLE, BG_COLOR
from .menu_view import MenuView


class BridgeMasterApp(arcade.Window):
    """Main application window for Bridge Master."""

    def __init__(self):
        super().__init__(SCREEN_WIDTH, SCREEN_HEIGHT, SCREEN_TITLE)
        arcade.set_background_color(BG_COLOR)

    def setup(self):
        """Show the main menu."""
        menu = MenuView()
        self.show_view(menu)
