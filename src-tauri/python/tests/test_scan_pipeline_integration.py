import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

import scripts.pipeline.scan_pipeline as scan_pipeline


class ScanPipelineIntegrationTests(unittest.TestCase):
    def test_probe_pipeline_forwards_base_url_to_executor(self) -> None:
        javascript = """
        fetch('/api/orders', {
            method: 'GET'
        })
        """

        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            target = root / "fixture.js"
            output = root / "report.json"
            target.write_text(javascript, encoding="utf-8")

            captured = {}

            class FakeExecutor:
                def __init__(self):
                    pass

                def probe_all(self, endpoints, base_url=None):
                    captured["endpoints"] = endpoints
                    captured["base_url"] = base_url
                    return []

            argv = [
                "scan_pipeline.py",
                str(target),
                "--probe",
                "--base-url",
                "http://fixture.invalid/api/v1",
                "-o",
                str(output),
            ]

            with patch.object(
                scan_pipeline,
                "AdaptiveSandboxExecutor",
                FakeExecutor,
            ):
                with patch.object(
                    scan_pipeline,
                    "RiskEngine",
                ) as risk_engine:
                    risk_engine.evaluate_all.return_value = []

                    with patch.object(
                        scan_pipeline,
                        "JSEndpointExtractor",
                    ) as extractor_cls:
                        extractor_cls.return_value.parse_file.return_value = []

                        with patch(
                            "sys.argv",
                            argv,
                        ):
                            scan_pipeline.main()

            self.assertEqual(
                captured["base_url"],
                "http://fixture.invalid/api/v1",
            )
            self.assertEqual(captured["endpoints"], [])


if __name__ == "__main__":
    unittest.main()
