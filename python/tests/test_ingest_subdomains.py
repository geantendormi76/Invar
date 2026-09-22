import json
import sys
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from scripts.data.asset.ingest_subdomains import ingest_subdomains


class TestIngestSubdomains(unittest.TestCase):
    def test_duplicate_subdomains_are_deduplicated(self):
        input_content = """api.ikuai8.com
kiam.corp.ikuai8.com
kiam.corp.ikuai8.com
www.ikuai8.com
"""

        observed_at = datetime(
            2026,
            9,
            16,
            10,
            0,
            0,
            tzinfo=timezone.utc,
        )

        with tempfile.TemporaryDirectory() as temp_dir:
            input_path = Path(temp_dir) / "subdomains.txt"
            output_path = Path(temp_dir) / "subdomains.jsonl"
            input_path.write_text(input_content, encoding="utf-8")

            ingest_subdomains(
                input_path=input_path,
                output_path=output_path,
                target="ikuai8.com",
                observed_at=observed_at,
            )

            records = [
                json.loads(line)
                for line in output_path.read_text(
                    encoding="utf-8"
                ).splitlines()
                if line.strip()
            ]

        self.assertEqual(len(records), 3)

        hostnames = {record["hostname"] for record in records}

        self.assertEqual(
            hostnames,
            {
                "api.ikuai8.com",
                "kiam.corp.ikuai8.com",
                "www.ikuai8.com",
            },
        )

        for record in records:
            self.assertEqual(record["asset_type"], "subdomain")
            self.assertEqual(record["target"], "ikuai8.com")
            self.assertEqual(
                record["asset_id"],
                f"subdomain:{record['hostname']}",
            )

    def test_external_domain_is_rejected(self):
        input_content = """api.ikuai8.com
example.com
www.ikuai8.com
"""

        observed_at = datetime(
            2026,
            9,
            16,
            10,
            0,
            0,
            tzinfo=timezone.utc,
        )

        with tempfile.TemporaryDirectory() as temp_dir:
            input_path = Path(temp_dir) / "subdomains.txt"
            output_path = Path(temp_dir) / "subdomains.jsonl"
            input_path.write_text(input_content, encoding="utf-8")

            ingest_subdomains(
                input_path=input_path,
                output_path=output_path,
                target="ikuai8.com",
                observed_at=observed_at,
            )

            records = [
                json.loads(line)
                for line in output_path.read_text(
                    encoding="utf-8"
                ).splitlines()
                if line.strip()
            ]

        hostnames = {record["hostname"] for record in records}

        self.assertEqual(
            hostnames,
            {
                "api.ikuai8.com",
                "www.ikuai8.com",
            },
        )

    def test_existing_asset_is_updated_instead_of_duplicated(self):
        first_time = datetime(
            2026,
            9,
            16,
            10,
            0,
            0,
            tzinfo=timezone.utc,
        )
        second_time = datetime(
            2026,
            9,
            16,
            11,
            0,
            0,
            tzinfo=timezone.utc,
        )

        input_content = """api.ikuai8.com
api.ikuai8.com
"""

        with tempfile.TemporaryDirectory() as temp_dir:
            input_path = Path(temp_dir) / "subdomains.txt"
            output_path = Path(temp_dir) / "subdomains.jsonl"

            input_path.write_text(input_content, encoding="utf-8")

            ingest_subdomains(
                input_path=input_path,
                output_path=output_path,
                target="ikuai8.com",
                observed_at=first_time,
            )

            ingest_subdomains(
                input_path=input_path,
                output_path=output_path,
                target="ikuai8.com",
                observed_at=second_time,
            )

            records = [
                json.loads(line)
                for line in output_path.read_text(
                    encoding="utf-8"
                ).splitlines()
                if line.strip()
            ]

        self.assertEqual(len(records), 1)

        record = records[0]

        self.assertEqual(
            record["asset_id"],
            "subdomain:api.ikuai8.com",
        )
        self.assertEqual(
            record["first_seen"],
            first_time.isoformat(),
        )
        self.assertEqual(
            record["last_seen"],
            second_time.isoformat(),
        )
        self.assertEqual(record["status"], "active")

    def test_new_assets_are_recorded_once_in_changes(self):
        first_time = datetime(
            2026,
            9,
            16,
            10,
            0,
            0,
            tzinfo=timezone.utc,
        )

        input_content = """api.ikuai8.com
www.ikuai8.com
"""

        with tempfile.TemporaryDirectory() as temp_dir:
            input_path = Path(temp_dir) / "subdomains.txt"
            output_path = Path(temp_dir) / "subdomains.jsonl"
            changes_path = Path(temp_dir) / "changes.jsonl"

            input_path.write_text(input_content, encoding="utf-8")

            ingest_subdomains(
                input_path=input_path,
                output_path=output_path,
                changes_path=changes_path,
                target="ikuai8.com",
                observed_at=first_time,
            )

            ingest_subdomains(
                input_path=input_path,
                output_path=output_path,
                changes_path=changes_path,
                target="ikuai8.com",
                observed_at=first_time,
            )

            changes = [
                json.loads(line)
                for line in changes_path.read_text(
                    encoding="utf-8"
                ).splitlines()
                if line.strip()
            ]

        self.assertEqual(len(changes), 2)

        change_by_asset_id = {
            change["asset_id"]: change
            for change in changes
        }

        self.assertEqual(
            set(change_by_asset_id),
            {
                "subdomain:api.ikuai8.com",
                "subdomain:www.ikuai8.com",
            },
        )

        for change in changes:
            self.assertEqual(change["change_type"], "created")
            self.assertEqual(change["target"], "ikuai8.com")
            self.assertEqual(
                change["observed_at"],
                first_time.isoformat(),
            )

    def test_scan_is_recorded_in_manifest(self):
        observed_at = datetime(
            2026,
            9,
            16,
            12,
            0,
            0,
            tzinfo=timezone.utc,
        )

        input_content = """api.ikuai8.com
www.ikuai8.com
"""

        with tempfile.TemporaryDirectory() as temp_dir:
            input_path = Path(temp_dir) / "subdomains.txt"
            output_path = Path(temp_dir) / "subdomains.jsonl"
            changes_path = Path(temp_dir) / "changes.jsonl"
            manifest_path = Path(temp_dir) / "manifest.jsonl"

            input_path.write_text(input_content, encoding="utf-8")

            ingest_subdomains(
                input_path=input_path,
                output_path=output_path,
                changes_path=changes_path,
                manifest_path=manifest_path,
                target="ikuai8.com",
                observed_at=observed_at,
            )

            manifest_records = [
                json.loads(line)
                for line in manifest_path.read_text(
                    encoding="utf-8"
                ).splitlines()
                if line.strip()
            ]

        self.assertEqual(len(manifest_records), 1)

        manifest = manifest_records[0]

        self.assertEqual(manifest["target"], "ikuai8.com")
        self.assertEqual(manifest["source"], "subfinder")
        self.assertEqual(manifest["asset_type"], "subdomain")
        self.assertEqual(
            manifest["observed_at"],
            observed_at.isoformat(),
        )
        self.assertEqual(manifest["status"], "completed")

    def test_completed_scan_marks_missing_assets_inactive(self):
        first_time = datetime(
            2026,
            9,
            16,
            10,
            0,
            0,
            tzinfo=timezone.utc,
        )

        second_time = datetime(
            2026,
            9,
            16,
            11,
            0,
            0,
            tzinfo=timezone.utc,
        )

        first_input = """api.ikuai8.com
www.ikuai8.com
"""

        second_input = """api.ikuai8.com
"""

        with tempfile.TemporaryDirectory() as temp_dir:
            first_input_path = Path(temp_dir) / "first.txt"
            second_input_path = Path(temp_dir) / "second.txt"
            output_path = Path(temp_dir) / "subdomains.jsonl"
            changes_path = Path(temp_dir) / "changes.jsonl"
            manifest_path = Path(temp_dir) / "manifest.jsonl"

            first_input_path.write_text(
                first_input,
                encoding="utf-8",
            )
            second_input_path.write_text(
                second_input,
                encoding="utf-8",
            )

            ingest_subdomains(
                input_path=first_input_path,
                output_path=output_path,
                changes_path=changes_path,
                manifest_path=manifest_path,
                target="ikuai8.com",
                observed_at=first_time,
            )

            ingest_subdomains(
                input_path=second_input_path,
                output_path=output_path,
                changes_path=changes_path,
                manifest_path=manifest_path,
                target="ikuai8.com",
                observed_at=second_time,
            )

            records = {
                json.loads(line)["asset_id"]: json.loads(line)
                for line in output_path.read_text(
                    encoding="utf-8"
                ).splitlines()
                if line.strip()
            }

        self.assertEqual(
            records["subdomain:api.ikuai8.com"]["status"],
            "active",
        )

        self.assertEqual(
            records["subdomain:www.ikuai8.com"]["status"],
            "inactive",
        )

        self.assertEqual(
            records["subdomain:www.ikuai8.com"]["first_seen"],
            first_time.isoformat(),
        )

        self.assertEqual(
            records["subdomain:www.ikuai8.com"]["last_seen"],
            first_time.isoformat(),
        )

    def test_status_change_to_inactive_is_recorded_in_changes(self):
        first_time = datetime(
            2026,
            9,
            16,
            10,
            0,
            0,
            tzinfo=timezone.utc,
        )

        second_time = datetime(
            2026,
            9,
            16,
            11,
            0,
            0,
            tzinfo=timezone.utc,
        )

        first_input = """api.ikuai8.com
www.ikuai8.com
"""

        second_input = """api.ikuai8.com
"""

        with tempfile.TemporaryDirectory() as temp_dir:
            first_input_path = Path(temp_dir) / "first.txt"
            second_input_path = Path(temp_dir) / "second.txt"
            output_path = Path(temp_dir) / "subdomains.jsonl"
            changes_path = Path(temp_dir) / "changes.jsonl"
            manifest_path = Path(temp_dir) / "manifest.jsonl"

            first_input_path.write_text(
                first_input,
                encoding="utf-8",
            )
            second_input_path.write_text(
                second_input,
                encoding="utf-8",
            )

            ingest_subdomains(
                input_path=first_input_path,
                output_path=output_path,
                changes_path=changes_path,
                manifest_path=manifest_path,
                target="ikuai8.com",
                observed_at=first_time,
            )

            ingest_subdomains(
                input_path=second_input_path,
                output_path=output_path,
                changes_path=changes_path,
                manifest_path=manifest_path,
                target="ikuai8.com",
                observed_at=second_time,
            )

            changes = [
                json.loads(line)
                for line in changes_path.read_text(
                    encoding="utf-8"
                ).splitlines()
                if line.strip()
            ]

        inactive_changes = [
            change
            for change in changes
            if change["asset_id"]
            == "subdomain:www.ikuai8.com"
            and change["change_type"] == "status_changed"
        ]

        self.assertEqual(len(inactive_changes), 1)

        change = inactive_changes[0]

        self.assertEqual(change["old_status"], "active")
        self.assertEqual(change["new_status"], "inactive")
        self.assertEqual(
            change["observed_at"],
            second_time.isoformat(),
        )

    def test_repeated_inactive_state_does_not_create_duplicate_change(self):
        first_time = datetime(
            2026,
            9,
            16,
            10,
            0,
            0,
            tzinfo=timezone.utc,
        )

        second_time = datetime(
            2026,
            9,
            16,
            11,
            0,
            0,
            tzinfo=timezone.utc,
        )

        third_time = datetime(
            2026,
            9,
            16,
            12,
            0,
            0,
            tzinfo=timezone.utc,
        )

        first_input = """api.ikuai8.com
www.ikuai8.com
"""

        missing_input = """api.ikuai8.com
"""

        with tempfile.TemporaryDirectory() as temp_dir:
            first_input_path = Path(temp_dir) / "first.txt"
            second_input_path = Path(temp_dir) / "second.txt"
            third_input_path = Path(temp_dir) / "third.txt"

            output_path = Path(temp_dir) / "subdomains.jsonl"
            changes_path = Path(temp_dir) / "changes.jsonl"
            manifest_path = Path(temp_dir) / "manifest.jsonl"

            first_input_path.write_text(
                first_input,
                encoding="utf-8",
            )

            second_input_path.write_text(
                missing_input,
                encoding="utf-8",
            )

            third_input_path.write_text(
                missing_input,
                encoding="utf-8",
            )

            ingest_subdomains(
                input_path=first_input_path,
                output_path=output_path,
                changes_path=changes_path,
                manifest_path=manifest_path,
                target="ikuai8.com",
                observed_at=first_time,
            )

            ingest_subdomains(
                input_path=second_input_path,
                output_path=output_path,
                changes_path=changes_path,
                manifest_path=manifest_path,
                target="ikuai8.com",
                observed_at=second_time,
            )

            ingest_subdomains(
                input_path=third_input_path,
                output_path=output_path,
                changes_path=changes_path,
                manifest_path=manifest_path,
                target="ikuai8.com",
                observed_at=third_time,
            )

            changes = [
                json.loads(line)
                for line in changes_path.read_text(
                    encoding="utf-8"
                ).splitlines()
                if line.strip()
            ]

        inactive_changes = [
            change
            for change in changes
            if change["asset_id"]
            == "subdomain:www.ikuai8.com"
            and change["change_type"] == "status_changed"
        ]

        self.assertEqual(len(inactive_changes), 1)

        change = inactive_changes[0]

        self.assertEqual(change["old_status"], "active")
        self.assertEqual(change["new_status"], "inactive")
        self.assertEqual(
            change["observed_at"],
            second_time.isoformat(),
        )

if __name__ == "__main__":
    unittest.main()

