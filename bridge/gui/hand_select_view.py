"""Hand selection view — pick which hand to play within a theme."""

from __future__ import annotations
from pathlib import Path
import arcade
from .constants import *
from ..formats.collection import ThemeCollection
from ..progress import ProgressTracker


DATA_DIR = Path("data/themes")

ITEM_H = 44
ITEM_GAP = 6
ITEM_TOTAL = ITEM_H + ITEM_GAP
LIST_TOP = SCREEN_HEIGHT - 110
LIST_BOTTOM = 80
VISIBLE = int((LIST_TOP - LIST_BOTTOM) / ITEM_TOTAL)

# Colors
COMPLETED_BG = (30, 80, 30)
INCOMPLETE_BG = BUTTON_COLOR
COMPLETED_BORDER = (80, 180, 80)
INCOMPLETE_BORDER = (120, 120, 180)


class HandSelectView(arcade.View):
    """Select a specific hand from a theme, with completion indicators."""

    def __init__(self, theme_file: str, progress: ProgressTracker):
        super().__init__()
        self.theme_file = theme_file
        self.progress = progress
        self.collection = ThemeCollection.load(DATA_DIR / f"{theme_file}.json")
        self._scroll = 0
        self._mouse_x = 0
        self._mouse_y = 0

        total = len(self.collection.hands)
        done = progress.completed_count(theme_file)

        self.title_text = arcade.Text(
            self.collection.theme,
            SCREEN_WIDTH // 2, SCREEN_HEIGHT - 35,
            TEXT_COLOR, FONT_SIZE_LARGE,
            anchor_x="center", anchor_y="center", bold=True,
        )
        self.subtitle_text = arcade.Text(
            f"{done}/{total} completed",
            SCREEN_WIDTH // 2, SCREEN_HEIGHT - 65,
            (180, 220, 180) if done == total else (180, 180, 180),
            FONT_SIZE_SMALL,
            anchor_x="center", anchor_y="center",
        )
        self.back_text = arcade.Text(
            "ESC: Back", 70, 40, BUTTON_TEXT, FONT_SIZE_SMALL,
            anchor_x="center", anchor_y="center",
        )
        self.resume_text = arcade.Text(
            "R: Resume (next incomplete)", SCREEN_WIDTH // 2, 40,
            (180, 220, 180), FONT_SIZE_SMALL,
            anchor_x="center", anchor_y="center",
        )

        # Reusable text objects for list items
        self._item_titles: list[arcade.Text] = []
        self._item_status: list[arcade.Text] = []
        for _ in range(VISIBLE + 1):
            self._item_titles.append(arcade.Text(
                "", 0, 0, BUTTON_TEXT, FONT_SIZE_SMALL,
            ))
            self._item_status.append(arcade.Text(
                "", 0, 0, (100, 200, 100), FONT_SIZE_TINY,
                anchor_x="right",
            ))

    @property
    def _max_scroll(self) -> int:
        return max(0, len(self.collection.hands) - VISIBLE)

    def on_show_view(self):
        arcade.set_background_color(BG_COLOR)

    def on_draw(self):
        self.clear()

        self.title_text.draw()

        # Update completion count
        total = len(self.collection.hands)
        done = self.progress.completed_count(self.theme_file)
        self.subtitle_text.text = f"{done}/{total} completed"
        self.subtitle_text.color = (100, 255, 100) if done == total else (180, 180, 180)
        self.subtitle_text.draw()

        # Hand list
        cx = SCREEN_WIDTH // 2
        w = 750
        vis_end = min(self._scroll + VISIBLE, total)

        for vi, idx in enumerate(range(self._scroll, vis_end)):
            entry = self.collection.hands[idx]
            y = LIST_TOP - vi * ITEM_TOTAL - ITEM_H // 2
            completed = self.progress.is_completed(self.theme_file, idx)

            hovered = (abs(self._mouse_x - cx) < w // 2
                       and abs(self._mouse_y - y) < ITEM_H // 2)

            if completed:
                bg = (40, 100, 40) if hovered else COMPLETED_BG
                border = COMPLETED_BORDER
            else:
                bg = BUTTON_HOVER if hovered else INCOMPLETE_BG
                border = INCOMPLETE_BORDER

            rect = arcade.XYWH(cx, y, w, ITEM_H)
            arcade.draw_rect_filled(rect, bg)
            arcade.draw_rect_outline(rect, border, 1)

            # Title
            txt = self._item_titles[vi]
            txt.text = f"{idx + 1}. {entry.title}"
            txt.x = cx - w // 2 + 15
            txt.y = y - 2
            txt.color = (180, 255, 180) if completed else BUTTON_TEXT
            txt.draw()

            # Status indicator
            st = self._item_status[vi]
            if completed:
                st.text = "DONE"
                st.color = (100, 200, 100)
            else:
                st.text = ""
            st.x = cx + w // 2 - 15
            st.y = y - 2
            st.draw()

        # Scrollbar
        if total > VISIBLE:
            sb_x = cx + w // 2 + 18
            sb_top = LIST_TOP
            sb_bottom = LIST_TOP - VISIBLE * ITEM_TOTAL
            sb_h = sb_top - sb_bottom
            track = arcade.XYWH(sb_x, (sb_top + sb_bottom) // 2, 8, sb_h)
            arcade.draw_rect_filled(track, (60, 60, 60))

            thumb_ratio = VISIBLE / total
            thumb_h = max(30, sb_h * thumb_ratio)
            scroll_range = sb_h - thumb_h
            thumb_off = (self._scroll / self._max_scroll * scroll_range) if self._max_scroll > 0 else 0
            thumb_cy = sb_top - thumb_h / 2 - thumb_off
            thumb = arcade.XYWH(sb_x, thumb_cy, 8, thumb_h)
            arcade.draw_rect_filled(thumb, (160, 160, 200))

        # Bottom bar
        bk_rect = arcade.XYWH(70, 40, 120, 32)
        arcade.draw_rect_filled(bk_rect, BUTTON_COLOR)
        self.back_text.draw()
        self.resume_text.draw()

    def on_mouse_motion(self, x, y, dx, dy):
        self._mouse_x = x
        self._mouse_y = y

    def on_mouse_scroll(self, x, y, scroll_x, scroll_y):
        if scroll_y > 0:
            self._scroll = max(0, self._scroll - 1)
        elif scroll_y < 0:
            self._scroll = min(self._max_scroll, self._scroll + 1)

    def on_key_press(self, key, modifiers):
        if key == arcade.key.ESCAPE:
            from .theme_browser_view import ThemeBrowserView
            self.window.show_view(ThemeBrowserView(mode="play"))
        elif key == arcade.key.UP:
            self._scroll = max(0, self._scroll - 1)
        elif key == arcade.key.DOWN:
            self._scroll = min(self._max_scroll, self._scroll + 1)
        elif key == arcade.key.PAGEUP:
            self._scroll = max(0, self._scroll - VISIBLE)
        elif key == arcade.key.PAGEDOWN:
            self._scroll = min(self._max_scroll, self._scroll + VISIBLE)
        elif key == arcade.key.R:
            self._resume_next_incomplete()

    def on_mouse_press(self, x, y, button, modifiers):
        # Back button
        if abs(x - 70) < 60 and abs(y - 40) < 16:
            from .theme_browser_view import ThemeBrowserView
            self.window.show_view(ThemeBrowserView(mode="play"))
            return

        # Hand items
        cx = SCREEN_WIDTH // 2
        w = 750
        vis_end = min(self._scroll + VISIBLE, len(self.collection.hands))
        for vi, idx in enumerate(range(self._scroll, vis_end)):
            y = LIST_TOP - vi * ITEM_TOTAL - ITEM_H // 2
            if abs(x - cx) < w // 2 and abs(y - self._mouse_y) < ITEM_H // 2:
                self._play_hand(idx)
                return

    def _play_hand(self, hand_index: int):
        from .play_view import PlayView
        view = PlayView(self.theme_file, progress=self.progress, start_index=hand_index)
        self.window.show_view(view)

    def _resume_next_incomplete(self):
        total = len(self.collection.hands)
        idx = self.progress.first_incomplete(self.theme_file, total)
        if idx is not None:
            self._play_hand(idx)
