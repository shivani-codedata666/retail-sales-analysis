"""
clean_data.py
-------------
Cleans the raw retail sales export and writes an analysis-ready CSV.

Issues handled:
  1. Inconsistent date formats (YYYY-MM-DD, MM/DD/YYYY, DD-Mon-YYYY)
  2. Duplicate rows
  3. Missing values (ship_mode, customer_name, discount, profit)
  4. Inconsistent text casing / stray whitespace
  5. Negative quantities (data entry errors)
"""

import pandas as pd
import numpy as np

RAW_PATH = "/home/claude/retail-sales-analysis/data/raw/sales_data_raw.csv"
CLEAN_PATH = "/home/claude/retail-sales-analysis/data/cleaned/sales_data_cleaned.csv"

df = pd.read_csv(RAW_PATH)
print(f"Raw rows: {len(df)}")

# 1. Parse mixed-format dates
def parse_mixed_date(series):
    return pd.to_datetime(series, format="mixed", dayfirst=False, errors="coerce")

df["order_date"] = parse_mixed_date(df["order_date"])
df["ship_date"] = parse_mixed_date(df["ship_date"])

# 2. Drop exact duplicate rows
before = len(df)
df = df.drop_duplicates()
print(f"Dropped {before - len(df)} duplicate rows")

# 3. Standardize text columns (trim whitespace, fix casing)
text_cols = ["region", "state", "category", "sub_category", "segment", "ship_mode", "customer_name"]
for col in text_cols:
    df[col] = df[col].astype(str).str.strip()
    df[col] = df[col].replace("nan", np.nan)

df["region"] = df["region"].str.title()
df["category"] = df["category"].str.title()
df["customer_name"] = df["customer_name"].str.title()

# 4. Handle missing values
# ship_mode: fill with the most common mode (mode imputation is reasonable for a low-missing categorical field)
df["ship_mode"] = df["ship_mode"].fillna(df["ship_mode"].mode()[0])

# customer_name: recover from customer_id lookup where possible, else flag as Unknown
name_lookup = df.dropna(subset=["customer_name"]).drop_duplicates("customer_id").set_index("customer_id")["customer_name"]
df["customer_name"] = df["customer_name"].fillna(df["customer_id"].map(name_lookup))
df["customer_name"] = df["customer_name"].fillna("Unknown")

# discount: assume missing means no discount was applied at checkout
df["discount"] = df["discount"].fillna(0)

# profit: recompute from sales using the category's median margin rather than dropping rows
df["margin_pct"] = df["profit"] / df["sales"]
category_median_margin = df.groupby("category")["margin_pct"].transform("median")
df["profit"] = df["profit"].fillna(df["sales"] * category_median_margin)
df = df.drop(columns=["margin_pct"])

# 5. Fix negative quantities (data entry sign errors) -> take absolute value
neg_count = (df["quantity"] < 0).sum()
df["quantity"] = df["quantity"].abs()
print(f"Corrected {neg_count} negative quantity values")

# 6. Drop rows where dates failed to parse or core fields are still missing
before = len(df)
df = df.dropna(subset=["order_date", "ship_date", "sales"])
print(f"Dropped {before - len(df)} rows with unparseable dates")

# 7. Derived columns useful for analysis
df["order_year"] = df["order_date"].dt.year
df["order_month"] = df["order_date"].dt.to_period("M").astype(str)
df["days_to_ship"] = (df["ship_date"] - df["order_date"]).dt.days
df["profit_margin"] = (df["profit"] / df["sales"]).round(4)

df = df.sort_values("order_date").reset_index(drop=True)

df.to_csv(CLEAN_PATH, index=False)
print(f"\nClean rows: {len(df)}")
print(f"Saved -> {CLEAN_PATH}")
print("\nRemaining nulls:")
print(df.isna().sum()[df.isna().sum() > 0])
