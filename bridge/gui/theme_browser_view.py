"""Theme browser view — select a theme collection to play or browse.

Supports scrolling for large numbers of themes (mouse wheel or Up/Down keys).
"""

from __future__ import annotations
from pathlib import Path
import arcade
from .constants import *
from ..formats.collection import ThemeCollection


DATA_DIR = Path("data/themes")

# Layout
ITEM_HEIGHT = 60
ITEM_SPACING = 10
ITEM_TOTAL = ITEM_HEIGHT + ITEM_SPACING
VISIBLE_TOP = SCREEN_HEIGHT - 100
VISIBLE_BOTTOM = 90
VISIBLE_COUNT = int((VISIBLE_TOP - VISIBLE_BOTTOM) / ITEM_TOTAL)


class ThemeBrowserView(arcade.View):
    """Browse and select theme collections with scrolling."""

    def __init__(self, mode: str = "play"):
        super().__init__()
        self.mode = mode
        self.themes: list[ThemeCollection] = []
        self.theme_files: list[str] = []
        self._mouse_x = 0
        self._mouse_y = 0
        self._scroll_offset = 0  # index of first visible theme
        self._load_themes()

        # Text objects
        title = "Select Theme to Play" if self.mode == "play" else "Theme Collections"
        self.title_text = arcade.Text(
            title, SCREEN_WIDTH // 2, SCREEN_HEIGHT - 40,
            TEXT_COLOR, FONT_SIZE_LARGE,
            anchor_x="center", anchor_y="center", bold=True,
        )
        self.subtitle_text = arcade.Text(
            "", SCREEN_WIDTH // 2, SCREEN_HEIGHT - 70,
            (180, 180, 180), FONT_SIZE_SMALL,
            anchor_x="center", anchor_y="center",
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
        self.scroll_hint = arcade.Text(
            "", SCREEN_WIDTH // 2, 55,
            (150, 150, 150), FONT_SIZE_SMALL,
            anchor_x="center", anchor_y="center",
        )

        # Pre-create reusable text objects for visible items
        self._item_texts: list[arcade.Text] = []
        self._item_detail_texts: list[arcade.Text] = []
        for i in range(VISIBLE_COUNT + 1):
            self._item_texts.append(arcade.Text(
                "", 0, 0, BUTTON_TEXT, FONT_SIZE_MEDIUM,
                anchor_x="center", anchor_y="center",
            ))
            self._item_detail_texts.append(arcade.Text(
                "", 0, 0, (180, 180, 220), FONT_SIZE_TINY,
                anchor_x="center", anchor_y="center",
            ))

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

    @property
    def _max_scroll(self) -> int:
        return max(0, len(self.themes) - VISIBLE_COUNT)

    def on_show_view(self):
        arcade.set_background_color(BG_COLOR)

    def on_draw(self):
        self.clear()

        self.title_text.draw()

        if not self.themes:
            self.empty_text.draw()
        else:
            total = len(self.themes)
            self.subtitle_text.text = f"{total} themes available  |  Scroll with mouse wheel or Up/Down"
            self.subtitle_text.draw()

            # Draw visible items
            visible_end = min(self._scroll_offset + VISIBLE_COUNT, total)
            cx = SCREEN_WIDTH // 2
            w = 700

            for vi, idx in enumerate(range(self._scroll_offset, visible_end)):
                coll = self.themes[idx]
                y = VISIBLE_TOP - vi * ITEM_TOTAL - ITEM_HEIGHT // 2

                hovered = (abs(self._mouse_x - cx) < w // 2
                           and abs(self._mouse_y - y) < ITEM_HEIGHT // 2)
                color = BUTTON_HOVER if hovered else BUTTON_COLOR
                rect = arcade.XYWH(cx, y, w, ITEM_HEIGHT)
                arcade.draw_rect_filled(rect, color)
                arcade.draw_rect_outline(rect, TEXT_COLOR, 1)

                # Theme name
                txt = self._item_texts[vi]
                txt.text = coll.theme
                txt.x = cx
                txt.y = y + 8
                txt.draw()

                # Detail line
                dtxt = self._item_detail_texts[vi]
                diff_label = {1: "Beginner", 2: "Beginner-Int", 3: "Intermediate", 4: "Int-Advanced", 5: "Advanced"}.get(coll.difficulty, str(coll.difficulty))
                dtxt.text = f"{len(coll.hands)} hands  |  {diff_label}"
                dtxt.x = cx
                dtxt.y = y - 12
                dtxt.draw()

            # Scrollbar (right side)
            if total > VISIBLE_COUNT:
                sb_x = cx + w // 2 + 20
                sb_top = VISIBLE_TOP
                sb_bottom = VISIBLE_TOP - VISIBLE_COUNT * ITEM_TOTAL
                sb_height = sb_top - sb_bottom
                track_rect = arcade.XYWH(sb_x, (sb_top + sb_bottom) // 2, 8, sb_height)
                arcade.draw_rect_filled(track_rect, (60, 60, 60))
                arcade.draw_rect_outline(track_rect, (100, 100, 100), 1)

                # Thumb
                thumb_ratio = VISIBLE_COUNT / total
                thumb_h = max(30, sb_height * thumb_ratio)
                scroll_range = sb_height - thumb_h
                if self._max_scroll > 0:
                    thumb_offset = (self._scroll_offset / self._max_scroll) * scroll_range
                else:
                    thumb_offset = 0
                thumb_cy = sb_top - thumb_h / 2 - thumb_offset
                thumb_rect = arcade.XYWH(sb_x, thumb_cy, 8, thumb_h)
                arcade.draw_rect_filled(thumb_rect, (160, 160, 200))

        # Back button
        bx, by = 100, 40
        rect = arcade.XYWH(bx, by, 140, 40)
        arcade.draw_rect_filled(rect, BUTTON_COLOR)
        arcade.draw_rect_outline(rect, TEXT_COLOR, 2)
        self.back_text.draw()

    def on_mouse_motion(self, x, y, dx, dy):
        self._mouse_x = x
        self._mouse_y = y

    def on_mouse_scroll(self, x, y, scroll_x, scroll_y):
        if scroll_y > 0:
            self._scroll_offset = max(0, self._scroll_offset - 1)
        elif scroll_y < 0:
            self._scroll_offset = min(self._max_scroll, self._scroll_offset + 1)

    def on_key_press(self, key, modifiers):
        if key == arcade.key.ESCAPE:
            from .menu_view import MenuView
            self.window.show_view(MenuView())
        elif key == arcade.key.UP:
            self._scroll_offset = max(0, self._scroll_offset - 1)
        elif key == arcade.key.DOWN:
            self._scroll_offset = min(self._max_scroll, self._scroll_offset + 1)
        elif key == arcade.key.PAGEUP:
            self._scroll_offset = max(0, self._scroll_offset - VISIBLE_COUNT)
        elif key == arcade.key.PAGEDOWN:
            self._scroll_offset = min(self._max_scroll, self._scroll_offset + VISIBLE_COUNT)

    def on_mouse_press(self, x, y, button, modifiers):
        # Back button
        if abs(x - 100) < 70 and abs(y - 40) < 20:
            from .menu_view import MenuView
            self.window.show_view(MenuView())
            return

        # Theme buttons
        cx = SCREEN_WIDTH // 2
        w = 700
        visible_end = min(self._scroll_offset + VISIBLE_COUNT, len(self.themes))

        for vi, idx in enumerate(range(self._scroll_offset, visible_end)):
            y_pos = VISIBLE_TOP - vi * ITEM_TOTAL - ITEM_HEIGHT // 2
            if abs(x - cx) < w // 2 and abs(y - y_pos) < ITEM_HEIGHT // 2:
                if self.mode == "play":
                    from .play_view import PlayView
                    self.window.show_view(PlayView(self.theme_files[idx]))
                return
