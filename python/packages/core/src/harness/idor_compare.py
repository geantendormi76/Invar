# -*- coding: utf-8 -*-
"""
Invar Authorization Baseline Comparator (BOLA / IDOR 授权差分判定算子)
对标 Claude-Red (IDOR SOP) 与 Tencent A.I.G 黄金标准。
摒弃脆弱的单纯字符相似度，基于对象引用 (Object Reference) 提取与属主身份绑定实施精准断言，
彻底消除同构 JSON 误报与外层包装漏报。
"""
from __future__ import annotations

import difflib
import json
from typing import Any, Dict, List, Optional, Set

from harness.domain_contracts import IDOR_KEYWORDS
from harness.invariant_evaluator import InvariantEvaluation


class IdorCompareOperator:
    """
    Invar 高级攻防算子：BOLA / IDOR 双主体租户隔离与对象引用对比算子
    """

    SIMILARITY_THRESHOLD = 0.80

    @classmethod
    def _extract_identifiers(cls, data: Any, prefix: str = "") -> Dict[str, Any]:
        """
        递归提取结构化数据中承载对象身份的键值对 (Object Identifiers)
        """
        identifiers: Dict[str, Any] = {}
        if isinstance(data, dict):
            for k, v in data.items():
                k_lower = str(k).lower()
                is_id_key = (
                    any(kw == k_lower or kw in k_lower for kw in IDOR_KEYWORDS)
                    or k_lower.endswith("_id")
                    or k_lower == "id"
                )
                if is_id_key and isinstance(v, (str, int)) and not isinstance(v, bool):
                    full_key = f"{prefix}.{k}" if prefix else str(k)
                    identifiers[full_key] = v
                if isinstance(v, (dict, list)):
                    sub_prefix = f"{prefix}.{k}" if prefix else str(k)
                    identifiers.update(cls._extract_identifiers(v, prefix=sub_prefix))
        elif isinstance(data, list):
            for idx, item in enumerate(data):
                if isinstance(item, (dict, list)):
                    identifiers.update(cls._extract_identifiers(item, prefix=f"{prefix}[{idx}]"))
        return identifiers

    @classmethod
    def compare(
        cls,
        victim_response_text: str,
        attacker_response_text: str,
        attacker_status_code: int,
    ) -> InvariantEvaluation:
        inv_type = "idor_boundary"

        # 1. 明确的权限拦截 (401/403)
        if attacker_status_code in [401, 403]:
            return InvariantEvaluation(
                invariant_type=inv_type,
                status="confirmed",
                rationale=f"服务端返回 {attacker_status_code}，租户边界得到有效隔离",
            )

        # 2. 状态码在 200~299 成功区间：进入深度对象引用与属主比对
        if 200 <= attacker_status_code <= 299:
            victim_json = None
            attacker_json = None
            try:
                victim_json = json.loads(victim_response_text)
            except Exception:
                pass
            try:
                attacker_json = json.loads(attacker_response_text)
            except Exception:
                pass

            # -------------------------------------------------------------
            # 分支 A: 双方均为结构化 JSON 数据 (高精度对象引用比对)
            # -------------------------------------------------------------
            if isinstance(victim_json, (dict, list)) and isinstance(attacker_json, (dict, list)):
                victim_ids = cls._extract_identifiers(victim_json)
                attacker_ids = cls._extract_identifiers(attacker_json)

                # 场景 A1: 受害者响应中提取到了核心对象标识符
                if victim_ids:
                    leaked_ids = {}
                    attacker_id_values = set(attacker_ids.values())
                    for v_k, v_val in victim_ids.items():
                        # 若受害者的核心标识符值赫然出现在攻击者解析出的标识符池中，或出现在攻击者正文中
                        if v_val in attacker_id_values or str(v_val) in attacker_response_text:
                            # 进一步排查：如果攻击者在完全相同的字段上拥有不同的自身 ID，则不属于泄露
                            # 例如 victim 有 user_id=1001，attacker 有 user_id=1002，且 1001 未泄露
                            matching_attacker_keys = [
                                ak for ak, av in attacker_ids.items()
                                if ak.split(".")[-1] == v_k.split(".")[-1]
                            ]
                            if matching_attacker_keys:
                                if any(attacker_ids[ak] == v_val for ak in matching_attacker_keys):
                                    leaked_ids[v_k] = v_val
                            else:
                                if str(v_val) in attacker_response_text:
                                    leaked_ids[v_k] = v_val

                    # 实锤越权判定
                    if leaked_ids:
                        leaked_repr = ", ".join(f"{k}={v}" for k, v in leaked_ids.items())
                        return InvariantEvaluation(
                            invariant_type=inv_type,
                            status="vulnerable",
                            rationale=(
                                f"检测到受害者受保护对象标识符 [{leaked_repr}] 泄露于攻击者响应中，"
                                "存在水平越权 (IDOR / BOLA) 漏洞"
                            ),
                        )

                    # 属主安全判定：攻击者拥有属于自己的合法独立对象，未发生受害者数据跨主体泄露
                    if attacker_ids:
                        own_repr = ", ".join(f"{k}={v}" for k, v in attacker_ids.items())
                        return InvariantEvaluation(
                            invariant_type=inv_type,
                            status="confirmed",
                            rationale=(
                                f"攻击者访问属于自身的独立对象 [{own_repr}]，"
                                "未获取受害者对象，租户隔离正常"
                            ),
                        )

            # -------------------------------------------------------------
            # 分支 B: 非结构化数据或未发现 ID 键，平滑降级为文本相似度分析
            # -------------------------------------------------------------
            similarity = difflib.SequenceMatcher(
                None,
                victim_response_text,
                attacker_response_text,
            ).ratio()

            if similarity >= cls.SIMILARITY_THRESHOLD:
                return InvariantEvaluation(
                    invariant_type=inv_type,
                    status="vulnerable",
                    rationale=(
                        f"攻击者成功获取受害者资源，响应相似度达 {similarity:.2f} "
                        f"(阈值 {cls.SIMILARITY_THRESHOLD})，存在水平越权 (IDOR / BOLA) 漏洞"
                    ),
                )
            else:
                return InvariantEvaluation(
                    invariant_type=inv_type,
                    status="confirmed",
                    rationale=(
                        f"攻击者虽获得 {attacker_status_code} 响应，但相似度仅为 {similarity:.2f}，"
                        "与受害者基线差异巨大，未发生实质性数据泄露"
                    ),
                )

        # 3. 其他异常状态码 (如 500)
        return InvariantEvaluation(
            invariant_type=inv_type,
            status="inconclusive",
            rationale=f"服务端返回异常状态码 {attacker_status_code}，无法准确判定隔离状态",
        )
