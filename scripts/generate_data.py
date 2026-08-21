"""
generate_data.py
-----------------
Generates a synthetic retail sales dataset (2 years, multi-region, multi-category)
that mimics a real-world messy export: missing values, duplicate rows,
inconsistent date formats, and stray whitespace/casing issues.

This stands in for a real Kaggle/company export so the project is fully
reproducible without external downloads.
"""

import numpy as np
import pandas as pd
from faker import Faker
import random

Faker.seed(42)
np.random.seed(42)
random.seed(42)

fake = Faker()

N_CUSTOMERS = 500
N_ORDERS = 9000

regions = ["East", "West", "Central", "South"]
states_by_region = {
    "East": ["New York", "New Jersey", "Massachusetts", "Pennsylvania"],
    "West": ["California", "Washington", "Oregon", "Nevada"],
    "Central": ["Texas", "Illinois", "Michigan", "Ohio"],
    "South": ["Florida", "Georgia", "North Carolina", "Tennessee"],
}

categories = {
    "Furniture": ["Chairs", "Tables", "Bookcases", "Furnishings"],
    "Office Supplies": ["Binders", "Paper", "Storage", "Art", "Labels"],
    "Technology": ["Phones", "Accessories", "Machines", "Copiers"],
}

segments = ["Consumer", "Corporate", "Home Office"]
ship_modes = ["Standard Class", "Second Class", "First Class", "Same Day"]

# --- Build customer master list ---
customers = []
for i in range(1, N_CUSTOMERS + 1):
    region = random.choice(regions)
    customers.append({
        "customer_id": f"CUST-{i:04d}",
        "customer_name": fake.name(),
        "segment": random.choice(segments),
        "region": region,
        "state": random.choice(states_by_region[region]),
    })
customers_df = pd.DataFrame(customers)

# --- Build orders ---
start_date = pd.Timestamp("2023-01-01")
end_date = pd.Timestamp("2024-12-31")
date_range_days = (end_date - start_date).days

rows = []
for i in range(1, N_ORDERS + 1):
    cust = customers_df.sample(1, random_state=i).iloc[0]
    category = random.choice(list(categories.keys()))
    sub_category = random.choice(categories[category])

    order_date = start_date + pd.Timedelta(days=random.randint(0, date_range_days))
    ship_delay = random.randint(1, 7)
    ship_date = order_date + pd.Timedelta(days=ship_delay)

    # base price varies by category, with noise
    base_price = {"Furniture": 250, "Office Supplies": 35, "Technology": 400}[category]
    quantity = random.randint(1, 8)
    unit_price = max(5, np.random.normal(base_price, base_price * 0.3))
    discount = random.choice([0, 0, 0, 0.1, 0.15, 0.2, 0.3])
    sales = round(unit_price * quantity * (1 - discount), 2)

    # profit margin varies, occasionally negative (heavy discount categories)
    margin_pct = np.random.normal(0.15, 0.12)
    if discount >= 0.2:
        margin_pct -= 0.15
    profit = round(sales * margin_pct, 2)

    row = {
        "order_id": f"ORD-{i:06d}",
        "order_date": order_date,
        "ship_date": ship_date,
        "ship_mode": random.choice(ship_modes),
        "customer_id": cust["customer_id"],
        "customer_name": cust["customer_name"],
        "segment": cust["segment"],
        "region": cust["region"],
        "state": cust["state"],
        "category": category,
        "sub_category": sub_category,
        "quantity": quantity,
        "unit_price": round(unit_price, 2),
        "discount": discount,
        "sales": sales,
        "profit": profit,
    }
    rows.append(row)

df = pd.DataFrame(rows)

# ---------------------------------------------------------------
# Inject realistic messiness for the cleaning step of the project
# ---------------------------------------------------------------

# 1. Missing values scattered in a few columns
for col, frac in [("customer_name", 0.01), ("discount", 0.02), ("ship_mode", 0.015), ("profit", 0.01)]:
    idx = df.sample(frac=frac, random_state=1).index
    df.loc[idx, col] = np.nan

# 2. Duplicate rows (simulate double export)
dupes = df.sample(frac=0.01, random_state=2)
df = pd.concat([df, dupes], ignore_index=True)

# 3. Inconsistent date formats (mix of string formats before final export)
def messy_date(d):
    if pd.isna(d):
        return d
    fmt = random.choice(["%Y-%m-%d", "%m/%d/%Y", "%d-%b-%Y"])
    return d.strftime(fmt)

df["order_date"] = df["order_date"].apply(messy_date)
df["ship_date"] = df["ship_date"].apply(messy_date)

# 4. Inconsistent text casing / stray whitespace
df["region"] = df["region"].apply(lambda x: x.upper() if random.random() < 0.05 else x)
df["category"] = df["category"].apply(lambda x: f"  {x} " if random.random() < 0.03 else x)
df["customer_name"] = df["customer_name"].apply(
    lambda x: x.lower() if isinstance(x, str) and random.random() < 0.04 else x
)

# 5. A few negative quantities (data entry errors) to catch in cleaning
neg_idx = df.sample(frac=0.005, random_state=3).index
df.loc[neg_idx, "quantity"] = -df.loc[neg_idx, "quantity"]

# Shuffle rows so it doesn't look artificially ordered
df = df.sample(frac=1, random_state=7).reset_index(drop=True)

df.to_csv("/home/claude/retail-sales-analysis/data/raw/sales_data_raw.csv", index=False)
print(f"Generated {len(df)} rows -> data/raw/sales_data_raw.csv")
print(df.isna().sum())
