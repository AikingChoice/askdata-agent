from __future__ import annotations

import sqlite3
from pathlib import Path

TABLE_DESCRIPTIONS = {
    "fact_orders": "订单事实表：订单、GMV、销售额、订单数、客单价、退款率、下单日期、状态",
    "fact_order_items": "订单商品明细：商品、品类、数量、单价、成本、行金额",
    "fact_refunds": "退款事实表：退款金额、退款原因、退款状态、退款日期",
    "dim_dates": "日期维：年、季度、月、周、日期、节假日",
    "dim_regions": "区域维：省、市、大区、区域别名（华东/华东区/江浙沪）",
    "dim_channels": "渠道维：App、官网、小程序、线下门店、电商平台",
    "dim_products": "商品维：商品名、品类、品牌、成本、标价",
    "dim_customers": "客户维：客户、新客、老客、复购、注册日期、所属区域",
    "dim_campaigns": "活动维：618、双 11、818、年货节",
    "dim_sales_reps": "销售维：销售、负责人、所属区域",
}

KEYWORDS = {
    "fact_orders": ["订单", "gmv", "销售额", "成交额", "客单价", "下单", "退款率", "退货率", "复购"],
    "fact_order_items": ["商品", "品类", "明细", "销量", "成本", "毛利"],
    "fact_refunds": ["退款", "退货", "退款原因"],
    "dim_dates": ["上月", "本月", "日期", "季度", "月", "年", "周", "趋势", "环比", "同比", "q1", "q2", "q3", "q4"],
    "dim_regions": ["区域", "大区", "华东", "华北", "华南", "城市", "省"],
    "dim_customers": ["客户", "新客", "老客", "复购", "注册"],
    "dim_products": ["商品", "品类", "品牌", "成本"],
    "dim_channels": ["渠道"],
    "dim_campaigns": ["活动", "营销"],
    "dim_sales_reps": ["销售", "负责人"],
}

TIME_WORDS = ("月", "季度", "年", "周", "日", "同比", "环比", "趋势", "今天", "昨天", "上周", "上月", "本月", "q1", "q2", "q3", "q4")


def load_schema(db_path: Path) -> dict[str, dict]:
    if not db_path.exists():
        raise FileNotFoundError(f"database not found: {db_path}")
    uri = f"file:{db_path.as_posix()}?mode=ro"
    conn = sqlite3.connect(uri, uri=True)
    try:
        table_names = [
            row[0]
            for row in conn.execute(
                "SELECT name FROM sqlite_master "
                "WHERE type = 'table' AND name NOT LIKE 'sqlite_%' ORDER BY name"
            )
        ]
        schema: dict[str, dict] = {}
        for table in table_names:
            columns = []
            for row in conn.execute(f'PRAGMA table_info("{table}")'):
                columns.append(
                    {
                        "cid": row[0],
                        "name": row[1],
                        "type": row[2],
                        "notnull": bool(row[3]),
                        "default": row[4],
                        "pk": bool(row[5]),
                    }
                )
            foreign_keys = []
            for row in conn.execute(f'PRAGMA foreign_key_list("{table}")'):
                foreign_keys.append(
                    {"table": row[2], "from": row[3], "to": row[4]}
                )
            schema[table] = {"columns": columns, "foreign_keys": foreign_keys}
        return schema
    finally:
        conn.close()


def select_tables(question: str, schema: dict[str, dict], limit: int = 6) -> list[str]:
    text = question.lower()
    scores = {name: 0 for name in schema}
    for table, words in KEYWORDS.items():
        if table not in schema:
            continue
        for word in words:
            if word.lower() in text:
                scores[table] += 2
    if "fact_orders" in scores:
        scores["fact_orders"] += 1
    if any(word in text for word in TIME_WORDS) and "dim_dates" in schema:
        scores["dim_dates"] += 2
    if scores.get("fact_refunds", 0) > 0:
        scores["fact_orders"] += 1
    if scores.get("fact_order_items", 0) > 0:
        scores["fact_orders"] += 1

    ordered = sorted(
        scores,
        key=lambda name: (scores[name], name == "fact_orders"),
        reverse=True,
    )
    selected = [name for name in ordered if scores[name] > 0 or name == "fact_orders"]
    return selected[:limit]


def format_schema(schema: dict[str, dict], selected: list[str]) -> str:
    lines: list[str] = []
    for name in selected:
        info = schema[name]
        lines.append(f"TABLE {name} -- {TABLE_DESCRIPTIONS.get(name, '')}")
        for column in info["columns"]:
            flags = []
            if column["pk"]:
                flags.append("PK")
            if column["notnull"]:
                flags.append("NOT NULL")
            suffix = (" " + " ".join(flags)) if flags else ""
            lines.append(f"  {column['name']} {column['type']}{suffix}")
        foreign_keys = [
            fk for fk in info["foreign_keys"] if fk["table"] in selected
        ]
        if foreign_keys:
            lines.append(
                "  FK: "
                + "; ".join(
                    f"{fk['from']} -> {fk['table']}.{fk['to']}" for fk in foreign_keys
                )
            )
        lines.append("")
    return "\n".join(lines)
