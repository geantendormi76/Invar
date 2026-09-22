import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from harness.triage_dispatcher import TriageDispatcher, TriageTask


class TriageDispatcherTests(unittest.TestCase):
    def setUp(self):
        self.dispatcher = TriageDispatcher(impact_threshold=3.5, sensitivity_threshold=3.5)

    def test_classify_dual_high_non_destructive_assigns_auth_hypothesis(self):
        # 双高但非破坏性（特权修改/角色提升）：主假说为特权认证边界 H-AUTH-1
        endpoint_row = {
            "surface_id": "sid_dual_high_01",
            "endpoint_id": "POST:/api/user/role",
            "method": "POST",
            "path": "/api/user/role",
            "extracted_params": ["user_id", "role_id"],
            "rule": {"high_risk_candidate": True, "destructive": False},
            "neural": {"impact_score": 4.2, "sensitivity_score": 4.0, "neural_usable": True},
        }
        task = self.dispatcher.classify_and_assemble(endpoint_row, pool_origin="POOL_B_DISCREPANCY")
        self.assertEqual(task.priority, "P0")
        self.assertEqual(task.profile, "p0_dual_high_state_and_confidentiality")
        self.assertEqual(task.hypothesis_id, "H-AUTH-1")
        self.assertEqual(task.method, "POST")
        self.assertEqual(task.endpoint_id, "POST:/api/user/role")

    def test_classify_dual_high_destructive_assigns_destruct_hypothesis(self):
        # 双高且破坏性（清空/删除用户数据）：主假说为破坏性确认防护 H-DESTRUCT-1
        endpoint_row = {
            "surface_id": "sid_dual_high_destruct",
            "endpoint_id": "DELETE:/api/user/purge",
            "method": "DELETE",
            "path": "/api/user/purge",
            "extracted_params": ["user_id"],
            "rule": {"high_risk_candidate": True, "destructive": True},
            "neural": {"impact_score": 4.8, "sensitivity_score": 4.5, "neural_usable": True},
        }
        task = self.dispatcher.classify_and_assemble(endpoint_row, pool_origin="POOL_A_RULE_MUST_KEEP")
        self.assertEqual(task.priority, "P0")
        self.assertEqual(task.profile, "p0_dual_high_state_and_confidentiality")
        self.assertEqual(task.hypothesis_id, "H-DESTRUCT-1")
        self.assertEqual(task.method, "DELETE")

    def test_classify_high_impact_assigns_state_mutation_profile(self):
        endpoint_row = {
            "surface_id": "sid_impact_01",
            "endpoint_id": "DELETE:/api/order/batch",
            "method": "DELETE",
            "path": "/api/order/batch",
            "extracted_params": ["order_ids"],
            "rule": {"high_risk_candidate": True, "destructive": True},
            "neural": {"impact_score": 4.5, "sensitivity_score": 2.0, "neural_usable": True},
        }
        task = self.dispatcher.classify_and_assemble(endpoint_row, pool_origin="POOL_A_RULE_MUST_KEEP")
        self.assertEqual(task.priority, "P1")
        self.assertEqual(task.profile, "p1_state_mutation_safety")
        self.assertEqual(task.hypothesis_id, "H-DESTRUCT-1")
        self.assertEqual(task.attack_class, "destructive_action")

    def test_classify_high_sensitivity_with_id_params_assigns_idor_profile(self):
        endpoint_row = {
            "surface_id": "sid_sens_01",
            "endpoint_id": "GET:/api/tenant/invoice",
            "method": "GET",
            "path": "/api/tenant/invoice",
            "extracted_params": ["tenant_id", "order_id"],
            "rule": {"high_risk_candidate": False, "destructive": False},
            "neural": {"impact_score": 2.1, "sensitivity_score": 4.1, "neural_usable": True},
        }
        task = self.dispatcher.classify_and_assemble(endpoint_row, pool_origin="POOL_B_DISCREPANCY")
        self.assertEqual(task.priority, "P1")
        self.assertEqual(task.profile, "p1_differential_idor_leak")
        self.assertEqual(task.hypothesis_id, "H-IDOR-1")
        self.assertEqual(task.attack_class, "idor_boundary")

    def test_satisfies_rust_research_task_contract(self):
        endpoint_row = {
            "surface_id": "sid_contract_01",
            "endpoint_id": "POST:/api/device/reboot",
            "method": "POST",
            "path": "/api/device/reboot",
            "extracted_params": [],
            "rule": {"high_risk_candidate": True, "destructive": True},
            "neural": {"impact_score": 5.0, "sensitivity_score": 3.0, "neural_usable": True},
        }
        task = self.dispatcher.classify_and_assemble(endpoint_row, pool_origin="POOL_A_RULE_MUST_KEEP")
        rust_dict = task.to_rust_task_dict()
        required_keys = {"task_id", "endpoint_id", "coverage_id", "hypothesis_id", "profile", "method", "path"}
        self.assertTrue(required_keys.issubset(set(rust_dict.keys())))
        self.assertEqual(rust_dict["endpoint_id"], "POST:/api/device/reboot")

    def test_assemble_from_files_filters_and_deduplicates(self):
        with TemporaryDirectory() as temp_dir:
            pools_path = Path(temp_dir) / "pools.json"
            dual_track_path = Path(temp_dir) / "dual_track.jsonl"

            pools_data = {
                "pool_a_rule_must_keep": ["sid_a1", "sid_a2"],
                "pool_b_discrepancy": ["sid_b1"],
                "pool_c_exploration": ["sid_c1"],
            }
            pools_path.write_text(json.dumps(pools_data), encoding="utf-8")

            dual_rows = [
                {"surface_id": "sid_a1", "endpoint_id": "DELETE:/a1", "method": "DELETE", "path": "/a1", "extracted_params": [], "neural": {"impact_score": 4.5, "sensitivity_score": 1.0, "neural_usable": True}, "rule": {"high_risk_candidate": True}},
                {"surface_id": "sid_a1", "endpoint_id": "DELETE:/a1", "method": "DELETE", "path": "/a1", "extracted_params": ["id"], "neural": {"impact_score": 4.5, "sensitivity_score": 1.0, "neural_usable": True}, "rule": {"high_risk_candidate": True}},
                {"surface_id": "sid_a2", "endpoint_id": "POST:/a2", "method": "POST", "path": "/a2", "extracted_params": [], "neural": {"impact_score": 2.0, "sensitivity_score": 2.0, "neural_usable": True}, "rule": {"high_risk_candidate": True}},
                {"surface_id": "sid_b1", "endpoint_id": "GET:/b1", "method": "GET", "path": "/b1", "extracted_params": ["user_id"], "neural": {"impact_score": 2.0, "sensitivity_score": 4.0, "neural_usable": True}, "rule": {"high_risk_candidate": False}},
                {"surface_id": "sid_c1", "endpoint_id": "GET:/c1", "method": "GET", "path": "/c1", "extracted_params": [], "neural": {"impact_score": 1.0, "sensitivity_score": 1.0, "neural_usable": True}, "rule": {"high_risk_candidate": False}},
            ]
            dual_track_path.write_text("\n".join(json.dumps(r) for r in dual_rows), encoding="utf-8")

            tasks = self.dispatcher.assemble_from_files(
                pools_path=pools_path,
                dual_track_path=dual_track_path,
                target_pools=["pool_a_rule_must_keep", "pool_b_discrepancy"]
            )

            self.assertEqual(len(tasks), 3)
            task_sids = {t.surface_id for t in tasks}
            self.assertEqual(task_sids, {"sid_a1", "sid_a2", "sid_b1"})
