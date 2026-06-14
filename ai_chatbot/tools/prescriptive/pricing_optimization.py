# Copyright (c) 2026, Sanjay Kumar and contributors
# For license information, please see license.txt
"""
Pricing Optimisation Tool

Estimates the price elasticity of demand for an item from its historical
monthly average price and quantity, then recommends a profit-maximising price.

Method:
	1. Aggregate Sales Invoice Items by month → (avg_price, total_qty).
	2. Fit log(qty) = a + e · log(price) by ordinary least squares.
	3. e (slope) is the elasticity. R² is reported as confidence.
	4. With marginal cost mc and constant-elasticity demand, profit is
	   maximised at p* = mc · e / (e + 1) when demand is elastic (e < -1).
	   Inelastic (-1 < e < 0) and positive-elasticity cases are flagged.
"""

import math

import frappe
from frappe.query_builder import functions as fn
from frappe.utils import add_months, flt, get_first_day, get_last_day, nowdate

from ai_chatbot.core.session_context import get_company_filter
from ai_chatbot.data.charts import build_bar_chart
from ai_chatbot.data.currency import build_currency_response
from ai_chatbot.tools.common import apply_company_filter as _apply_company_filter
from ai_chatbot.tools.common import primary as _primary
from ai_chatbot.tools.registry import register_tool

_MIN_PRICE_POINTS = 6  # Need at least this many monthly observations to fit elasticity
_MIN_DISTINCT_PRICES = 3  # And at least this much price variation
_MIN_R_SQUARED = 0.3  # Below this we flag the recommendation as low-confidence


def _resolve_item(item_code: str) -> str | None:
	if frappe.db.exists("Item", item_code):
		return item_code
	resolved = frappe.db.get_value("Item", {"item_name": ["like", f"%{item_code}%"]}, "name")
	if resolved:
		return resolved
	return frappe.db.get_value("Item", {"name": ["like", f"%{item_code}%"]}, "name")


def _get_unit_cost(item_code: str) -> float:
	item = frappe.db.get_value(
		"Item",
		item_code,
		["valuation_rate", "last_purchase_rate", "standard_rate"],
		as_dict=True,
	)
	if not item:
		return 0.0
	for field in ("valuation_rate", "last_purchase_rate", "standard_rate"):
		value = flt(item.get(field))
		if value > 0:
			return value
	return 0.0


def _get_monthly_price_qty(item_code: str, company, months_back: int) -> list[dict]:
	"""Return monthly aggregates: [{month, qty, price}, ...] for months with sales."""
	si = frappe.qb.DocType("Sales Invoice")
	sii = frappe.qb.DocType("Sales Invoice Item")
	start_date = get_first_day(add_months(nowdate(), -months_back + 1))
	end_date = get_last_day(nowdate())
	month_expr = fn.DateFormat(si.posting_date, "%Y-%m")

	# Quantity-weighted average price: SUM(stock_qty * rate) / SUM(stock_qty)
	query = (
		frappe.qb.from_(sii)
		.join(si)
		.on(sii.parent == si.name)
		.select(
			month_expr.as_("month"),
			fn.Sum(sii.stock_qty).as_("qty"),
			fn.Sum(sii.stock_qty * sii.rate).as_("revenue"),
		)
		.where(si.docstatus == 1)
		.where(sii.item_code == item_code)
		.where(sii.rate > 0)
		.where(sii.stock_qty > 0)
		.where(si.posting_date >= start_date)
		.where(si.posting_date <= end_date)
	)
	query = _apply_company_filter(query, si, company)
	rows = query.groupby(month_expr).orderby(month_expr).run(as_dict=True)

	result = []
	for r in rows:
		qty = flt(r.qty)
		revenue = flt(r.revenue)
		if qty > 0 and revenue > 0:
			result.append({"month": r.month, "qty": qty, "price": revenue / qty})
	return result


def _ols(xs: list[float], ys: list[float]) -> tuple[float, float, float]:
	"""Ordinary least squares regression of y on x.

	Returns:
		(slope, intercept, r_squared)
	"""
	n = len(xs)
	if n < 2:
		return (0.0, ys[0] if ys else 0.0, 0.0)

	x_mean = sum(xs) / n
	y_mean = sum(ys) / n

	ss_xy = sum((xs[i] - x_mean) * (ys[i] - y_mean) for i in range(n))
	ss_xx = sum((x - x_mean) ** 2 for x in xs)
	ss_yy = sum((y - y_mean) ** 2 for y in ys)

	if ss_xx == 0:
		return (0.0, y_mean, 0.0)

	slope = ss_xy / ss_xx
	intercept = y_mean - slope * x_mean
	r_squared = (ss_xy ** 2) / (ss_xx * ss_yy) if ss_yy > 0 else 0.0
	return (slope, intercept, r_squared)


@register_tool(
	name="optimize_pricing",
	category="prescriptive",
	description=(
		"Estimate price elasticity of demand for an item and recommend a profit-maximising price. "
		"Uses a log-log regression on historical monthly average price vs quantity from Sales "
		"Invoices. Requires sufficient price variation in the history. Returns elasticity, "
		"recommended price, expected volume/margin impact, and a confidence score (R²)."
	),
	parameters={
		"item_code": {
			"type": "string",
			"description": "Item code or item name to analyse (required).",
		},
		"months_back": {
			"type": "integer",
			"description": "How many months of history to use (default 12, max 36).",
		},
		"marginal_cost": {
			"type": "number",
			"description": "Override the marginal cost per unit. Defaults to item valuation rate.",
		},
		"company": {
			"type": "string",
			"description": "Company name. Optional — defaults to the user's default company.",
		},
	},
	doctypes=["Sales Invoice", "Item"],
)
def optimize_pricing(item_code=None, months_back=12, marginal_cost=None, company=None):
	"""Recommend a price based on estimated demand elasticity."""
	if not item_code:
		return {"error": "item_code is required"}

	company = get_company_filter(company)
	months_back = min(max(3, int(months_back or 12)), 36)

	resolved = _resolve_item(item_code)
	if not resolved:
		return {"error": f"Item '{item_code}' not found"}
	item_code = resolved
	item_name = frappe.db.get_value("Item", item_code, "item_name") or item_code

	points = _get_monthly_price_qty(item_code, company, months_back)

	if len(points) < _MIN_PRICE_POINTS:
		return {
			"error": (
				f"Not enough monthly observations to estimate elasticity for '{item_name}'. "
				f"Need at least {_MIN_PRICE_POINTS} months with sales, found {len(points)}."
			),
			"item_code": item_code,
			"item_name": item_name,
			"observations": len(points),
		}

	distinct_prices = {round(p["price"], 4) for p in points}
	if len(distinct_prices) < _MIN_DISTINCT_PRICES:
		return {
			"error": (
				f"Insufficient price variation for '{item_name}' — found {len(distinct_prices)} "
				f"distinct prices. Elasticity needs at least {_MIN_DISTINCT_PRICES}."
			),
			"item_code": item_code,
			"item_name": item_name,
			"distinct_price_points": len(distinct_prices),
		}

	# Log-log regression
	xs = [math.log(p["price"]) for p in points]
	ys = [math.log(p["qty"]) for p in points]
	elasticity, intercept, r_squared = _ols(xs, ys)

	mc = flt(marginal_cost) if marginal_cost else _get_unit_cost(item_code)
	if mc <= 0:
		return {
			"error": (
				f"Cannot determine marginal cost for '{item_name}'. Provide marginal_cost or set "
				"valuation_rate/last_purchase_rate/standard_rate on the Item."
			),
			"item_code": item_code,
			"item_name": item_name,
		}

	current_price = points[-1]["price"]
	current_qty = points[-1]["qty"]

	# Classify elasticity and pick a recommendation
	warning = None
	if elasticity < -1:
		# Elastic — closed-form profit-max price
		recommended_price = mc * elasticity / (elasticity + 1)
		demand_regime = "elastic"
	elif -1 <= elasticity < 0:
		demand_regime = "inelastic"
		# Profit rises monotonically with price. Suggest a cautious 10% bump for testing.
		recommended_price = current_price * 1.10
		warning = (
			"Demand is inelastic (|e| < 1). The mathematical profit-max price is unbounded; "
			"recommendation shown is a conservative 10% test increase. Watch for customer churn."
		)
	else:
		demand_regime = "anomalous"
		recommended_price = current_price
		warning = (
			f"Estimated elasticity is non-negative ({elasticity:.2f}). This is unusual and likely "
			"indicates noisy data, confounding factors (promotions, seasonality), or insufficient "
			"history. Do not act on this recommendation."
		)

	# Expected impact (constant-elasticity model): qty ratio = (p_new/p_old)^e
	price_change_pct = (recommended_price - current_price) / current_price * 100
	if elasticity < 0 and recommended_price > 0 and current_price > 0:
		qty_ratio = (recommended_price / current_price) ** elasticity
		expected_qty = current_qty * qty_ratio
		expected_volume_change_pct = (qty_ratio - 1) * 100
	else:
		expected_qty = current_qty
		expected_volume_change_pct = 0.0

	expected_current_margin = (current_price - mc) * current_qty
	expected_new_margin = (recommended_price - mc) * expected_qty
	expected_margin_change = expected_new_margin - expected_current_margin

	confidence_label = (
		"high" if r_squared >= 0.6 else "medium" if r_squared >= _MIN_R_SQUARED else "low"
	)
	if confidence_label == "low" and not warning:
		warning = (
			f"R² is {r_squared:.2f} — the relationship between price and quantity is weak in this "
			"data. Treat the recommendation as exploratory."
		)

	echart = build_bar_chart(
		title=f"Pricing — {item_name}",
		categories=["Current Price", "Marginal Cost", "Recommended Price"],
		series_data=[round(current_price, 2), round(mc, 2), round(recommended_price, 2)],
		y_axis_name="Price",
		series_name="Price",
	)

	action = (
		f"Move price from {round(current_price, 2)} to {round(recommended_price, 2)} "
		f"({round(price_change_pct, 1):+}%)"
	)

	data = {
		"item_code": item_code,
		"item_name": item_name,
		"observations": len(points),
		"distinct_price_points": len(distinct_prices),
		"elasticity": flt(elasticity, 4),
		"r_squared": flt(r_squared, 4),
		"intercept": flt(intercept, 4),
		"demand_regime": demand_regime,
		"current_price": flt(current_price, 2),
		"current_monthly_qty": flt(current_qty, 2),
		"marginal_cost": flt(mc, 2),
		"recommended_price": flt(recommended_price, 2),
		"price_change_pct": flt(price_change_pct, 2),
		"expected_volume_change_pct": flt(expected_volume_change_pct, 2),
		"expected_new_monthly_qty": flt(expected_qty, 2),
		"expected_margin_change_per_month": flt(expected_margin_change, 2),
		"confidence": confidence_label,
		"warning": warning,
		"action": action,
		"echart_option": echart,
	}
	return build_currency_response(data, _primary(company))
