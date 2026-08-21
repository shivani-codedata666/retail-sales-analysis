"""
make_visuals.py
----------------
Generates all chart images used in the README and notebook.
"""

import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import seaborn as sns

sns.set_theme(style="whitegrid", palette="deep")
plt.rcParams["figure.dpi"] = 120

CLEAN_PATH = "/home/claude/retail-sales-analysis/data/cleaned/sales_data_cleaned.csv"
RFM_PATH = "/home/claude/retail-sales-analysis/data/cleaned/customer_rfm_segments.csv"
VIS_DIR = "/home/claude/retail-sales-analysis/visuals"

df = pd.read_csv(CLEAN_PATH, parse_dates=["order_date"])
rfm = pd.read_csv(RFM_PATH)

# 1. Monthly sales & profit trend
monthly = df.groupby("order_month").agg(sales=("sales", "sum"), profit=("profit", "sum")).reset_index()
fig, ax1 = plt.subplots(figsize=(11, 5))
ax1.bar(monthly["order_month"], monthly["sales"], color="#4C72B0", label="Sales")
ax1.set_ylabel("Sales ($)")
ax1.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"${x/1000:.0f}K"))
ax1.set_xticklabels(monthly["order_month"], rotation=90, fontsize=7)
ax2 = ax1.twinx()
ax2.plot(monthly["order_month"], monthly["profit"], color="#DD8452", marker="o", linewidth=2, label="Profit")
ax2.set_ylabel("Profit ($)")
ax2.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"${x/1000:.0f}K"))
fig.legend(loc="upper right", bbox_to_anchor=(0.9, 0.95))
plt.title("Monthly Sales & Profit Trend (2023–2024)")
fig.tight_layout()
fig.savefig(f"{VIS_DIR}/01_monthly_sales_profit_trend.png")
plt.close(fig)

# 2. Regional performance
regional = df.groupby("region").agg(sales=("sales", "sum"), profit=("profit", "sum")).reset_index()
regional["margin_pct"] = regional["profit"] / regional["sales"] * 100
regional = regional.sort_values("sales", ascending=False)
fig, ax = plt.subplots(figsize=(8, 5))
bars = ax.bar(regional["region"], regional["sales"], color="#55A868")
ax.set_ylabel("Total Sales ($)")
ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"${x/1e6:.1f}M"))
for bar, margin in zip(bars, regional["margin_pct"]):
    ax.text(bar.get_x() + bar.get_width()/2, bar.get_height(), f"{margin:.1f}% margin",
            ha="center", va="bottom", fontsize=9)
plt.title("Sales by Region (label = profit margin %)")
fig.tight_layout()
fig.savefig(f"{VIS_DIR}/02_regional_performance.png")
plt.close(fig)

# 3. Discount band vs margin — the headline insight
discount_bins = [-0.01, 0, 0.15, 0.25, 1]
discount_labels = ["0% (no discount)", "1-15%", "16-25%", "26%+"]
df["discount_band"] = pd.cut(df["discount"], bins=discount_bins, labels=discount_labels)
disc = df.groupby("discount_band", observed=True)["profit_margin"].mean().reset_index()
disc["profit_margin"] *= 100
fig, ax = plt.subplots(figsize=(8, 5))
colors = ["#55A868" if v > 5 else "#C44E52" for v in disc["profit_margin"]]
ax.bar(disc["discount_band"], disc["profit_margin"], color=colors)
ax.axhline(0, color="black", linewidth=0.8)
ax.set_ylabel("Average Profit Margin (%)")
ax.set_xlabel("Discount Band")
plt.title("Discounting Above 15% Erodes Profit Margin")
for i, v in enumerate(disc["profit_margin"]):
    ax.text(i, v + (0.5 if v >= 0 else -1.5), f"{v:.1f}%", ha="center", fontweight="bold")
fig.tight_layout()
fig.savefig(f"{VIS_DIR}/03_discount_vs_margin.png")
plt.close(fig)

# 4. Category / sub-category sales
cat = df.groupby(["category", "sub_category"]).agg(sales=("sales", "sum")).reset_index()
cat = cat.sort_values("sales", ascending=True)
fig, ax = plt.subplots(figsize=(9, 6))
palette = {"Technology": "#4C72B0", "Furniture": "#DD8452", "Office Supplies": "#55A868"}
colors = cat["category"].map(palette)
ax.barh(cat["sub_category"], cat["sales"], color=colors)
ax.set_xlabel("Total Sales ($)")
ax.xaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"${x/1e3:.0f}K"))
plt.title("Sales by Sub-Category")
handles = [plt.Rectangle((0,0),1,1, color=c) for c in palette.values()]
ax.legend(handles, palette.keys(), loc="lower right")
fig.tight_layout()
fig.savefig(f"{VIS_DIR}/04_subcategory_sales.png")
plt.close(fig)

# 5. RFM segment distribution
seg_summary = rfm.groupby("segment").agg(
    customers=("customer_id", "count"),
    avg_monetary=("monetary", "mean")
).reset_index().sort_values("avg_monetary", ascending=False)

fig, axes = plt.subplots(1, 2, figsize=(13, 5))
sns.barplot(data=seg_summary, x="segment", y="customers", ax=axes[0], palette="viridis", hue="segment", legend=False)
axes[0].set_title("Customer Count by RFM Segment")
axes[0].set_xlabel("")
axes[0].tick_params(axis="x", rotation=30)

sns.barplot(data=seg_summary, x="segment", y="avg_monetary", ax=axes[1], palette="magma", hue="segment", legend=False)
axes[1].set_title("Average Customer Value by RFM Segment")
axes[1].set_xlabel("")
axes[1].yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"${x/1e3:.0f}K"))
axes[1].tick_params(axis="x", rotation=30)

fig.tight_layout()
fig.savefig(f"{VIS_DIR}/05_rfm_segments.png")
plt.close(fig)

# 6. Recency vs Frequency scatter colored by segment (classic RFM view)
fig, ax = plt.subplots(figsize=(9, 6))
sns.scatterplot(data=rfm, x="recency", y="frequency", hue="segment", size="monetary",
                 sizes=(20, 200), alpha=0.7, ax=ax, palette="tab10")
ax.set_xlabel("Recency (days since last order)")
ax.set_ylabel("Frequency (number of orders)")
plt.title("Customer Segments: Recency vs Frequency (bubble size = spend)")
ax.legend(bbox_to_anchor=(1.02, 1), loc="upper left", fontsize=8)
fig.tight_layout()
fig.savefig(f"{VIS_DIR}/06_rfm_scatter.png")
plt.close(fig)

print("All visuals saved to", VIS_DIR)
