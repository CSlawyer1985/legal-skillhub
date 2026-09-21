import unittest
from pathlib import Path
import sys

SCRIPT_DIR = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPT_DIR))
import migrate_state_v2 as m


class StateMigrationTests(unittest.TestCase):
    def test_migration_preserves_order_and_unknown_fields(self):
        v1 = {
            "checkpoint": "2026-09-01 08:00:00",
            "checkpoint2": "2026-09-01 09:00:00",
            "processed_media_ids": ["b", "a", "b"],
            "note": "legacy",
            "future_key": {"x": 1},
        }
        v2 = m.migrate(v1)
        self.assertEqual(v2["legacy"]["processed_media_ids"], ["b", "a"])
        self.assertEqual(v2["legacy"]["unknown_fields"], {"future_key": {"x": 1}})
        self.assertTrue(m.validate_v2(v2))

    def test_validation_fails_open_write_flags(self):
        v2 = m.migrate({})
        v2["shadow"]["write_main_ledger"] = True
        self.assertFalse(m.validate_v2(v2))

    def test_validation_rejects_incomplete_v2(self):
        self.assertFalse(m.validate_v2({"schema_version": 2}))


if __name__ == "__main__":
    unittest.main()
