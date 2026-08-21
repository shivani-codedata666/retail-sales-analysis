"""
run_sql_analysis.py
--------------------
Loads the cleaned CSV into a local SQLite database and executes each
query in sql/analysis_queries.sql, printing results. This both validates
the SQL and lets us generate a results snapshot for documentation.
"""

import sqlite3
import pandas as pd
import re

CLEAN_PATH = "/home/claude/retail-sales-analysis/data/cleaned/sales_data_cleaned.csv"
SQL_PATH = "/home/claude/retail-sales-analysis/sql/analysis_queries.sql"
DB_PATH = "/home/claude/retail-sales-analysis/data/cleaned/sales.db"

df = pd.read_csv(CLEAN_PATH)

conn = sqlite3.connect(DB_PATH)
df.to_sql("sales", conn, if_exists="replace", index=False)

with open(SQL_PATH, "r") as f:
    sql_text = f.read()

# split into individual statements, keep their leading comment as a title
blocks = re.split(r"\n(?=-- \d+\.)", sql_text)

for block in blocks:
    block = block.strip()
    if not block:
        continue
    title_match = re.match(r"-- (\d+\..*)", block)
    title = title_match.group(1) if title_match else "Query"
    query = "\n".join(line for line in block.split("\n") if not line.strip().startswith("--"))
    query = query.strip()
    if not query:
        continue
    print("=" * 70)
    print(title)
    print("=" * 70)
    try:
        result = pd.read_sql_query(query, conn)
        print(result.to_string(index=False))
    except Exception as e:
        print(f"ERROR: {e}")
    print()

conn.close()
