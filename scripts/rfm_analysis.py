"""
rfm_analysis.py
----------------
Performs RFM (Recency, Frequency, Monetary) segmentation on the cleaned
sales data and buckets customers into actionable marketing segments.
"""

import pandas as pd

CLEAN_PATH = "/home/claude/retail-sales-analysis/data/cleaned/sales_data_cleaned.csv"
OUT_PATH = "/home/claude/retail-sales-analysis/data/cleaned/customer_rfm_segments.csv"

df = pd.read_csv(CLEAN_PATH, parse_dates=["order_date"])

snapshot_date = df["order_date"].max() + pd.Timedelta(days=1)

rfm = df.groupby("customer_id").agg(
    customer_name=("customer_name", "first"),
    recency=("order_date", lambda x: (snapshot_date - x.max()).days),
    frequency=("order_id", "nunique"),
    monetary=("sales", "sum"),
).reset_index()

# Score each dimension 1-5 using quintiles (5 = best)
rfm["r_score"] = pd.qcut(rfm["recency"], 5, labels=[5, 4, 3, 2, 1]).astype(int)
rfm["f_score"] = pd.qcut(rfm["frequency"].rank(method="first"), 5, labels=[1, 2, 3, 4, 5]).astype(int)
rfm["m_score"] = pd.qcut(rfm["monetary"], 5, labels=[1, 2, 3, 4, 5]).astype(int)

rfm["rfm_score"] = rfm["r_score"] + rfm["f_score"] + rfm["m_score"]


def segment_customer(row):
    r, f, m = row["r_score"], row["f_score"], row["m_score"]
    if r >= 4 and f >= 4 and m >= 4:
        return "Champions"
    elif r >= 3 and f >= 3:
        return "Loyal Customers"
    elif r >= 4 and f <= 2:
        return "New / Promising"
    elif r <= 2 and f >= 3:
        return "At Risk"
    elif r <= 2 and f <= 2 and m <= 2:
        return "Lost / Low Value"
    else:
        return "Needs Attention"


rfm["segment"] = rfm.apply(segment_customer, axis=1)

rfm = rfm.sort_values("rfm_score", ascending=False).reset_index(drop=True)
rfm.to_csv(OUT_PATH, index=False)

print(f"Segmented {len(rfm)} customers")
print("\nSegment distribution:")
summary = rfm.groupby("segment").agg(
    customers=("customer_id", "count"),
    avg_monetary=("monetary", "mean"),
    avg_frequency=("frequency", "mean"),
    avg_recency=("recency", "mean"),
).round(1).sort_values("avg_monetary", ascending=False)
print(summary)
print(f"\nSaved -> {OUT_PATH}")
