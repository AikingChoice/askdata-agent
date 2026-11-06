from __future__ import annotations

import re

from .config import Settings

SYSTEM_PROMPT = """你是严谨的 SQLite 数据分析师。把用户问题转成一条只读 SELECT。

规则：
1. 只输出 SQL，不要 Markdown、解释或注释。
2. 只使用 schema 中出现的表和列，不要编造表名/列名。
3. 只允许 SELECT 或 WITH...SELECT；禁止 INSERT/UPDATE/DELETE/DDL/PRAGMA。
4. date_id 是 YYYYMMDD 整数。今天是 2026-11-05；上月是 20261001..20261031；本月是 20261101..20261105。
5. GMV 排除 status = 'cancelled'，按事实表 date_id 统计。
6. 多表查询写明确 JOIN；不要 SELECT *，只选需要的列。
7. 给结果列清晰别名，例如 gmv、order_count、refund_rate。
8. 只返回回答问题所需的最小列，不要额外列；排名/占比/增长率/对比类问题只返回对象列和指标列。
9. 问“哪些/哪个”时只返回对象列。
10. “连续 N 个月增长/下降”先按月聚合，再比较相邻月份；只返回对象列。
11. 按维度分组时，GROUP BY 使用维表的业务字段（如 dim_regions.region_group、dim_channels.channel_name），不要按 id 分组后再展示名称。
12. 复购客户 = 订单数 >= 2 的客户，不是 dim_customers.segment 的某个值。
"""


def clean_sql(text: str) -> str:
    text = (text or "").strip()
    if "```" in text:
        parts = text.split("```")
        for part in parts:
            candidate = part.strip()
            if candidate.lower().startswith("sql"):
                candidate = candidate[3:].strip()
            if candidate.lower().startswith(("select", "with")):
                return candidate.rstrip(";").strip()
    match = re.search(r"\b(select|with)\b", text, flags=re.IGNORECASE)
    if match:
        text = text[match.start() :]
    return text.rstrip(";").strip()


class MockLLM:
    model = "mock"

    def generate_sql(
        self,
        question: str,
        schema_text: str,
        metrics_text: str,
        previous_sql: str | None = None,
        error: str | None = None,
    ) -> str:
        text = question.lower()
        if "gmv" in text or "销售额" in text or "成交额" in text:
            return (
                "SELECT ROUND(SUM(net_amount), 2) AS gmv "
                "FROM fact_orders "
                "WHERE date_id BETWEEN 20261001 AND 20261031 "
                "AND status <> 'cancelled'"
            )
        if "订单数" in text or "单量" in text:
            return (
                "SELECT COUNT(DISTINCT order_id) AS order_count "
                "FROM fact_orders "
                "WHERE date_id BETWEEN 20261001 AND 20261031 "
                "AND status <> 'cancelled'"
            )
        if "退款率" in text:
            return (
                "SELECT ROUND(SUM(r.refund_amount) * 1.0 / "
                "NULLIF(SUM(CASE WHEN o.status <> 'cancelled' THEN o.net_amount ELSE 0 END), 0), 4) "
                "AS refund_rate "
                "FROM fact_orders o "
                "LEFT JOIN fact_refunds r ON r.order_id = o.order_id "
                "WHERE o.date_id BETWEEN 20261001 AND 20261031"
            )
        return "SELECT 1 AS ok"


class DeepSeekLLM:
    def __init__(self, settings: Settings):
        from openai import OpenAI

        self.model = settings.deepseek_model
        self.client = OpenAI(
            api_key=settings.deepseek_api_key,
            base_url=settings.deepseek_base_url,
            timeout=settings.timeout_seconds,
        )

    def generate_sql(
        self,
        question: str,
        schema_text: str,
        metrics_text: str,
        previous_sql: str | None = None,
        error: str | None = None,
    ) -> str:
        repair_note = ""
        if previous_sql and error:
            repair_note = (
                f"\n\n上一次 SQL 执行/校验失败：\n{previous_sql}\n"
                f"错误：{error}\n请修正这条 SQL，只输出一条 SQLite SELECT。"
            )
        user_prompt = (
            f"问题：{question}\n\n"
            f"可选表结构：\n{schema_text}\n\n"
            f"指标口径：\n{metrics_text}\n\n"
            "请只输出一条 SQLite SELECT。"
            f"{repair_note}"
        )
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0,
            max_tokens=2000,
        )
        content = response.choices[0].message.content or ""
        return clean_sql(content)


def build_llm(settings: Settings):
    if settings.llm_mode.lower() == "mock" or not settings.deepseek_api_key:
        return MockLLM()
    return DeepSeekLLM(settings)
