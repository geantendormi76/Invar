from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from scripts.data.asset.ingest_httpx import ingest_httpx
from scripts.data.asset.ingest_katana import build_katana_input


class TestIngestHttpx(unittest.TestCase):
    def test_same_host_from_multiple_httpx_urls_creates_one_asset(self):
        input_content = """{"url":"https://api.ikuai8.com","status-code":200,"title":"API","webserver":"nginx"}
{"url":"http://api.ikuai8.com","status-code":301,"title":"Redirect"}
"""

        with tempfile.TemporaryDirectory() as temp_dir:
            input_path = Path(temp_dir) / "httpx.jsonl"
            output_path = Path(temp_dir) / "hosts.jsonl"

            input_path.write_text(input_content, encoding="utf-8")

            ingest_httpx(
                input_path=input_path,
                output_path=output_path,
                target="ikuai8.com",
            )

            records = [
                json.loads(line)
                for line in output_path.read_text(
                    encoding="utf-8"
                ).splitlines()
                if line.strip()
            ]

        self.assertEqual(len(records), 1)
        self.assertEqual(records[0]["asset_type"], "host")
        self.assertEqual(records[0]["hostname"], "api.ikuai8.com")
        self.assertEqual(records[0]["target"], "ikuai8.com")

    def test_external_domain_is_rejected(self):
        input_content = """{"url":"https://api.ikuai8.com","status-code":200}
{"url":"https://example.com","status-code":200}
"""

        with tempfile.TemporaryDirectory() as temp_dir:
            input_path = Path(temp_dir) / "httpx.jsonl"
            output_path = Path(temp_dir) / "hosts.jsonl"

            input_path.write_text(input_content, encoding="utf-8")

            ingest_httpx(
                input_path=input_path,
                output_path=output_path,
                target="ikuai8.com",
            )

            records = [
                json.loads(line)
                for line in output_path.read_text(
                    encoding="utf-8"
                ).splitlines()
                if line.strip()
            ]

        self.assertEqual(len(records), 1)
        self.assertEqual(records[0]["hostname"], "api.ikuai8.com")

    def test_host_asset_v1_contract(self):
        input_content = (
            '{"url":"https://api.ikuai8.com",'
            '"status_code":200,'
            '"title":"API",'
            '"webserver":"nginx",'
            '"tech":["Nginx"],'
            '"host_ip":"1.2.3.4",'
            '"content_length":1234}'
        )

        with tempfile.TemporaryDirectory() as temp_dir:
            input_path = Path(temp_dir) / "httpx.jsonl"
            output_path = Path(temp_dir) / "hosts.jsonl"

            input_path.write_text(
                input_content + "\n",
                encoding="utf-8",
            )

            ingest_httpx(
                input_path=input_path,
                output_path=output_path,
                target="ikuai8.com",
            )

            records = [
                json.loads(line)
                for line in output_path.read_text(
                    encoding="utf-8"
                ).splitlines()
                if line.strip()
            ]

        self.assertEqual(len(records), 1)

        self.assertEqual(
            records[0],
            {
                "asset_id": "host:api.ikuai8.com",
                "asset_type": "host",
                "hostname": "api.ikuai8.com",
                "target": "ikuai8.com",
            },
        )

    def test_host_asset_v1_does_not_copy_raw_httpx_fields(self):
        input_content = (
            '{"url":"https://api.ikuai8.com",'
            '"status_code":200,'
            '"title":"API",'
            '"webserver":"nginx",'
            '"tech":["Nginx"],'
            '"host_ip":"1.2.3.4",'
            '"content_length":1234,'
            '"time":"123ms"}'
        )

        with tempfile.TemporaryDirectory() as temp_dir:
            input_path = Path(temp_dir) / "httpx.jsonl"
            output_path = Path(temp_dir) / "hosts.jsonl"

            input_path.write_text(
                input_content + "\n",
                encoding="utf-8",
            )

            ingest_httpx(
                input_path=input_path,
                output_path=output_path,
                target="ikuai8.com",
            )

            records = [
                json.loads(line)
                for line in output_path.read_text(
                    encoding="utf-8"
                ).splitlines()
                if line.strip()
            ]

        self.assertEqual(len(records), 1)

        self.assertEqual(
            set(records[0].keys()),
            {
                "asset_id",
                "asset_type",
                "hostname",
                "target",
            },
        )

    def test_build_katana_input_from_live_hosts(self):
        input_content = """{"asset_id":"host:api.ikuai8.com","asset_type":"host","hostname":"api.ikuai8.com","target":"ikuai8.com"}
{"asset_id":"host:www.ikuai8.com","asset_type":"host","hostname":"www.ikuai8.com","target":"ikuai8.com"}
"""

        with tempfile.TemporaryDirectory() as temp_dir:
            input_path = Path(temp_dir) / "live_hosts.jsonl"
            output_path = Path(temp_dir) / "katana_urls.txt"

            input_path.write_text(
                input_content,
                encoding="utf-8",
            )

            build_katana_input(
                input_path=input_path,
                output_path=output_path,
            )

            urls = [
                line
                for line in output_path.read_text(
                    encoding="utf-8"
                ).splitlines()
                if line.strip()
            ]

        self.assertEqual(
            urls,
            [
                "https://api.ikuai8.com",
                "https://www.ikuai8.com",
            ],
        )


if __name__ == "__main__":
    unittest.main()
