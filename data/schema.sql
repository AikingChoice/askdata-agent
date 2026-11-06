-- AskData demo schema (SQLite/Postgres portable subset)
-- date_id format: YYYYMMDD
-- IDs are explicit; seed data supplies values.

CREATE TABLE IF NOT EXISTS dim_dates (
    date_id INTEGER PRIMARY KEY,
    date_value DATE NOT NULL,
    year_num INTEGER NOT NULL,
    quarter_num INTEGER NOT NULL,
    month_num INTEGER NOT NULL,
    week_num INTEGER NOT NULL,
    day_of_week INTEGER NOT NULL,
    is_holiday INTEGER NOT NULL DEFAULT 0 CHECK (is_holiday IN (0, 1))
);

CREATE TABLE IF NOT EXISTS dim_regions (
    region_id INTEGER PRIMARY KEY,
    province TEXT NOT NULL,
    city TEXT,
    region_group TEXT NOT NULL CHECK (region_group IN ('华东','华北','华南','华中','西南','西北','东北')),
    aliases TEXT
);

CREATE TABLE IF NOT EXISTS dim_channels (
    channel_id INTEGER PRIMARY KEY,
    channel_name TEXT NOT NULL,
    channel_type TEXT NOT NULL CHECK (channel_type IN ('app','web','mini_program','offline','marketplace'))
);

CREATE TABLE IF NOT EXISTS dim_products (
    product_id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    category TEXT NOT NULL,
    brand TEXT,
    cost NUMERIC(12,2) NOT NULL DEFAULT 0,
    list_price NUMERIC(12,2) NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS dim_customers (
    customer_id TEXT PRIMARY KEY,
    name_masked TEXT NOT NULL,
    region_id INTEGER NOT NULL,
    segment TEXT NOT NULL CHECK (segment IN ('new','active','vip','churn')),
    register_date_id INTEGER NOT NULL,
    phone_masked TEXT,
    FOREIGN KEY (region_id) REFERENCES dim_regions(region_id),
    FOREIGN KEY (register_date_id) REFERENCES dim_dates(date_id)
);

CREATE TABLE IF NOT EXISTS dim_campaigns (
    campaign_id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    start_date_id INTEGER NOT NULL,
    end_date_id INTEGER NOT NULL,
    channel_id INTEGER,
    budget NUMERIC(12,2) DEFAULT 0,
    FOREIGN KEY (start_date_id) REFERENCES dim_dates(date_id),
    FOREIGN KEY (end_date_id) REFERENCES dim_dates(date_id),
    FOREIGN KEY (channel_id) REFERENCES dim_channels(channel_id)
);

CREATE TABLE IF NOT EXISTS dim_sales_reps (
    rep_id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    region_id INTEGER NOT NULL,
    manager_id INTEGER,
    FOREIGN KEY (region_id) REFERENCES dim_regions(region_id)
);

CREATE TABLE IF NOT EXISTS fact_orders (
    order_id TEXT PRIMARY KEY,
    customer_id TEXT NOT NULL,
    region_id INTEGER NOT NULL,
    channel_id INTEGER,
    campaign_id INTEGER,
    sales_rep_id INTEGER,
    date_id INTEGER NOT NULL,
    gross_amount NUMERIC(12,2) NOT NULL,
    discount NUMERIC(12,2) NOT NULL DEFAULT 0,
    net_amount NUMERIC(12,2) NOT NULL,
    status TEXT NOT NULL CHECK (status IN ('paid','shipped','delivered','cancelled','refunded')),
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (customer_id) REFERENCES dim_customers(customer_id),
    FOREIGN KEY (region_id) REFERENCES dim_regions(region_id),
    FOREIGN KEY (channel_id) REFERENCES dim_channels(channel_id),
    FOREIGN KEY (campaign_id) REFERENCES dim_campaigns(campaign_id),
    FOREIGN KEY (sales_rep_id) REFERENCES dim_sales_reps(rep_id),
    FOREIGN KEY (date_id) REFERENCES dim_dates(date_id)
);

CREATE TABLE IF NOT EXISTS fact_order_items (
    item_id INTEGER PRIMARY KEY,
    order_id TEXT NOT NULL,
    product_id TEXT NOT NULL,
    quantity INTEGER NOT NULL CHECK (quantity > 0),
    unit_price NUMERIC(12,2) NOT NULL,
    discount NUMERIC(12,2) NOT NULL DEFAULT 0,
    amount NUMERIC(12,2) NOT NULL,
    FOREIGN KEY (order_id) REFERENCES fact_orders(order_id),
    FOREIGN KEY (product_id) REFERENCES dim_products(product_id)
);

CREATE TABLE IF NOT EXISTS fact_refunds (
    refund_id TEXT PRIMARY KEY,
    order_id TEXT NOT NULL,
    refund_amount NUMERIC(12,2) NOT NULL CHECK (refund_amount >= 0),
    reason TEXT,
    status TEXT NOT NULL CHECK (status IN ('requested','approved','rejected','completed')),
    refund_date_id INTEGER NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (order_id) REFERENCES fact_orders(order_id),
    FOREIGN KEY (refund_date_id) REFERENCES dim_dates(date_id)
);

CREATE INDEX IF NOT EXISTS idx_orders_date ON fact_orders(date_id);
CREATE INDEX IF NOT EXISTS idx_orders_region ON fact_orders(region_id);
CREATE INDEX IF NOT EXISTS idx_orders_channel ON fact_orders(channel_id);
CREATE INDEX IF NOT EXISTS idx_orders_customer ON fact_orders(customer_id);
CREATE INDEX IF NOT EXISTS idx_orders_status ON fact_orders(status);

CREATE INDEX IF NOT EXISTS idx_items_order ON fact_order_items(order_id);
CREATE INDEX IF NOT EXISTS idx_items_product ON fact_order_items(product_id);

CREATE INDEX IF NOT EXISTS idx_refunds_order ON fact_refunds(order_id);
CREATE INDEX IF NOT EXISTS idx_refunds_date ON fact_refunds(refund_date_id);
CREATE INDEX IF NOT EXISTS idx_refunds_status ON fact_refunds(status);

CREATE INDEX IF NOT EXISTS idx_customers_region ON dim_customers(region_id);
CREATE INDEX IF NOT EXISTS idx_customers_register ON dim_customers(register_date_id);

-- Seed data: see data/seed.sql (D1)
