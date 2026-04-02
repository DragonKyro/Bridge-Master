"""Unit tests for PBN parser and ThemeCollection."""

import json
import tempfile
from pathlib import Path
import pytest
from bridge.models.deal import Deal, Direction
from bridge.models.game import Contract
from bridge.formats.pbn import PBNParser
from bridge.formats.collection import ThemeCollection, HandEntry


SAMPLE_PBN_DEAL = "S:A52.KQJ.T983.A65 KT3.T87.KJ4.QJ98 QJ4.A9654.A72.K3 9876.32.Q65.T742"


class TestPBNParser:
    def test_parse_deal_string(self):
        deal = Deal.from_pbn_deal(SAMPLE_PBN_DEAL)
        assert deal.is_complete()

    def test_tags_to_deal(self):
        tags = {
            "Deal": SAMPLE_PBN_DEAL,
            "Dealer": "S",
            "Vulnerable": "NS",
        }
        deal = PBNParser.tags_to_deal(tags)
        assert deal.is_complete()
        assert deal.vulnerability == "NS"

    def test_deal_to_pbn_string(self):
        deal = Deal.from_pbn_deal(SAMPLE_PBN_DEAL)
        pbn_text = PBNParser.deal_to_pbn_string(deal)
        assert '[Deal "' in pbn_text
        assert '[Dealer "' in pbn_text

    def test_roundtrip(self):
        deal = Deal.from_pbn_deal(SAMPLE_PBN_DEAL)
        contract = Contract.from_str("4H", declarer=Direction.SOUTH)
        pbn_text = PBNParser.deal_to_pbn_string(deal, contract)
        tags = PBNParser.parse_string(pbn_text)
        assert len(tags) == 1
        reconstructed = PBNParser.tags_to_deal(tags[0])
        assert reconstructed.is_complete()

    def test_write_and_read_file(self, tmp_path):
        deal = Deal.from_pbn_deal(SAMPLE_PBN_DEAL)
        contract = Contract.from_str("3NT")
        path = tmp_path / "test.pbn"
        PBNParser.write_file(path, [(deal, contract)])
        deals = PBNParser.load_deals(path)
        assert len(deals) == 1
        assert deals[0].is_complete()


class TestHandEntry:
    def test_to_deal(self):
        entry = HandEntry(
            title="Test",
            deal_pbn=SAMPLE_PBN_DEAL,
            contract="4H",
            declarer="S",
        )
        deal = entry.to_deal()
        assert deal.is_complete()

    def test_to_contract(self):
        entry = HandEntry(
            title="Test",
            deal_pbn=SAMPLE_PBN_DEAL,
            contract="3NT",
            declarer="S",
        )
        c = entry.to_contract()
        assert c.level == 3
        assert c.strain is None


class TestThemeCollection:
    def test_save_and_load(self, tmp_path):
        coll = ThemeCollection(
            theme="Test Theme",
            description="Testing",
            difficulty=2,
        )
        entry = HandEntry(
            title="Hand 1",
            deal_pbn=SAMPLE_PBN_DEAL,
            contract="4H",
            declarer="S",
            notes="Test notes",
        )
        coll.add_hand(entry)
        assert len(coll.hands) == 1

        path = tmp_path / "test_theme.json"
        coll.save(path)

        loaded = ThemeCollection.load(path)
        assert loaded.theme == "Test Theme"
        assert loaded.difficulty == 2
        assert len(loaded.hands) == 1
        assert loaded.hands[0].title == "Hand 1"
        assert loaded.hands[0].notes == "Test notes"

    def test_list_themes(self, tmp_path):
        coll = ThemeCollection(theme="Alpha")
        coll.save(tmp_path / "alpha.json")
        coll2 = ThemeCollection(theme="Beta")
        coll2.save(tmp_path / "beta.json")

        themes = ThemeCollection.list_themes(tmp_path)
        assert "alpha" in themes
        assert "beta" in themes
