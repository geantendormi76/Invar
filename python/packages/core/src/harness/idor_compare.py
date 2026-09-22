import difflib
from harness.invariant_evaluator import InvariantEvaluation


class IdorCompareOperator:
    """
    Invar 高级攻防算子：BOLA / IDOR 双主体租户隔离对比算子
    通过对比受害者基线响应与攻击者越权响应的结构相似度，精准判定水平越权漏洞，彻底消除 200 OK 误报
    """

    SIMILARITY_THRESHOLD = 0.80

    @classmethod
    def compare(
        cls,
        victim_response_text: str,
        attacker_response_text: str,
        attacker_status_code: int,
    ) -> InvariantEvaluation:
        inv_type = "idor_boundary"

        # 1. 明确的权限拦截
        if attacker_status_code in [401, 403]:
            return InvariantEvaluation(
                invariant_type=inv_type,
                status="confirmed",
                rationale=f"服务端返回 {attacker_status_code}，租户边界得到有效隔离",
            )

        # 2. 状态码看似成功，进入深度微观对账 (Differential Compare)
        if 200 <= attacker_status_code <= 299:
            # 计算两份响应文本的相似度
            similarity = difflib.SequenceMatcher(
                None, 
                victim_response_text, 
                attacker_response_text
            ).ratio()

            if similarity >= cls.SIMILARITY_THRESHOLD:
                return InvariantEvaluation(
                    invariant_type=inv_type,
                    status="vulnerable",
                    rationale=f"攻击者成功获取受害者资源，响应相似度达 {similarity:.2f} (阈值 {cls.SIMILARITY_THRESHOLD})，存在水平越权 (IDOR / BOLA) 漏洞",
                )
            else:
                return InvariantEvaluation(
                    invariant_type=inv_type,
                    status="confirmed",
                    rationale=f"攻击者虽获得 {attacker_status_code} 响应，但相似度仅为 {similarity:.2f}，与受害者基线差异巨大，未发生实质性数据泄露",
                )

        # 3. 其他异常状态码 (如 500)
        return InvariantEvaluation(
            invariant_type=inv_type,
            status="inconclusive",
            rationale=f"服务端返回异常状态码 {attacker_status_code}，无法准确判定隔离状态",
        )
