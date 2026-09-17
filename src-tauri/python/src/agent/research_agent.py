from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any, Dict, List

from harness.models import EndpointIR

from agent.model_provider import (
    ModelProviderError,
    OpenAICompatibleProvider,
)


@dataclass(frozen=True)
class AgentHypothesis:
    hypothesis_id: str
    statement: str
    rationale: str
    invariant_type: str
    priority: str


@dataclass(frozen=True)
class ResearchPlan:
    endpoint_key: str
    hypotheses: List[AgentHypothesis] = field(default_factory=list)
    recommended_invariants: List[str] = field(default_factory=list)
    stop_conditions: List[str] = field(default_factory=list)
    rationale: str = ""


class ResearchAgent:
    """
    Invar 模型研究代理。

    职责：
      1. 从 EndpointIR + Risk 选择研究候选；
      2. 调用外部模型形成研究假设；
      3. 输出结构化 ResearchPlan。

    不负责：
      - HTTP 请求
      - Payload 具体变异
      - 证据判定
      - VERIFIED / REFUTED 决策
    """

    SYSTEM_PROMPT = """
你是 Invar 的安全研究规划 Agent。

你的职责是：
1. 理解 EndpointIR、静态风险标签和参数；
2. 生成“可验证的研究假设”；
3. 为每个假设推荐已经存在的不变量类型；
4. 给出明确的停止条件。

严格遵守：
- 静态风险不是漏洞事实。
- 不得声称目标已经存在漏洞。
- 不得伪造 HTTP 响应、身份、令牌或服务器行为。
- 不得直接执行 HTTP 请求。
- 不得设计绕过授权边界的无约束攻击流程。
- 不得发明 Invar 尚不存在的执行器能力。
- 优先使用现有不变量：
  idor_boundary
  auth_boundary
  destructive_confirmation
- 输出必须是合法 JSON。
- 每个模型产生的假设 hypothesis_id 必须以 H-LLM- 开头。

输出格式：

{
  "plans": [
    {
      "endpoint_key": "METHOD:/path",
      "hypotheses": [
        {
          "hypothesis_id": "H-LLM-001",
          "statement": "可验证的研究假设",
          "rationale": "基于输入事实的理由",
          "invariant_type": "idor_boundary",
          "priority": "high"
        }
      ],
      "recommended_invariants": ["idor_boundary"],
      "stop_conditions": [
        "证据不足时停止",
        "不变量已经确认时停止"
      ],
      "rationale": "总体研究理由"
    }
  ]
}
""".strip()

    def __init__(
        self,
        provider: OpenAICompatibleProvider,
        max_candidates: int = 30,
    ) -> None:
        if max_candidates < 1:
            raise ValueError("max_candidates 必须 >= 1")

        self.provider = provider
        self.max_candidates = max_candidates

    @staticmethod
    def _endpoint_key(endpoint: EndpointIR) -> str:
        return f"{endpoint.method.upper()}:{endpoint.path}"

    @staticmethod
    def _candidate_key(endpoint: EndpointIR) -> tuple:
        return (
            -float(endpoint.risk_score),
            -len(endpoint.extracted_params),
            -float(endpoint.confidence),
            endpoint.method.upper(),
            endpoint.path,
        )

    def select_candidates(
        self,
        endpoints: List[EndpointIR],
    ) -> List[EndpointIR]:
        candidates = [
            endpoint
            for endpoint in endpoints
            if (
                "risk-critical" in endpoint.tags
                or "risk-high" in endpoint.tags
                or endpoint.extracted_params
            )
        ]

        candidates.sort(key=self._candidate_key)

        return candidates[: self.max_candidates]

    def _build_prompt(
        self,
        endpoints: List[EndpointIR],
    ) -> str:
        endpoint_data: List[Dict[str, Any]] = []

        for endpoint in endpoints:
            endpoint_data.append(
                {
                    "endpoint_key": self._endpoint_key(endpoint),
                    "method": endpoint.method,
                    "path": endpoint.path,
                    "source_file": endpoint.source_file,
                    "line": endpoint.line,
                    "is_dynamic": endpoint.is_dynamic,
                    "extracted_params": endpoint.extracted_params,
                    "tags": endpoint.tags,
                    "risk_score": endpoint.risk_score,
                    "confidence": endpoint.confidence,
                    "call_signature": endpoint.call_signature,
                }
            )

        return (
            "请基于以下 Invar 静态分析结果生成研究计划。\n\n"
            "注意：这些数据只是观察事实和静态风险评分，"
            "不要把风险评分写成已确认漏洞。\n\n"
            "输入：\n"
            + json.dumps(
                endpoint_data,
                ensure_ascii=False,
                indent=2,
            )
        )

    @staticmethod
    def _extract_json(content: str) -> Dict[str, Any]:
        text = content.strip()

        if text.startswith("```"):
            lines = text.splitlines()

            if lines and lines[0].startswith("```"):
                lines = lines[1:]

            if lines and lines[-1].strip() == "```":
                lines = lines[:-1]

            text = "\n".join(lines).strip()

            if text.startswith("json"):
                text = text[4:].lstrip()

        try:
            value = json.loads(text)
        except json.JSONDecodeError as exc:
            raise ModelProviderError(
                f"模型输出不是合法 JSON: {exc}"
            ) from exc

        if not isinstance(value, dict):
            raise ModelProviderError(
                "模型 JSON 顶层对象不是 object。"
            )

        return value

    @staticmethod
    def _validate_plan(
        raw: Dict[str, Any],
        valid_endpoint_keys: set[str],
    ) -> List[ResearchPlan]:
        plans_value = raw.get("plans", [])

        if not isinstance(plans_value, list):
            raise ModelProviderError(
                "模型输出中的 plans 不是数组。"
            )

        plans: List[ResearchPlan] = []

        for plan_value in plans_value:
            if not isinstance(plan_value, dict):
                continue

            endpoint_key = str(
                plan_value.get("endpoint_key", "")
            ).strip()

            if endpoint_key not in valid_endpoint_keys:
                continue

            raw_hypotheses = plan_value.get("hypotheses", [])

            hypotheses: List[AgentHypothesis] = []

            if isinstance(raw_hypotheses, list):
                for item in raw_hypotheses:
                    if not isinstance(item, dict):
                        continue

                    hypothesis_id = str(
                        item.get("hypothesis_id", "")
                    ).strip()

                    if not hypothesis_id.startswith("H-LLM-"):
                        continue

                    statement = str(
                        item.get("statement", "")
                    ).strip()

                    rationale = str(
                        item.get("rationale", "")
                    ).strip()

                    invariant_type = str(
                        item.get("invariant_type", "")
                    ).strip()

                    priority = str(
                        item.get("priority", "medium")
                    ).strip().lower()

                    if not statement or not rationale:
                        continue

                    if invariant_type not in {
                        "idor_boundary",
                        "auth_boundary",
                        "destructive_confirmation",
                    }:
                        continue

                    if priority not in {
                        "low",
                        "medium",
                        "high",
                    }:
                        priority = "medium"

                    hypotheses.append(
                        AgentHypothesis(
                            hypothesis_id=hypothesis_id,
                            statement=statement,
                            rationale=rationale,
                            invariant_type=invariant_type,
                            priority=priority,
                        )
                    )

            recommended = plan_value.get(
                "recommended_invariants",
                [],
            )
            if not isinstance(recommended, list):
                recommended = []

            recommended = [
                str(value).strip()
                for value in recommended
                if str(value).strip()
                in {
                    "idor_boundary",
                    "auth_boundary",
                    "destructive_confirmation",
                }
            ]

            stop_conditions = plan_value.get(
                "stop_conditions",
                [],
            )
            if not isinstance(stop_conditions, list):
                stop_conditions = []

            stop_conditions = [
                str(value).strip()
                for value in stop_conditions
                if str(value).strip()
            ]

            rationale = str(
                plan_value.get("rationale", "")
            ).strip()

            plans.append(
                ResearchPlan(
                    endpoint_key=endpoint_key,
                    hypotheses=hypotheses,
                    recommended_invariants=recommended,
                    stop_conditions=stop_conditions,
                    rationale=rationale,
                )
            )

        return plans

    def plan(
        self,
        endpoints: List[EndpointIR],
    ) -> Dict[str, Any]:
        candidates = self.select_candidates(endpoints)

        if not candidates:
            return {
                "status": "no_candidates",
                "model": self.provider.model,
                "candidate_count": 0,
                "plans": [],
            }

        prompt = self._build_prompt(candidates)

        response = self.provider.chat(
            system_prompt=self.SYSTEM_PROMPT,
            user_prompt=prompt,
            temperature=0.1,
            max_tokens=6000,
        )

        valid_keys = {
            self._endpoint_key(endpoint)
            for endpoint in candidates
        }

        raw = self._extract_json(response.content)
        plans = self._validate_plan(
            raw,
            valid_endpoint_keys=valid_keys,
        )

        return {
            "status": "completed",
            "model": response.model,
            "candidate_count": len(candidates),
            "plans": [
                {
                    "endpoint_key": plan.endpoint_key,
                    "hypotheses": [
                        {
                            "hypothesis_id": hypothesis.hypothesis_id,
                            "statement": hypothesis.statement,
                            "rationale": hypothesis.rationale,
                            "invariant_type": hypothesis.invariant_type,
                            "priority": hypothesis.priority,
                        }
                        for hypothesis in plan.hypotheses
                    ],
                    "recommended_invariants": (
                        plan.recommended_invariants
                    ),
                    "stop_conditions": plan.stop_conditions,
                    "rationale": plan.rationale,
                }
                for plan in plans
            ],
        }
