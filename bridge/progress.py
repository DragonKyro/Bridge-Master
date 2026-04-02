"""Progress tracking — saves which hands and themes the user has completed.

Stores progress in a JSON file at data/progress.json:
{
    "completed": {
        "theme_filename": [0, 2, 5]   // list of completed hand indices
    }
}
"""

from __future__ import annotations
import json
from pathlib import Path


PROGRESS_FILE = Path("data/progress.json")


class ProgressTracker:
    """Tracks which hands have been completed per theme."""

    def __init__(self, path: Path = PROGRESS_FILE):
        self._path = path
        self._data: dict[str, list[int]] = {}
        self._load()

    def _load(self):
        if self._path.exists():
            try:
                raw = json.loads(self._path.read_text(encoding="utf-8"))
                self._data = raw.get("completed", {})
            except Exception:
                self._data = {}
        else:
            self._data = {}

    def save(self):
        self._path.parent.mkdir(parents=True, exist_ok=True)
        payload = {"completed": self._data}
        self._path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")

    def mark_completed(self, theme_file: str, hand_index: int):
        if theme_file not in self._data:
            self._data[theme_file] = []
        if hand_index not in self._data[theme_file]:
            self._data[theme_file].append(hand_index)
            self._data[theme_file].sort()
            self.save()

    def is_completed(self, theme_file: str, hand_index: int) -> bool:
        return hand_index in self._data.get(theme_file, [])

    def completed_count(self, theme_file: str) -> int:
        return len(self._data.get(theme_file, []))

    def is_theme_completed(self, theme_file: str, total_hands: int) -> bool:
        return self.completed_count(theme_file) >= total_hands

    def first_incomplete(self, theme_file: str, total_hands: int) -> int | None:
        """Return the index of the first incomplete hand, or None if all done."""
        completed = set(self._data.get(theme_file, []))
        for i in range(total_hands):
            if i not in completed:
                return i
        return None

    def reset_theme(self, theme_file: str):
        self._data.pop(theme_file, None)
        self.save()

    def reset_all(self):
        self._data.clear()
        self.save()
