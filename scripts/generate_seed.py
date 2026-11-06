"""Generate deterministic AskData demo seed data.

Usage:
    python scripts/generate_seed.py

Output:
    data/seed.sql
"""

from __future__ import annotations

import calendar
import random
from collections import Counter, defaultdict
from datetime import date, timedelta
from pathlib import Path

random.seed(20261105)
OUT = Path(__file__).resolve().parent.parent / "data" / "seed.sql"
START = date(2025, 1, 1)
DIM_END = date(2026, 12, 31)
FACT_END = date(2026, 11, 5)

# ---------- dates ----------
holidays: set[date] = set()


def add_range(start_date: date, end_date: date) -> None:
    current = start_date
    while current <= end_date:
        holidays.add(current)
        current += timedelta(days=1)


add_range(date(2025, 1, 1), date(2025, 1, 1))
add_range(date(2025, 1, 28), date(2025, 2, 4))
add_range(date(2025, 4, 4), date(2025, 4, 6))
add_range(date(2025, 5, 1), date(2025, 5, 5))
add_range(date(2025, 10, 1), date(2025, 10, 7))
add_range(date(2026, 1, 1), date(2026, 1, 1))
add_range(date(2026, 2, 16), date(2026, 2, 22))
add_range(date(2026, 4, 4), date(2026, 4, 6))
add_range(date(2026, 5, 1), date(2026, 5, 5))
add_range(date(2026, 10, 1), date(2026, 10, 7))

dates: list[date] = []
day = START
while day <= DIM_END:
    dates.append(day)
    day += timedelta(days=1)

# ---------- dimensions ----------
regions = [
    (1, "上海", "上海", "华东", "华东,华东区,江浙沪,上海"),
    (2, "江苏", "南京", "华东", "华东,华东区,江浙沪,江苏"),
    (3, "浙江", "杭州", "华东", "华东,华东区,江浙沪,浙江"),
    (4, "安徽", "合肥", "华东", "华东,华东区,安徽"),
    (5, "江苏", "苏州", "华东", "华东,华东区,江浙沪,苏州"),
    (6, "北京", "北京", "华北", "华北,华北区,京津冀,北京"),
    (7, "广东", "深圳", "华南", "华南,华南区,珠三角,广东"),
    (8, "湖北", "武汉", "华中", "华中,华中区,湖北"),
    (9, "四川", "成都", "西南", "西南,西南区,四川"),
    (10, "辽宁", "沈阳", "东北", "东北,东北区,辽宁"),
    (11, "陕西", "西安", "西北", "西北,西北区,陕西"),
    (12, "浙江", "宁波", "华东", "华东,华东区,江浙沪,宁波"),
]

channels = [
    (1, "App", "app"),
    (2, "官网", "web"),
    (3, "小程序", "mini_program"),
    (4, "线下门店", "offline"),
    (5, "电商平台", "marketplace"),
]

products = [
    ("P001", "声浪 Air 无线耳机", "音频", "声浪", 120, 299),
    ("P002", "云听 Pro 降噪耳机", "音频", "云听", 180, 499),
    ("P003", "声浪 Lite 耳机", "音频", "声浪", 60, 159),
    ("P004", "键行 K87 机械键盘", "键鼠", "键行", 150, 399),
    ("P005", "键行 K68 键盘", "键鼠", "键行", 90, 229),
    ("P006", "视界 27 寸显示器", "显示", "视界", 700, 1299),
    ("P007", "视界 24 寸显示器", "显示", "视界", 450, 899),
    ("P008", "极客 磁吸手机壳", "配件", "极客", 8, 39),
    ("P009", "极客 快充数据线", "配件", "极客", 10, 49),
    ("P010", "轻电 65W 充电器", "配件", "轻电", 45, 129),
    ("P011", "声浪 蓝牙音箱", "音频", "声浪", 100, 259),
    ("P012", "视界 高清摄像头", "显示", "视界", 80, 199),
    ("P013", "极客 平板支架", "配件", "极客", 20, 79),
    ("P014", "键行 无线鼠标", "键鼠", "键行", 50, 149),
    ("P015", "云听 智能手表", "智能穿戴", "云听", 300, 799),
    ("P016", "极客 双频路由器", "网络", "极客", 120, 279),
    ("P017", "轻电 20000mAh 移动电源", "配件", "轻电", 80, 199),
    ("P018", "声浪 USB 麦克风", "音频", "声浪", 150, 359),
    ("P019", "视界 1TB 移动硬盘", "存储", "视界", 280, 599),
    ("P020", "极客 128GB U 盘", "存储", "极客", 30, 89),
]

campaigns = [
    (1, "618 大促 2025", date(2025, 6, 1), date(2025, 6, 20), 5, 50000),
    (2, "双 11 2025", date(2025, 11, 1), date(2025, 11, 11), 1, 80000),
    (3, "年货节 2026", date(2026, 1, 10), date(2026, 1, 25), 3, 30000),
    (4, "618 2026", date(2026, 6, 1), date(2026, 6, 20), 1, 60000),
    (5, "818 2026", date(2026, 8, 1), date(2026, 8, 18), 2, 40000),
    (6, "双 11 2026", date(2026, 11, 1), date(2026, 11, 11), 1, 100000),
]

reps = [
    (1, "王*", 1, None),
    (2, "李*", 2, 1),
    (3, "张*", 3, 1),
    (4, "赵*", 4, 1),
    (5, "陈*", 5, 1),
    (6, "周*", 12, 1),
    (7, "吴*", 6, 1),
    (8, "徐*", 7, 1),
    (9, "孙*", 8, 1),
    (10, "马*", 9, 1),
    (11, "朱*", 10, 1),
    (12, "胡*", 11, 1),
    (13, "郭*", 1, 1),
    (14, "何*", 3, 1),
]
region_reps: dict[int, list[int]] = defaultdict(list)
for rep in reps:
    region_reps[rep[2]].append(rep[0])

surnames = [
    "张", "王", "李", "赵", "陈", "刘", "杨", "黄", "周", "吴",
    "徐", "孙", "胡", "朱", "高", "林", "何", "郭", "马", "罗",
]


def masked_name() -> str:
    return random.choice(surnames) + "*" * random.randint(1, 2)


def masked_phone(index: int) -> str:
    return f"1{random.choice(['3', '5', '8'])}****{index:04d}"


customers = []
for i in range(1, 61):
    cid = f"C{i:03d}"
    if i <= 10:
        region_id = [1, 2, 3, 4, 5, 12, 1, 3, 2, 4][i - 1]
        register_date = date(2025, random.randint(1, 6), random.randint(1, 28))
    elif i <= 50:
        region_id = random.choices(
            list(range(1, 13)),
            weights=[8, 8, 8, 6, 6, 5, 4, 4, 3, 2, 2, 5],
            k=1,
        )[0]
        register_date = START + timedelta(
            days=random.randint(0, (date(2025, 12, 31) - START).days)
        )
    elif i <= 53:
        region_id = random.choice([1, 2, 3, 5, 7, 12])
        register_date = date(2026, 11, 4)
    else:
        region_id = random.choice([1, 2, 3, 5, 7, 9, 12])
        register_date = START + timedelta(
            days=random.randint(0, (date(2025, 12, 31) - START).days)
        )
    customers.append(
        {
            "customer_id": cid,
            "name_masked": masked_name(),
            "region_id": region_id,
            "register_date": register_date,
            "phone_masked": masked_phone(i),
            "segment": "new",
        }
    )

customer_by_id = {customer["customer_id"]: customer for customer in customers}
top_ids = [f"C{i:03d}" for i in range(1, 11)]
top_set = set(top_ids)

# ---------- order slots ----------
month_counts = {
    (2025, 1): 12, (2025, 2): 10, (2025, 3): 14, (2025, 4): 12, (2025, 5): 14,
    (2025, 6): 30, (2025, 7): 12, (2025, 8): 14, (2025, 9): 12, (2025, 10): 14,
    (2025, 11): 40, (2025, 12): 18,
    (2026, 1): 20, (2026, 2): 10, (2026, 3): 14, (2026, 4): 12, (2026, 5): 14,
    (2026, 6): 35, (2026, 7): 16, (2026, 8): 26, (2026, 9): 16, (2026, 10): 50,
    (2026, 11): 20,
}

order_dates: list[date] = []
for (year, month), count in month_counts.items():
    max_day = 5 if (year, month) == (2026, 11) else calendar.monthrange(year, month)[1]
    for _ in range(count):
        order_dates.append(date(year, month, random.randint(1, max_day)))

slots = list(order_dates) + [date(2026, 11, 4)] * 3
available = set(range(len(slots)))


def take(pool: list[int], n: int) -> list[int]:
    candidates = [index for index in pool if index in available]
    chosen = random.sample(candidates, n)
    for index in chosen:
        available.remove(index)
    return chosen


oct_index = [i for i, value in enumerate(slots) if value.year == 2026 and value.month == 10]
nov26_index = [i for i, value in enumerate(slots) if value.year == 2026 and value.month == 11]
nov25_index = [i for i, value in enumerate(slots) if value.year == 2025 and value.month == 11]

assigned: list[tuple[date, str]] = []
for cid in top_ids:
    picks = []
    picks += take(oct_index, 2)
    picks += take(nov26_index, 1)
    picks += take(nov25_index, 1)
    picks += random.sample(list(available), 8)
    for index in picks:
        if index in available:
            available.remove(index)
        assigned.append((slots[index], cid))

reserved_new = [i for i in available if slots[i] == date(2026, 11, 4)]
random.shuffle(reserved_new)
for cid, index in zip(["C051", "C052", "C053"], reserved_new[:3]):
    available.remove(index)
    assigned.append((slots[index], cid))

remaining_customers = [f"C{i:03d}" for i in range(11, 51)] + [
    f"C{i:03d}" for i in range(54, 61)
]
remaining_index = sorted(available)
random.shuffle(remaining_index)
for cid, index in zip(remaining_customers, remaining_index[: len(remaining_customers)]):
    assigned.append((slots[index], cid))
used = set(remaining_index[: len(remaining_customers)])
remaining_index = [index for index in remaining_index if index not in used]

weights = []
for cid in remaining_customers:
    number = int(cid[1:])
    if number <= 20:
        weights.append(3)
    elif number <= 40:
        weights.append(2)
    else:
        weights.append(1)

for index in remaining_index:
    cid = random.choices(remaining_customers, weights=weights, k=1)[0]
    assigned.append((slots[index], cid))

assigned.sort(key=lambda item: item[0])

# ---------- facts ----------
orders = []
items = []
refunds = []
item_seq = 1
refund_seq = 1
seq_by_date: dict[date, int] = defaultdict(int)

for order_date, cid in assigned:
    seq_by_date[order_date] += 1
    order_id = f"ORD{order_date:%Y%m%d}{seq_by_date[order_date]:03d}"
    customer = customer_by_id[cid]
    region_id = customer["region_id"]

    channel_id = random.choices([1, 2, 3, 4, 5], weights=[45, 20, 15, 10, 10], k=1)[0]
    if random.random() < 0.05:
        channel_id = None

    sales_rep_id = random.choice(region_reps[region_id]) if region_reps[region_id] else None
    if random.random() < 0.10:
        sales_rep_id = None

    campaign_id = None
    for campaign in campaigns:
        if campaign[2] <= order_date <= campaign[3] and random.random() < 0.6:
            campaign_id = campaign[0]
            break

    n_items = random.randint(2, 4) if cid in top_set else random.randint(1, 3)
    chosen_products = random.sample(products, n_items)
    order_items = []
    for product in chosen_products:
        quantity = random.randint(1, 2)
        unit_price = round(product[5] * random.uniform(0.85, 1.05), 2)
        item_discount = round(quantity * unit_price * random.uniform(0, 0.08), 2)
        amount = round(quantity * unit_price - item_discount, 2)
        if amount <= 0:
            amount = 0.01
        order_items.append(
            (item_seq, order_id, product[0], quantity, unit_price, item_discount, amount)
        )
        item_seq += 1

    gross = round(sum(item[6] for item in order_items), 2)
    discount = round(gross * random.uniform(0, 0.10), 2)
    net = round(gross - discount, 2)
    if net <= 0:
        net = 0.01

    if order_date >= date(2026, 10, 1):
        status = random.choices(
            ["paid", "shipped", "delivered"], weights=[35, 40, 25], k=1
        )[0]
    else:
        status = random.choices(
            ["paid", "shipped", "delivered", "cancelled"],
            weights=[15, 20, 60, 5],
            k=1,
        )[0]

    refund = None
    if status != "cancelled" and random.random() < 0.14:
        refund_amount = round(net * random.uniform(0.3, 1.0), 2)
        reason = random.choice(
            ["质量问题", "尺码不合适", "不喜欢", "发错货", "物流太慢", None, "其他"]
        )
        refund_status = random.choices(
            ["requested", "approved", "completed", "rejected"],
            weights=[20, 20, 50, 10],
            k=1,
        )[0]
        if order_date.year == 2026 and order_date.month == 10 and random.random() < 0.7:
            max_offset = max(1, (date(2026, 10, 31) - order_date).days)
            refund_date = order_date + timedelta(days=random.randint(1, max_offset))
        else:
            refund_date = order_date + timedelta(days=random.randint(1, 15))
        if refund_date > FACT_END:
            refund_date = FACT_END
        refund = (
            f"RF{refund_seq:05d}",
            order_id,
            refund_amount,
            reason,
            refund_status,
            refund_date,
        )
        refund_seq += 1
        if random.random() < 0.6:
            status = "refunded"

    orders.append(
        {
            "order_id": order_id,
            "customer_id": cid,
            "region_id": region_id,
            "channel_id": channel_id,
            "campaign_id": campaign_id,
            "sales_rep_id": sales_rep_id,
            "date": order_date,
            "gross_amount": gross,
            "discount": discount,
            "net_amount": net,
            "status": status,
            "created_at": (
                f"{order_date.isoformat()} "
                f"{random.randint(8, 22):02d}:{random.randint(0, 59):02d}:00"
            ),
        }
    )
    items.extend(order_items)
    if refund:
        refunds.append(refund)

oct_refund_orders = {
    refund[1]
    for refund in refunds
    if refund[5].year == 2026 and refund[5].month == 10
}
for order in orders:
    if len(oct_refund_orders) >= 6:
        break
    if (
        order["date"].year == 2026
        and order["date"].month == 10
        and order["status"] != "cancelled"
        and order["order_id"] not in oct_refund_orders
    ):
        refund = (
            f"RF{refund_seq:05d}",
            order["order_id"],
            round(order["net_amount"] * random.uniform(0.4, 1.0), 2),
            random.choice(["质量问题", "尺码不合适", "不喜欢", "发错货"]),
            random.choices(["approved", "completed"], weights=[30, 70], k=1)[0],
            date(2026, 10, random.randint(20, 31)),
        )
        refund_seq += 1
        refunds.append(refund)
        oct_refund_orders.add(order["order_id"])
        order["status"] = "refunded"

orders_by_customer: dict[str, list[dict]] = defaultdict(list)
for order in orders:
    orders_by_customer[order["customer_id"]].append(order)

for customer in customers:
    cid = customer["customer_id"]
    history = orders_by_customer.get(cid, [])
    last_order = max(order["date"] for order in history) if history else None
    if cid in top_set:
        customer["segment"] = "vip"
    elif last_order is not None and last_order < date(2026, 7, 8):
        customer["segment"] = "churn"
    elif len(history) >= 2:
        customer["segment"] = "active"
    else:
        customer["segment"] = "new"

# ---------- SQL writer ----------
def q(value):
    if value is None:
        return "NULL"
    if isinstance(value, (int, float)):
        return str(value)
    return "'" + str(value).replace("'", "''") + "'"


def write_insert(table: str, columns: list[str], rows: list[tuple], batch: int = 100) -> str:
    statements = []
    for start in range(0, len(rows), batch):
        chunk = rows[start : start + batch]
        values = ",\n".join(
            "(" + ", ".join(q(value) for value in row) + ")" for row in chunk
        )
        statements.append(
            f"INSERT INTO {table} ({', '.join(columns)}) VALUES\n{values};"
        )
    return "\n\n".join(statements)


date_rows = [
    (
        value.strftime("%Y%m%d"),
        value.isoformat(),
        value.year,
        (value.month - 1) // 3 + 1,
        value.month,
        value.isocalendar()[1],
        value.isoweekday(),
        1 if value in holidays else 0,
    )
    for value in dates
]

customer_rows = [
    (
        customer["customer_id"],
        customer["name_masked"],
        customer["region_id"],
        customer["segment"],
        customer["register_date"].strftime("%Y%m%d"),
        customer["phone_masked"],
    )
    for customer in customers
]

order_rows = [
    (
        order["order_id"],
        order["customer_id"],
        order["region_id"],
        order["channel_id"],
        order["campaign_id"],
        order["sales_rep_id"],
        order["date"].strftime("%Y%m%d"),
        order["gross_amount"],
        order["discount"],
        order["net_amount"],
        order["status"],
        order["created_at"],
    )
    for order in orders
]

refund_rows = [
    (
        refund[0],
        refund[1],
        refund[2],
        refund[3],
        refund[4],
        refund[5].strftime("%Y%m%d"),
    )
    for refund in refunds
]

parts = [
    "-- AskData D1 seed data (SQLite demo, deterministic random.seed(20261105))",
    f"-- date dimension: {START} .. {DIM_END}; facts through {FACT_END}",
    "-- run on a fresh database after schema.sql",
    "",
    "DELETE FROM fact_refunds;",
    "DELETE FROM fact_order_items;",
    "DELETE FROM fact_orders;",
    "DELETE FROM dim_campaigns;",
    "DELETE FROM dim_sales_reps;",
    "DELETE FROM dim_customers;",
    "DELETE FROM dim_products;",
    "DELETE FROM dim_channels;",
    "DELETE FROM dim_regions;",
    "DELETE FROM dim_dates;",
    "",
    write_insert(
        "dim_dates",
        [
            "date_id",
            "date_value",
            "year_num",
            "quarter_num",
            "month_num",
            "week_num",
            "day_of_week",
            "is_holiday",
        ],
        date_rows,
    ),
    write_insert(
        "dim_regions",
        ["region_id", "province", "city", "region_group", "aliases"],
        regions,
    ),
    write_insert(
        "dim_channels",
        ["channel_id", "channel_name", "channel_type"],
        channels,
    ),
    write_insert(
        "dim_products",
        ["product_id", "name", "category", "brand", "cost", "list_price"],
        products,
    ),
    write_insert(
        "dim_customers",
        [
            "customer_id",
            "name_masked",
            "region_id",
            "segment",
            "register_date_id",
            "phone_masked",
        ],
        customer_rows,
    ),
    write_insert(
        "dim_campaigns",
        ["campaign_id", "name", "start_date_id", "end_date_id", "channel_id", "budget"],
        [
            (
                campaign[0],
                campaign[1],
                campaign[2].strftime("%Y%m%d"),
                campaign[3].strftime("%Y%m%d"),
                campaign[4],
                campaign[5],
            )
            for campaign in campaigns
        ],
    ),
    write_insert(
        "dim_sales_reps",
        ["rep_id", "name", "region_id", "manager_id"],
        reps,
    ),
    write_insert(
        "fact_orders",
        [
            "order_id",
            "customer_id",
            "region_id",
            "channel_id",
            "campaign_id",
            "sales_rep_id",
            "date_id",
            "gross_amount",
            "discount",
            "net_amount",
            "status",
            "created_at",
        ],
        order_rows,
        batch=50,
    ),
    write_insert(
        "fact_order_items",
        [
            "item_id",
            "order_id",
            "product_id",
            "quantity",
            "unit_price",
            "discount",
            "amount",
        ],
        items,
    ),
    write_insert(
        "fact_refunds",
        [
            "refund_id",
            "order_id",
            "refund_amount",
            "reason",
            "status",
            "refund_date_id",
        ],
        refund_rows,
        batch=50,
    ),
    "",
]

OUT.write_text("\n".join(parts), encoding="utf-8")

print("seed written:", OUT)
print(
    "dates", len(date_rows),
    "regions", len(regions),
    "channels", len(channels),
    "products", len(products),
)
print(
    "customers", len(customers),
    "campaigns", len(campaigns),
    "reps", len(reps),
)
print("orders", len(orders), "items", len(items), "refunds", len(refunds))
print("status", Counter(order["status"] for order in orders))
print("segments", Counter(customer["segment"] for customer in customers))
print("refund reasons", Counter(refund[3] for refund in refunds))
