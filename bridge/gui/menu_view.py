"""Main menu view."""

from __future__ import annotations
import arcade
from .constants import *


class MenuView(arcade.View):
    """Main menu with buttons for Play, Edit, and List themes."""

    def __init__(self):
        super().__init__()
        self._mouse_x = 0
        self._mouse_y = 0

        self.buttons: list[dict] = []
        self._build_buttons()

        # Static text objects
        self.title_text = arcade.Text(
            "Bridge Master",
            SCREEN_WIDTH // 2, SCREEN_HEIGHT - 150,
            TEXT_COLOR, FONT_SIZE_LARGE + 12,
            anchor_x="center", anchor_y="center", bold=True,
        )
        self.subtitle_text = arcade.Text(
            "Repetition-Based Card Play Trainer",
            SCREEN_WIDTH // 2, SCREEN_HEIGHT - 200,
            TEXT_COLOR, FONT_SIZE_MEDIUM,
            anchor_x="center", anchor_y="center",
        )

        # Button label text objects
        self.button_texts: list[arcade.Text] = []
        for btn in self.buttons:
            self.button_texts.append(arcade.Text(
                btn["label"], btn["x"], btn["y"],
                BUTTON_TEXT, FONT_SIZE_MEDIUM,
                anchor_x="center", anchor_y="center",
            ))

    def _build_buttons(self):
        cx = SCREEN_WIDTH // 2
        self.buttons = [
            {"label": "Play Themes", "x": cx, "y": 500, "action": "play"},
            {"label": "Hand Editor", "x": cx, "y": 400, "action": "edit"},
            {"label": "Browse Themes", "x": cx, "y": 300, "action": "list"},
            {"label": "Quit", "x": cx, "y": 180, "action": "quit"},
        ]

    def on_show_view(self):
        arcade.set_background_color(BG_COLOR)

    def on_draw(self):
        self.clear()

        self.title_text.draw()
        self.subtitle_text.draw()

        for i, btn in enumerate(self.buttons):
            w, h = 240, 50
            hovered = (abs(self._mouse_x - btn["x"]) < w // 2
                       and abs(self._mouse_y - btn["y"]) < h // 2)
            color = BUTTON_HOVER if hovered else BUTTON_COLOR
            rect = arcade.XYWH(btn["x"], btn["y"], w, h)
            arcade.draw_rect_filled(rect, color)
            arcade.draw_rect_outline(rect, TEXT_COLOR, 2)
            self.button_texts[i].draw()

    def on_mouse_motion(self, x, y, dx, dy):
        self._mouse_x = x
        self._mouse_y = y

    def on_mouse_press(self, x, y, button, modifiers):
        for btn in self.buttons:
            w, h = 240, 50
            if abs(x - btn["x"]) < w // 2 and abs(y - btn["y"]) < h // 2:
                self._handle_action(btn["action"])
                return

    def _handle_action(self, action: str):
        if action == "quit":
            arcade.close_window()
        elif action == "play":
            from .theme_browser_view import ThemeBrowserView
            from ..progress import ProgressTracker
            self.window.show_view(ThemeBrowserView(mode="play", progress=ProgressTracker()))
        elif action == "list":
            from .theme_browser_view import ThemeBrowserView
            from ..progress import ProgressTracker
            self.window.show_view(ThemeBrowserView(mode="browse", progress=ProgressTracker()))
        elif action == "edit":
            from .editor_view import EditorView
            self.window.show_view(EditorView())
