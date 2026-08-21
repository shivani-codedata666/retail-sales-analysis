-- ============================================================
-- analysis_queries.sql
-- Retail Sales Performance Analysis
-- Table: sales  (loaded from data/cleaned/sales_data_cleaned.csv)
-- ============================================================

-- 1. Overall KPIs
SELECT
    ROUND(SUM(sales), 2)  AS total_sales,
    ROUND(SUM(profit), 2) AS total_profit,
    ROUND(SUM(profit) * 100.0 / SUM(sales), 2) AS overall_margin_pct,
    COUNT(DISTINCT order_id) AS total_orders,
    COUNT(DISTINCT customer_id) AS total_customers
FROM sales;

-- 2. Monthly sales & profit trend
SELECT
    order_month,
    ROUND(SUM(sales), 2)  AS monthly_sales,
    ROUND(SUM(profit), 2) AS monthly_profit
FROM sales
GROUP BY order_month
ORDER BY order_month;

-- 3. Regional performance — sales, profit, margin
SELECT
    region,
    ROUND(SUM(sales), 2)  AS total_sales,
    ROUND(SUM(profit), 2) AS total_profit,
    ROUND(SUM(profit) * 100.0 / SUM(sales), 2) AS margin_pct
FROM sales
GROUP BY region
ORDER BY total_sales DESC;

-- 4. Category / sub-category breakdown — flag categories with high sales but low margin
SELECT
    category,
    sub_category,
    ROUND(SUM(sales), 2)  AS total_sales,
    ROUND(SUM(profit), 2) AS total_profit,
    ROUND(SUM(profit) * 100.0 / SUM(sales), 2) AS margin_pct
FROM sales
GROUP BY category, sub_category
ORDER BY total_sales DESC;

-- 5. Impact of discount tiers on profit margin
SELECT
    CASE
        WHEN discount = 0 THEN '0% (no discount)'
        WHEN discount <= 0.15 THEN '1-15%'
        WHEN discount <= 0.25 THEN '16-25%'
        ELSE '26%+'
    END AS discount_band,
    ROUND(AVG(profit_margin) * 100, 2) AS avg_margin_pct,
    ROUND(SUM(sales), 2) AS total_sales,
    COUNT(*) AS order_lines
FROM sales
GROUP BY discount_band
ORDER BY discount_band;

-- 6. Top 10 customers by revenue
SELECT
    customer_id,
    customer_name,
    ROUND(SUM(sales), 2) AS total_sales,
    COUNT(DISTINCT order_id) AS num_orders
FROM sales
GROUP BY customer_id, customer_name
ORDER BY total_sales DESC
LIMIT 10;

-- 7. Customer repeat-purchase rate
SELECT
    COUNT(DISTINCT CASE WHEN order_count > 1 THEN customer_id END) * 100.0
        / COUNT(DISTINCT customer_id) AS repeat_customer_pct
FROM (
    SELECT customer_id, COUNT(DISTINCT order_id) AS order_count
    FROM sales
    GROUP BY customer_id
) t;

-- 8. Average shipping delay by ship mode (operations angle)
SELECT
    ship_mode,
    ROUND(AVG(days_to_ship), 2) AS avg_days_to_ship,
    COUNT(*) AS order_lines
FROM sales
GROUP BY ship_mode
ORDER BY avg_days_to_ship;

-- 9. Segment performance (Consumer / Corporate / Home Office)
SELECT
    segment,
    ROUND(SUM(sales), 2)  AS total_sales,
    ROUND(SUM(profit), 2) AS total_profit,
    ROUND(SUM(profit) * 100.0 / SUM(sales), 2) AS margin_pct
FROM sales
GROUP BY segment
ORDER BY total_sales DESC;

-- 10. Loss-making sub-categories (negative total profit) — direct action items
SELECT
    category,
    sub_category,
    ROUND(SUM(sales), 2)  AS total_sales,
    ROUND(SUM(profit), 2) AS total_profit
FROM sales
GROUP BY category, sub_category
HAVING SUM(profit) < 0
ORDER BY total_profit ASC;
