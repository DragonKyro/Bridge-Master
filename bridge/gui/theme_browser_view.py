"""Theme browser view — select a theme collection to play or browse.

Shows completion status per theme. Clicking a theme opens hand selection.
"""

from __future__ import annotations
from pathlib import Path
import arcade
from .constants import *
from ..formats.collection import ThemeCollection
from ..progress import ProgressTracker


DATA_DIR = Path("data/themes")

# Layout
ITEM_HEIGHT = 60
ITEM_SPACING = 10
ITEM_TOTAL = ITEM_HEIGHT + ITEM_SPACING
VISIBLE_TOP = SCREEN_HEIGHT - 100
VISIBLE_BOTTOM = 90
VISIBLE_COUNT = int((VISIBLE_TOP - VISIBLE_BOTTOM) / ITEM_TOTAL)

# Theme completion colors
THEME_DONE_BG = (30, 80, 30)
THEME_PARTIAL_BG = BUTTON_COLOR
THEME_DONE_BORDER = (80, 180, 80)
THEME_PARTIAL_BORDER = (120, 120, 180)


class ThemeBrowserView(arcade.View):
    """Browse and select theme collections with scrolling and completion status."""

    def __init__(self, mode: str = "play", progress: ProgressTracker | None = None):
        super().__init__()
        self.mode = mode
        self.progress = progress or ProgressTracker()
        self.themes: list[ThemeCollection] = []
        self.theme_files: list[str] = []
        self._mouse_x = 0
        self._mouse_y = 0
        self._scroll_offset = 0
        self._load_themes()

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

        self._item_texts: list[arcade.Text] = []
        self._item_detail_texts: list[arcade.Text] = []
        self._item_progress_texts: list[arcade.Text] = []
        for _ in range(VISIBLE_COUNT + 1):
            self._item_texts.append(arcade.Text(
                "", 0, 0, BUTTON_TEXT, FONT_SIZE_MEDIUM,
                anchor_x="center", anchor_y="center",
            ))
            self._item_detail_texts.append(arcade.Text(
                "", 0, 0, (180, 180, 220), FONT_SIZE_TINY,
                anchor_x="center", anchor_y="center",
            ))
            self._item_progress_texts.append(arcade.Text(
                "", 0, 0, (100, 200, 100), FONT_SIZE_TINY,
                anchor_x="right", anchor_y="center",
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
            # Count overall progress
            total_themes = len(self.themes)
            done_themes = sum(
                1 for i, c in enumerate(self.themes)
                if self.progress.is_theme_completed(self.theme_files[i], len(c.hands))
            )
            self.subtitle_text.text = f"{total_themes} themes ({done_themes} completed)  |  Scroll with mouse wheel or Up/Down"
            self.subtitle_text.draw()

            visible_end = min(self._scroll_offset + VISIBLE_COUNT, total_themes)
            cx = SCREEN_WIDTH // 2
            w = 700

            for vi, idx in enumerate(range(self._scroll_offset, visible_end)):
                coll = self.themes[idx]
                fname = self.theme_files[idx]
                y = VISIBLE_TOP - vi * ITEM_TOTAL - ITEM_HEIGHT // 2

                total_hands = len(coll.hands)
                done_hands = self.progress.completed_count(fname)
                all_done = done_hands >= total_hands

                hovered = (abs(self._mouse_x - cx) < w // 2
                           and abs(self._mouse_y - y) < ITEM_HEIGHT // 2)

                if all_done:
                    bg = (40, 100, 40) if hovered else THEME_DONE_BG
                    border = THEME_DONE_BORDER
                else:
                    bg = BUTTON_HOVER if hovered else THEME_PARTIAL_BG
                    border = THEME_PARTIAL_BORDER

                rect = arcade.XYWH(cx, y, w, ITEM_HEIGHT)
                arcade.draw_rect_filled(rect, bg)
                arcade.draw_rect_outline(rect, border, 1)

                # Theme name
                txt = self._item_texts[vi]
                txt.text = coll.theme
                txt.x = cx
                txt.y = y + 8
                txt.color = (180, 255, 180) if all_done else BUTTON_TEXT
                txt.draw()

                # Detail line
                dtxt = self._item_detail_texts[vi]
                diff_label = {1: "Beginner", 2: "Beginner-Int", 3: "Intermediate", 4: "Int-Advanced", 5: "Advanced"}.get(coll.difficulty, str(coll.difficulty))
                dtxt.text = f"{total_hands} hands  |  {diff_label}"
                dtxt.x = cx - 60
                dtxt.y = y - 12
                dtxt.draw()

                # Progress indicator
                ptxt = self._item_progress_texts[vi]
                if all_done:
                    ptxt.text = "ALL DONE"
                    ptxt.color = (100, 255, 100)
                elif done_hands > 0:
                    ptxt.text = f"{done_hands}/{total_hands}"
                    ptxt.color = (200, 200, 100)
                else:
                    ptxt.text = ""
                ptxt.x = cx + w // 2 - 15
                ptxt.y = y
                ptxt.draw()

            # Scrollbar
            if total_themes > VISIBLE_COUNT:
                sb_x = cx + w // 2 + 20
                sb_top = VISIBLE_TOP
                sb_bottom = VISIBLE_TOP - VISIBLE_COUNT * ITEM_TOTAL
                sb_height = sb_top - sb_bottom
                track_rect = arcade.XYWH(sb_x, (sb_top + sb_bottom) // 2, 8, sb_height)
                arcade.draw_rect_filled(track_rect, (60, 60, 60))
                arcade.draw_rect_outline(track_rect, (100, 100, 100), 1)
                thumb_ratio = VISIBLE_COUNT / total_themes
                thumb_h = max(30, sb_height * thumb_ratio)
                scroll_range = sb_height - thumb_h
                thumb_off = (self._scroll_offset / self._max_scroll * scroll_range) if self._max_scroll > 0 else 0
                thumb_cy = sb_top - thumb_h / 2 - thumb_off
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
        if abs(x - 100) < 70 and abs(y - 40) < 20:
            from .menu_view import MenuView
            self.window.show_view(MenuView())
            return

        cx = SCREEN_WIDTH // 2
        w = 700
        visible_end = min(self._scroll_offset + VISIBLE_COUNT, len(self.themes))

        for vi, idx in enumerate(range(self._scroll_offset, visible_end)):
            y_pos = VISIBLE_TOP - vi * ITEM_TOTAL - ITEM_HEIGHT // 2
            if abs(x - cx) < w // 2 and abs(y - y_pos) < ITEM_HEIGHT // 2:
                if self.mode == "play":
                    from .hand_select_view import HandSelectView
                    self.window.show_view(HandSelectView(self.theme_files[idx], self.progress))
                return
