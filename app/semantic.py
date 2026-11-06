from __future__ import annotations

import re
from dataclasses import dataclass, field

WRITE_RE = re.compile(
    r"(删除|删掉|删了|清空|修改|更新|插入|写入|\b(drop|delete|update|insert|truncate|alter)\b)",
    re.IGNORECASE,
)
PII_TERMS = ("身份证", "手机号", "电话号码", "银行卡", "密码", "邮箱", "住址", "家庭地址")
UNSUPPORTED_TERMS = ("库存", "薪资", "工资", "供应商", "物流轨迹", "轨迹")
RECENT_TERMS = ("最近", "近来", "现在", "目前")
SALES_TERMS = ("销售", "业绩", "情况", "怎么样")
TIME_TERMS = (
    "上月", "上个月", "本月", "这个月", "上周", "本周", "昨天", "今天",
    "本季度", "季度", "q1", "q2", "q3", "q4", "年", "月", "日", "周",
    "同比", "环比", "连续", "至今", "去年",
)
DIMENSION_HINTS = {
    "region": ("区域", "大区", "华东", "华北", "华南", "华中", "西南", "西北", "东北", "省", "城市"),
    "channel": ("渠道", "app", "官网", "小程序", "线下", "电商平台"),
    "category": ("品类", "商品", "品牌"),
    "customer": ("客户", "新客", "老客", "复购客户", "用户"),
    "campaign": ("活动", "营销"),
    "sales_rep": ("销售员", "销售代表", "销售负责", "负责人"),
}
GENERIC_DIMENSIONS = ("各", "按", "top", "排名", "最高", "最低")


@dataclass
class Analysis:
    route: str
    reason: str = "ok"
    answer: str = ""
    metric: str | None = None
    time_range: list[str] = field(default_factory=list)
    dimensions: list[str] = field(default_factory=list)

    def as_dict(self) -> dict:
        return {
            "route": self.route,
            "reason": self.reason,
            "metric": self.metric,
            "time_range": self.time_range,
            "dimensions": self.dimensions,
        }


def _metric_terms(metrics: dict) -> dict[str, str]:
    terms: dict[str, str] = {}
    for key, item in metrics.get("metrics", {}).items():
        for term in [key, item.get("label", ""), *item.get("synonyms", [])]:
            if term:
                terms[str(term).lower()] = key
    for key, item in metrics.get("supporting_measures", {}).items():
        for term in [key, item.get("label", ""), *item.get("synonyms", [])]:
            if term:
                terms[str(term).lower()] = key
    terms["退款原因"] = "refund_amount"
    terms["新客"] = "new_customer_count"
    return dict(sorted(terms.items(), key=lambda item: len(item[0]), reverse=True))


def _detect_metric(text: str, terms: dict[str, str]) -> str | None:
    for term, metric in terms.items():
        if term in text:
            return metric
    return None


def _detect_dimensions(text: str) -> list[str]:
    dimensions = []
    for key, words in DIMENSION_HINTS.items():
        if any(word in text for word in words):
            dimensions.append(key)
    if any(word in text for word in GENERIC_DIMENSIONS):
        dimensions.append("generic")
    return dimensions


def analyze_question(question: str, metrics: dict) -> Analysis:
    text = question.lower().strip()
    if WRITE_RE.search(text):
        return Analysis(
            "refuse",
            reason="write_operation",
            answer="当前只支持只读查询，不能执行删除、更新或写入操作。",
        )
    if any(term in text for term in PII_TERMS):
        return Analysis(
            "refuse",
            reason="pii",
            answer="当前数据源不包含身份证、手机号等敏感字段，且无相应权限，无法回答。",
        )
    if any(term in text for term in UNSUPPORTED_TERMS):
        return Analysis(
            "refuse",
            reason="unsupported_data",
            answer="当前数据源没有这个字段或主题，无法回答。",
        )

    if any(term in text for term in RECENT_TERMS) and any(
        term in text for term in SALES_TERMS
    ):
        return Analysis(
            "clarify",
            reason="recent_ambiguous",
            answer="你想看哪个时间段、哪个指标？例如：上月 GMV、本月各品类销售额。",
        )

    terms = _metric_terms(metrics)
    metric = _detect_metric(text, terms)
    dimensions = _detect_dimensions(text)
    time_range = [term for term in TIME_TERMS if term in text]

    if not metric:
        return Analysis(
            "clarify",
            reason="missing_metric",
            answer="请补充指标和时间范围，例如：上月 GMV、本月各渠道订单数。",
            time_range=time_range,
            dimensions=dimensions,
        )

    if metric == "gmv" and "销售额" in text and not dimensions:
        return Analysis(
            "clarify",
            reason="sales_caliber",
            answer="“销售额”是指 GMV（含税、未扣退款），还是净收入（扣退款）？",
            metric=metric,
            time_range=time_range,
            dimensions=dimensions,
        )

    if not time_range and not dimensions:
        return Analysis(
            "clarify",
            reason="missing_time_or_dimension",
            answer="请补充时间范围（如上月/本月）或维度（如区域/渠道/品类）。",
            metric=metric,
            time_range=time_range,
            dimensions=dimensions,
        )

    return Analysis(
        "sql",
        reason="ok",
        metric=metric,
        time_range=time_range,
        dimensions=dimensions,
    )
