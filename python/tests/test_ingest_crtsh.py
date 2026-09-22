import unittest
from pathlib import Path
import sys

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.data.asset.ingest_crtsh import (
    belongs_to_target,
    clean_subdomain,
    extract_subdomains_from_crtsh_data,
)

class TestIngestCrtsh(unittest.TestCase):
    def test_belongs_to_target(self):
        self.assertTrue(belongs_to_target("api.ikuai8.com", "ikuai8.com"))
        self.assertTrue(belongs_to_target("dev.staging.ikuai8.com", "ikuai8.com"))
        self.assertTrue(belongs_to_target("ikuai8.com", "ikuai8.com"))
        self.assertFalse(belongs_to_target("notikuai8.com", "ikuai8.com"))
        self.assertFalse(belongs_to_target("example.com", "ikuai8.com"))

    def test_clean_subdomain_wildcard_and_case(self):
        self.assertEqual(clean_subdomain("*.API.ikuai8.com", "ikuai8.com"), "api.ikuai8.com")
        self.assertEqual(clean_subdomain("admin.ikuai8.com.", "ikuai8.com"), "admin.ikuai8.com")
        self.assertIsNone(clean_subdomain("attacker.com", "ikuai8.com"))
        self.assertIsNone(clean_subdomain("admin@ikuai8.com", "ikuai8.com"))

    def test_extract_subdomains_multi_san(self):
        mock_records = [
            {
                "common_name": "www.ikuai8.com",
                "name_value": "www.ikuai8.com\n*.dev.ikuai8.com\napi.ikuai8.com",
            },
            {
                "common_name": "staging.ikuai8.com",
                "name_value": "staging.ikuai8.com\nforeign.example.com",
            },
            {
                "common_name": "invalid_entry",
                "name_value": None,
            },
        ]
        results = extract_subdomains_from_crtsh_data(mock_records, "ikuai8.com")
        self.assertEqual(
            results,
            [
                "api.ikuai8.com",
                "dev.ikuai8.com",
                "staging.ikuai8.com",
                "www.ikuai8.com",
            ],
        )

if __name__ == "__main__":
    unittest.main()
