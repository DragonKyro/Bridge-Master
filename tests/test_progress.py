"""Unit tests for ProgressTracker."""

import pytest
from pathlib import Path
from bridge.progress import ProgressTracker


class TestProgressTracker:
    def test_empty(self, tmp_path):
        p = ProgressTracker(tmp_path / "progress.json")
        assert p.completed_count("theme1") == 0
        assert not p.is_completed("theme1", 0)

    def test_mark_completed(self, tmp_path):
        p = ProgressTracker(tmp_path / "progress.json")
        p.mark_completed("theme1", 0)
        p.mark_completed("theme1", 2)
        assert p.is_completed("theme1", 0)
        assert not p.is_completed("theme1", 1)
        assert p.is_completed("theme1", 2)
        assert p.completed_count("theme1") == 2

    def test_idempotent(self, tmp_path):
        p = ProgressTracker(tmp_path / "progress.json")
        p.mark_completed("t", 0)
        p.mark_completed("t", 0)
        assert p.completed_count("t") == 1

    def test_persistence(self, tmp_path):
        path = tmp_path / "progress.json"
        p1 = ProgressTracker(path)
        p1.mark_completed("theme1", 3)
        p1.mark_completed("theme1", 7)

        p2 = ProgressTracker(path)
        assert p2.is_completed("theme1", 3)
        assert p2.is_completed("theme1", 7)
        assert p2.completed_count("theme1") == 2

    def test_is_theme_completed(self, tmp_path):
        p = ProgressTracker(tmp_path / "progress.json")
        for i in range(5):
            p.mark_completed("t", i)
        assert p.is_theme_completed("t", 5)
        assert not p.is_theme_completed("t", 6)

    def test_first_incomplete(self, tmp_path):
        p = ProgressTracker(tmp_path / "progress.json")
        p.mark_completed("t", 0)
        p.mark_completed("t", 1)
        p.mark_completed("t", 3)
        assert p.first_incomplete("t", 5) == 2

    def test_first_incomplete_all_done(self, tmp_path):
        p = ProgressTracker(tmp_path / "progress.json")
        for i in range(3):
            p.mark_completed("t", i)
        assert p.first_incomplete("t", 3) is None

    def test_reset_theme(self, tmp_path):
        p = ProgressTracker(tmp_path / "progress.json")
        p.mark_completed("t", 0)
        p.reset_theme("t")
        assert p.completed_count("t") == 0

    def test_reset_all(self, tmp_path):
        p = ProgressTracker(tmp_path / "progress.json")
        p.mark_completed("a", 0)
        p.mark_completed("b", 1)
        p.reset_all()
        assert p.completed_count("a") == 0
        assert p.completed_count("b") == 0

    def test_multiple_themes(self, tmp_path):
        p = ProgressTracker(tmp_path / "progress.json")
        p.mark_completed("theme_a", 0)
        p.mark_completed("theme_b", 5)
        assert p.is_completed("theme_a", 0)
        assert not p.is_completed("theme_a", 5)
        assert p.is_completed("theme_b", 5)
