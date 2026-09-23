import unittest
from unittest.mock import patch

from harness.config import InvarConfig
from harness.models import EndpointIR
from harness.sandbox_executor import AdaptiveSandboxExecutor


class SandboxBaseUrlCompatibilityTests(unittest.TestCase):
    def setUp(self) -> None:
        self.executor = AdaptiveSandboxExecutor(
            InvarConfig(
                target_api_base="http://default.invalid/api/v1",
                request_timeout=1,
                max_concurrent_workers=1,
                max_mutation_rounds=1,
            )
        )

    def test_probe_all_accepts_cli_base_url_override(self) -> None:
        endpoint = EndpointIR(
            method="GET",
            path="/api/orders",
            source_file="fixture.js",
            line=10,
            is_dynamic=False,
            extracted_params=[],
            tags=[],
            risk_score=1.0,
            confidence=0.95,
            call_signature="client.get('/api/orders')",
        )

        config = InvarConfig(
            target_api_base="http://default.invalid/api/v1",
            request_timeout=1,
            max_concurrent_workers=1,
            max_mutation_rounds=1,
        )

        executor = AdaptiveSandboxExecutor(config)

        with patch.object(
            executor.transport,
            "request",
        ) as request_mock:
            class FakeResponse:
                status_code = 404
                text = ""
                headers = {}

            request_mock.return_value = FakeResponse()

            executor.probe_all(
                [endpoint],
                base_url="http://override.invalid/api/v2",
            )

        request_mock.assert_called_once()

        call_kwargs = request_mock.call_args.kwargs

        self.assertEqual(
            call_kwargs["url"],
            "http://override.invalid/api/v2/api/orders",
        )

    def test_host_is_derived_from_source_file_subdomain(self) -> None:
        """【宿主动态解析】未指定 CLI base_url 时，按 source_file 子域名推导实际基地址"""
        for source, expected in [
            (r"tmp\raw_js\demo.ikuai8.com\c0223e037f4f6f9a38b0_index-0af67a26.js", "https://demo.ikuai8.com"),
            ("tmp/raw_js/cloud.ikuai8.com/07a7ade6ba70ea6ecb4e_chunk-71e3ab88.af00cba6.js", "https://cloud.ikuai8.com"),
            (r"tmp\raw_js\spdl.ikuai8.com\index.js", "https://spdl.ikuai8.com"),
        ]:
            endpoint = EndpointIR(
                method="GET",
                path="/api/x",
                source_file=source,
                line=1,
                is_dynamic=False,
                extracted_params=[],
                tags=[],
                risk_score=1.0,
                confidence=0.95,
                call_signature="get('/api/x')",
            )
            url = self.executor._build_url(endpoint)
            self.assertEqual(url, f"{expected}/api/x", msg=f"mismatch for {source}")

    def test_host_from_source_file_ignores_path_and_file(self) -> None:
        """【宿主动态解析】仅抽取子域宿主，路径与文件名不影响结果"""
        endpoint = EndpointIR(
            method="GET",
            path="/api/x",
            source_file=r"tmp\raw_js\demo.ikuai8.com\c0223e037f4f6f9a38b0_index-0af67a26.js",
            line=1,
            is_dynamic=False,
            extracted_params=[],
            tags=[],
            risk_score=1.0,
            confidence=0.95,
            call_signature="get('/api/x')",
        )
        host = self.executor._host_from_source_file(endpoint.source_file)
        self.assertEqual(host, "demo.ikuai8.com")
        self.assertEqual(self.executor._base_url_from_source_file(endpoint), "https://demo.ikuai8.com")

    def test_host_from_source_file_fallback_when_missing(self) -> None:
        """【宿主动态解析】source_file 不含 ikuai8.com 子域时返回 None，回退配置默认基址"""
        endpoint = EndpointIR(
            method="GET",
            path="/api/orders",
            source_file="fixture.js",
            line=10,
            is_dynamic=False,
            extracted_params=[],
            tags=[],
            risk_score=1.0,
            confidence=0.95,
            call_signature="client.get('/api/orders')",
        )
        self.assertIsNone(self.executor._host_from_source_file(endpoint.source_file))
        # 无宿主信息时回退到 cfg.target_api_base
        url = self.executor._build_url(endpoint)
        self.assertEqual(url, "http://default.invalid/api/v1/api/orders")

    def test_cli_base_url_override_beats_source_file_host(self) -> None:
        """【宿主动态解析】CLI 显式 base_url 优先，覆盖 source_file 推导结果"""
        demo_endpoint = EndpointIR(
            method="GET",
            path="/api/x",
            source_file=r"tmp\raw_js\demo.ikuai8.com\index.js",
            line=1,
            is_dynamic=False,
            extracted_params=[],
            tags=[],
            risk_score=1.0,
            confidence=0.95,
            call_signature="get('/api/x')",
        )
        url = self.executor._build_url(demo_endpoint, base_url="http://forced.invalid/api/v9")
        self.assertEqual(url, "http://forced.invalid/api/v9/api/x")


if __name__ == "__main__":
    unittest.main()
