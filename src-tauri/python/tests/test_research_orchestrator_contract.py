import unittest
from unittest.mock import Mock

from harness.config import InvarConfig
from harness.models import EndpointIR
from harness.research_models import ResearchExecutionResult


class ResearchOrchestratorContractTests(unittest.TestCase):
    def test_orchestrator_runs_one_research_case_and_returns_execution_result(
        self,
    ) -> None:
        from harness.research_orchestrator import ResearchOrchestrator

        endpoint = EndpointIR(
            method="POST",
            path="/api/orders",
            source_file="fixture.js",
            line=10,
            is_dynamic=False,
            extracted_params=["orderId"],
            tags=[],
            risk_score=5.0,
            confidence=0.95,
            call_signature="client.post('/api/orders')",
        )

        fake_result = Mock(spec=ResearchExecutionResult)

        executor = Mock()
        executor.probe_endpoint_with_research.return_value = fake_result

        orchestrator = ResearchOrchestrator(
            executor=executor,
        )

        result = orchestrator.run(endpoint)

        self.assertIs(result, fake_result)

        executor.probe_endpoint_with_research.assert_called_once_with(
            endpoint,
        )


if __name__ == "__main__":
    unittest.main()
