import unittest

from harness.triage_dispatcher import TriageDispatcher


class TriageDispatcherSemanticContractTests(unittest.TestCase):
    def test_high_impact_non_destructive_state_change_uses_authorization_contract(self):
        dispatcher = TriageDispatcher(
            impact_threshold=3.5,
            sensitivity_threshold=3.5,
        )

        endpoint_row = {
            "surface_id": "sid_recursive_move",
            "endpoint_id": "POST:/fs/recursive_move",
            "method": "POST",
            "path": "/fs/recursive_move",
            "extracted_params": [
                "src_dir",
                "dst_dir",
                "conflict_policy",
            ],
            "rule": {
                "high_risk_candidate": True,
                "destructive": False,
            },
            "neural": {
                "impact_score": 3.65,
                "sensitivity_score": 2.51,
                "neural_usable": True,
            },
        }

        task = dispatcher.classify_and_assemble(
            endpoint_row,
            pool_origin="POOL_B_DISCREPANCY",
        )

        self.assertEqual(task.priority, "P1")
        self.assertEqual(task.profile, "p1_state_mutation_safety")
        self.assertEqual(task.hypothesis_id, "H-AUTH-1")

        # Canonical research semantics:
        # profile describes HOW to research;
        # attack_class describes WHAT security property is being evaluated.
        self.assertEqual(task.attack_class, "authorization")
        self.assertEqual(task.coverage_id, "api-fs-authorization")


if __name__ == "__main__":
    unittest.main()
