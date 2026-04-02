"""Unit tests for validation utilities."""

import json
from pathlib import Path
import pytest
from bridge.utils.validate import validate_deal_pbn, validate_collection


VALID_PBN = "S:A52.KQJ.T983.A65 KT3.T87.KJ4.QJ98 QJ4.A9654.A72.K3 9876.32.Q65.T742"


class TestValidateDealPBN:
    def test_valid_deal(self):
        issues = validate_deal_pbn(VALID_PBN, "test")
        assert issues == []

    def test_duplicate_card(self):
        # Replace a card to create a duplicate
        bad = "S:A52.KQJ.T983.A65 KT3.T87.KJ4.QJ98 QJ4.A9654.A72.A3 9876.32.Q65.T742"
        issues = validate_deal_pbn(bad, "dup")
        assert len(issues) > 0
        assert any("Duplicate" in i or "missing" in i.lower() for i in issues)

    def test_wrong_card_count(self):
        # Remove a card from South
        bad = "S:A52.KQJ.T983.A6 KT3.T87.KJ4.QJ98 QJ4.A9654.A72.K3 9876.32.Q65.T742"
        issues = validate_deal_pbn(bad, "short")
        assert any("12 cards" in i or "has 12" in i for i in issues)

    def test_unparseable(self):
        issues = validate_deal_pbn("garbage", "bad")
        assert len(issues) > 0
        assert any("Parse error" in i for i in issues)


class TestValidateCollection:
    def test_valid_collection(self, tmp_path):
        data = {
            "theme": "Test",
            "hands": [{
                "title": "Hand 1",
                "deal_pbn": VALID_PBN,
                "contract": "3NT",
            }]
        }
        path = tmp_path / "test.json"
        path.write_text(json.dumps(data))
        total, valid, issues = validate_collection(path)
        assert total == 1
        assert valid == 1
        assert issues == []

    def test_invalid_json(self, tmp_path):
        path = tmp_path / "bad.json"
        path.write_text("not json")
        total, valid, issues = validate_collection(path)
        assert total == 0
        assert len(issues) > 0

    def test_mixed_validity(self, tmp_path):
        data = {
            "theme": "Test",
            "hands": [
                {"title": "Good", "deal_pbn": VALID_PBN, "contract": "3NT"},
                {"title": "Bad", "deal_pbn": "garbage", "contract": "3NT"},
            ]
        }
        path = tmp_path / "mixed.json"
        path.write_text(json.dumps(data))
        total, valid, issues = validate_collection(path)
        assert total == 2
        assert valid == 1
        assert len(issues) > 0


class TestAllThemeFiles:
    """Integration test: validate every theme file in data/themes/."""

    def test_all_themes_valid(self):
        themes_dir = Path("data/themes")
        if not themes_dir.exists():
            pytest.skip("data/themes not found")
        for path in sorted(themes_dir.glob("*.json")):
            total, valid, issues = validate_collection(path)
            assert valid == total, f"{path.name}: {total - valid} invalid hands: {issues[:3]}"
