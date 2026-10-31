"""Canonical finance metric definitions shared by agents, SQL, and UI."""
METRICS = {
    "revenue": "SUM(revenue)",
    "cost": "SUM(cost)",
    "gross_profit": "SUM(revenue) - SUM(cost)",
    "gross_margin": "(SUM(revenue) - SUM(cost)) / NULLIF(SUM(revenue), 0)",
}

DEFINITIONS = """Revenue is the sum of fact_finance.revenue. Cost is the sum of fact_finance.cost.
Gross profit = revenue - cost. Gross margin = gross profit / revenue; report as percent.
Revenue, cost and gross profit are additive. Gross margin must be recomputed from totals,
never averaged across groups. Fiscal quarters follow calendar quarters. Amounts use the selected dataset's native currency (USD or INR)."""
