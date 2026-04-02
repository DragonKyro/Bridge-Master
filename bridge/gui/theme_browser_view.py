"""Theme browser view — select a theme collection to play or browse."""

from __future__ import annotations
from pathlib import Path
import arcade
from .constants import *
from ..formats.collection import ThemeCollection


DATA_DIR = Path("data/themes")


class ThemeBrowserView(arcade.View):
    """Browse and select theme collections."""

    def __init__(self, mode: str = "play"):
        super().__init__()
        self.mode = mode  # "play" or "browse"
        self.themes: list[ThemeCollection] = []
        self.theme_files: list[str] = []
        self._mouse_x = 0
        self._mouse_y = 0
        self._load_themes()

        # Text objects
        title = "Select Theme to Play" if self.mode == "play" else "Theme Collections"
        self.title_text = arcade.Text(
            title, SCREEN_WIDTH // 2, SCREEN_HEIGHT - 60,
            TEXT_COLOR, FONT_SIZE_LARGE,
            anchor_x="center", anchor_y="center", bold=True,
        )
        self.empty_text = arcade.Text(
            "No themes found. Use the Hand Editor to create one.",
            SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2,
            TEXT_COLOR, FONT_SIZE_MEDIUM,
            anchor_x="center", anchor_y="center",
        )
        self.back_text = arcade.Text(
            "Back", 100, 40, BUTTON_TEXT, FONT_SIZE_MEDIUM,
            anchor_x="center", anchor_y="center",
        )

        # Theme button texts
        self.theme_texts: list[arcade.Text] = []
        self.theme_ys: list[float] = []
        y = SCREEN_HEIGHT - 140
        for coll in self.themes:
            label = f"{coll.theme} ({len(coll.hands)} hands, difficulty {coll.difficulty})"
            self.theme_texts.append(arcade.Text(
                label, SCREEN_WIDTH // 2, y,
                BUTTON_TEXT, FONT_SIZE_MEDIUM,
                anchor_x="center", anchor_y="center",
            ))
            self.theme_ys.append(y)
            y -= 80

    def _load_themes(self):
        self.themes.clear()
        self.theme_files.clear()
        if DATA_DIR.exists():
            for f in sorted(DATA_DIR.glob("*.json")):
                try:
                    collection = ThemeCollection.load(f)
                    self.themes.append(collection)
                    self.theme_files.append(f.stem)
                except Exception:
                    pass

    def on_show_view(self):
        arcade.set_background_color(BG_COLOR)

    def on_draw(self):
        self.clear()

        self.title_text.draw()

        if not self.themes:
            self.empty_text.draw()
        else:
            for i, y in enumerate(self.theme_ys):
                w, h = 600, 60
                cx = SCREEN_WIDTH // 2
                hovered = (abs(self._mouse_x - cx) < w // 2
                           and abs(self._mouse_y - y) < h // 2)
                color = BUTTON_HOVER if hovered else BUTTON_COLOR
                rect = arcade.XYWH(cx, y, w, h)
                arcade.draw_rect_filled(rect, color)
                arcade.draw_rect_outline(rect, TEXT_COLOR, 2)
                self.theme_texts[i].draw()

        # Back button
        bx, by = 100, 40
        rect = arcade.XYWH(bx, by, 140, 40)
        arcade.draw_rect_filled(rect, BUTTON_COLOR)
        arcade.draw_rect_outline(rect, TEXT_COLOR, 2)
        self.back_text.draw()

    def on_mouse_motion(self, x, y, dx, dy):
        self._mouse_x = x
        self._mouse_y = y

    def on_mouse_press(self, x, y, button, modifiers):
        # Back button
        if abs(x - 100) < 70 and abs(y - 40) < 20:
            from .menu_view import MenuView
            self.window.show_view(MenuView())
            return

        # Theme buttons
        for i, y_pos in enumerate(self.theme_ys):
            if abs(x - SCREEN_WIDTH // 2) < 300 and abs(y - y_pos) < 30:
                if self.mode == "play":
                    from .play_view import PlayView
                    self.window.show_view(PlayView(self.theme_files[i]))
                return
