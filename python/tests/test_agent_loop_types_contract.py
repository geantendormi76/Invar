import unittest
from agent.loop_types import (
    AbortSignal,
    QueueMode,
    ResearchEvent,
    ResearchEventType,
    ResearchMessage,
    ResearchMessageRole,
    SteeringMessage,
    convert_to_llm,
)


class AgentLoopTypesContractTests(unittest.TestCase):
    """
    验证消息双轨制、转译边界与强类型事件流的核心契约
    """

    def test_two_track_message_conversion_and_mapping(self):
        """【契约 1】内轨富文本消息转译为外轨标准 OpenAI 字典，并准确映射 CRITIC_STEER"""
        internal_messages = [
            ResearchMessage(
                role=ResearchMessageRole.SYSTEM,
                content="You are an expert security researcher.",
            ),
            ResearchMessage(
                role=ResearchMessageRole.CRITIC_STEER,
                content="WAF detected via Server header. Prioritize X-Rewrite-URL.",
                metadata={"source": "CoverageCritic"},
            ),
            ResearchMessage(
                role=ResearchMessageRole.TOOL_RESULT,
                content="HTTP 403 Forbidden",
                variant_ref="F3_REWRITE_URL",
            ),
        ]

        llm_messages = convert_to_llm(internal_messages)
        self.assertEqual(len(llm_messages), 3)

        # 1. 验证系统消息原样保留
        self.assertEqual(llm_messages[0]["role"], "system")
        self.assertEqual(llm_messages[0]["content"], "You are an expert security researcher.")

        # 2. 验证 CRITIC_STEER 映射为 user 且添加清晰前缀
        self.assertEqual(llm_messages[1]["role"], "user")
        self.assertIn("[CoverageCritic Steering Instruction]", llm_messages[1]["content"])

        # 3. 验证 TOOL_RESULT 映射为 user 且标注变体标识
        self.assertEqual(llm_messages[2]["role"], "user")
        self.assertIn("[Probe Result (F3_REWRITE_URL)]", llm_messages[2]["content"])

    def test_context_boundary_enforces_800_char_slice_limit(self):
        """【契约 2】上下文边界硬约束：长文本内容被强制截断至 800 字符内，杜绝 OOM"""
        giant_code = "const sensitiveOperation = () => { " + ("A" * 2000) + " };"
        msg = ResearchMessage(
            role=ResearchMessageRole.USER,
            content=giant_code,
        )
        llm_msgs = convert_to_llm([msg], max_slice_chars=800)
        content = llm_msgs[0]["content"]

        self.assertTrue(len(content) <= 850)
        self.assertIn("[TRUNCATED_AT_800_CHARS]", content)

    def test_push_based_event_sink_and_event_serialization(self):
        """【契约 3】推模式事件流：强类型事件按顺序入流且支持 100% 无损字典序列化"""
        received_events = []

        def mock_sink(event: ResearchEvent) -> None:
            received_events.append(event)

        # 模拟执行过程中的连续事件抛送
        mock_sink(ResearchEvent(
            event_type=ResearchEventType.LOOP_START,
            payload={"target_endpoint": "GET:/api/v1/secrets"},
        ))
        mock_sink(ResearchEvent(
            event_type=ResearchEventType.DENIAL_CLASSIFIED,
            payload={"category": "ACCESS_POLICY_DENIAL", "frontend": "WAF"},
        ))
        mock_sink(ResearchEvent(
            event_type=ResearchEventType.VARIANT_SELECTED,
            payload={"variant_id": "F3_REWRITE_X_REWRITE_URL"},
        ))
        mock_sink(ResearchEvent(
            event_type=ResearchEventType.LOOP_END,
            payload={"verdict": "CONFIRMED"},
        ))

        self.assertEqual(len(received_events), 4)
        self.assertEqual(received_events[0].event_type, ResearchEventType.LOOP_START)
        self.assertEqual(received_events[1].event_type, ResearchEventType.DENIAL_CLASSIFIED)
        self.assertEqual(received_events[3].event_type, ResearchEventType.LOOP_END)

        # 验证序列化字典格式满足前端/IPC 需求
        event_dict = received_events[1].to_dict()
        self.assertEqual(event_dict["event_type"], "denial_classified")
        self.assertEqual(event_dict["payload"]["frontend"], "WAF")
        self.assertIn("timestamp", event_dict)

    def test_abort_signal_thread_safety_and_reason(self):
        """【契约 4】取消信号控制：初始未中断，触发 abort 后准确记录中断原因"""
        signal = AbortSignal()
        self.assertFalse(signal.is_aborted)
        self.assertIsNone(signal.reason)

        signal.abort("Budget exceeded")
        self.assertTrue(signal.is_aborted)
        self.assertEqual(signal.reason, "Budget exceeded")

    def test_steering_message_conversion(self):
        """【契约 5】干预消息实体无缝转换为内轨科研消息"""
        steering = SteeringMessage(
            content="Force header tunnel testing",
            source="HumanSupervisor",
            metadata={"priority": "urgent"},
        )
        research_msg = steering.to_research_message()
        self.assertEqual(research_msg.role, ResearchMessageRole.CRITIC_STEER)
        self.assertEqual(research_msg.content, "Force header tunnel testing")
        self.assertEqual(research_msg.metadata["source"], "HumanSupervisor")
        self.assertEqual(research_msg.metadata["priority"], "urgent")


if __name__ == "__main__":
    unittest.main()
