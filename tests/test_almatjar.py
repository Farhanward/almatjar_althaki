from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from almatjar_althaki.batch import evaluate
from almatjar_althaki.datasets import convert_bitext
from almatjar_althaki.store import default_catalog, handle_store_message, save_catalog


class AlMatjarTests(unittest.TestCase):
    def test_handle_order_message(self):
        result = handle_store_message("I want to buy whatsapp sales bot", default_catalog())
        self.assertEqual(result["action"], "CREATE_DRAFT_ORDER")
        self.assertIn("product", result["recommendation"])

    def test_convert_and_batch_fixture(self):
        with tempfile.TemporaryDirectory(dir="C:/Projects") as tmp:
            source = Path(tmp) / "bitext.jsonl"
            events = Path(tmp) / "events.jsonl"
            catalog = Path(tmp) / "catalog.json"
            source.write_text('{"instruction":"buy automation","intent":"place_order"}\n{"instruction":"refund please","intent":"refund"}\n', encoding="utf-8")
            save_catalog(catalog)
            info = convert_bitext(source, events)
            self.assertEqual(info["rows"], 2)
            summary = evaluate(events, catalog)
            self.assertEqual(summary["errors"], 0)


if __name__ == "__main__":
    unittest.main()

