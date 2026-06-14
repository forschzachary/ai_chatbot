# Copyright (c) 2026, Sanjay Kumar and contributors
# For license information, please see license.txt
"""
Inventory Optimisation Tool

Recommends Economic Order Quantity (EOQ), safety stock, and reorder point
for an item using its historical monthly demand and Item master data.

Formulas:
	EOQ            = sqrt((2 · D · S) / H)
	Safety Stock   = z · sigma_monthly · sqrt(L / 30)
	Reorder Point  = (D / 30) · L + Safety Stock

Where:
	D = annual demand (units)
	S = fixed cost per order (currency)
	H = annual holding cost per unit = unit_cost · holding_cost_pct
	z = service level factor (1.28=90%, 1.65=95%, 2.33=99%)
	sigma = standard deviation of monthly demand
	L = lead time (days)
"""

import math

import frappe
from frappe.query_builder import functions as fn
from frappe.utils import add_months, flt, get_first_day, get_last_day, nowdate

from ai_chatbot.core.constants import MIN_FORECAST_HISTORY
from ai_chatbot.core.session_context import get_company_filter
from ai_chatbot.data.charts import build_bar_chart
from ai_chatbot.data.currency import build_currency_response
from ai_chatbot.data.forecasting import _mean, _std, fill_month_gaps
from ai_chatbot.tools.common import apply_company_filter as _apply_company_filter
from ai_chatbot.tools.common import primary as _primary
from ai_chatbot.tools.registry import register_tool

# Service-level → z-score lookup
_SERVICE_LEVEL_Z = {
	"90": 1.28,
	"95": 1.65,
	"99": 2.33,
}

# Defaults (overridable per call)
_DEFAULT_ORDER_COST = 50.0
_DEFAULT_HOLDING_COST_PCT = 0.25  # 25% of unit cost per year
_DEFAULT_LEAD_TIME_DAYS = 7


def _get_monthly_demand(item_code: str, company, months_back: int = 12) -> list[float]:
	"""Query monthly sold quantity for an item from Sales Invoice Item."""
	si = frappe.qb.DocType("Sales Invoice")
	sii = frappe.qb.DocType("Sales Invoice Item")
	start_date = get_first_day(add_months(nowdate(), -months_back + 1))
	end_date = get_last_day(nowdate())
	month_expr = fn.DateFormat(si.posting_date, "%Y-%m")

	query = (
		frappe.qb.from_(sii)
		.join(si)
		.on(sii.parent == si.name)
		.select(
			month_expr.as_("month"),
			fn.Sum(sii.stock_qty).as_("total_qty"),
		)
		.where(si.docstatus == 1)
		.where(sii.item_code == item_code)
		.where(si.posting_date >= start_date)
		.where(si.posting_date <= end_date)
	)
	query = _apply_company_filter(query, si, company)
	rows = query.groupby(month_expr).orderby(month_expr).run(as_dict=True)

	start_month = (
		f"{start_date.year:04d}-{start_date.month:02d}"
		if hasattr(start_date, "year")
		else str(start_date)[:7]
	)
	_, values = fill_month_gaps(rows, "month", "total_qty", start_month, months_back)
	return values


def _resolve_item(item_code: str) -> str | None:
	"""Resolve item_code by exact match, then fuzzy item_name match."""
	if frappe.db.exists("Item", item_code):
		return item_code
	resolved = frappe.db.get_value("Item", {"item_name": ["like", f"%{item_code}%"]}, "name")
	if resolved:
		return resolved
	return frappe.db.get_value("Item", {"name": ["like", f"%{item_code}%"]}, "name")


def _get_unit_cost(item_code: str) -> float:
	"""Get a per-unit cost for the item.

	Priority: valuation_rate → last_purchase_rate → standard_rate.
	"""
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


def _get_current_stock(item_code: str, company) -> float:
	"""Sum actual_qty across all warehouses for the given company."""
	bin_dt = frappe.qb.DocType("Bin")
	wh = frappe.qb.DocType("Warehouse")
	query = (
		frappe.qb.from_(bin_dt)
		.join(wh)
		.on(bin_dt.warehouse == wh.name)
		.select(fn.Sum(bin_dt.actual_qty).as_("qty"))
		.where(bin_dt.item_code == item_code)
	)
	query = _apply_company_filter(query, wh, company)
	rows = query.run(as_dict=True)
	return flt(rows[0].qty) if rows and rows[0].qty else 0.0


def _stockout_risk_label(current_stock: float, reorder_point: float, safety_stock: float) -> str:
	"""Qualitative stockout risk based on current stock vs reorder point."""
	if reorder_point <= 0:
		return "unknown"
	if current_stock <= safety_stock:
		return "high"
	if current_stock <= reorder_point:
		return "medium"
	return "low"


@register_tool(
	name="optimize_inventory",
	category="prescriptive",
	description=(
		"Recommend optimal reorder quantity (EOQ), safety stock, and reorder point for an item. "
		"Uses historical monthly demand from Sales Invoices, item lead time, valuation rate, "
		"and configurable order/holding cost assumptions. Returns expected annual carrying and "
		"order costs plus a qualitative stockout risk for current stock."
	),
	parameters={
		"item_code": {
			"type": "string",
			"description": "Item code or item name to optimise (required).",
		},
		"service_level": {
			"type": "string",
			"description": "Target service level: '90', '95' (default), or '99'.",
		},
		"order_cost": {
			"type": "number",
			"description": "Fixed cost per purchase order. Defaults to 50.",
		},
		"holding_cost_pct": {
			"type": "number",
			"description": "Annual holding cost as a fraction of unit cost (e.g. 0.25 = 25%). Default 0.25.",
		},
		"lead_time_days": {
			"type": "integer",
			"description": "Override the item's lead_time_days. Optional.",
		},
		"company": {
			"type": "string",
			"description": "Company name. Optional — defaults to the user's default company.",
		},
	},
	doctypes=["Sales Invoice", "Item", "Bin"],
)
def optimize_inventory(
	item_code=None,
	service_level="95",
	order_cost=None,
	holding_cost_pct=None,
	lead_time_days=None,
	company=None,
):
	"""Compute EOQ, safety stock, and reorder point for an item."""
	if not item_code:
		return {"error": "item_code is required"}

	company = get_company_filter(company)

	resolved = _resolve_item(item_code)
	if not resolved:
		return {"error": f"Item '{item_code}' not found"}
	item_code = resolved
	item_name = frappe.db.get_value("Item", item_code, "item_name") or item_code

	monthly_demand = _get_monthly_demand(item_code, company)
	# Trim leading zero months — they distort sigma and mean
	first_nonzero = next((i for i, v in enumerate(monthly_demand) if v > 0), len(monthly_demand))
	monthly_demand = monthly_demand[first_nonzero:]

	if len(monthly_demand) < MIN_FORECAST_HISTORY:
		return {
			"error": (
				f"Insufficient sales history for '{item_name}'. "
				f"Need at least {MIN_FORECAST_HISTORY} months of demand, found {len(monthly_demand)}."
			),
			"item_code": item_code,
			"item_name": item_name,
		}

	# Inputs
	avg_monthly = _mean(monthly_demand)
	std_monthly = _std(monthly_demand)
	annual_demand = avg_monthly * 12

	unit_cost = _get_unit_cost(item_code)
	if unit_cost <= 0:
		return {
			"error": (
				f"Cannot determine unit cost for '{item_name}'. "
				"Set valuation_rate, last_purchase_rate, or standard_rate on the Item."
			),
			"item_code": item_code,
			"item_name": item_name,
		}

	order_cost = flt(order_cost) if order_cost else _DEFAULT_ORDER_COST
	holding_cost_pct = flt(holding_cost_pct) if holding_cost_pct else _DEFAULT_HOLDING_COST_PCT
	holding_cost_per_unit = unit_cost * holding_cost_pct

	if lead_time_days is None:
		lead_time_days = flt(frappe.db.get_value("Item", item_code, "lead_time_days")) or _DEFAULT_LEAD_TIME_DAYS
	lead_time_days = max(1, int(lead_time_days))

	z_score = _SERVICE_LEVEL_Z.get(str(service_level), _SERVICE_LEVEL_Z["95"])

	# EOQ
	if holding_cost_per_unit <= 0 or annual_demand <= 0:
		return {
			"error": "Cannot compute EOQ — annual demand and holding cost must be positive.",
			"item_code": item_code,
			"annual_demand": annual_demand,
			"holding_cost_per_unit": holding_cost_per_unit,
		}
	eoq = math.sqrt((2 * annual_demand * order_cost) / holding_cost_per_unit)

	# Safety stock and reorder point
	safety_stock = z_score * std_monthly * math.sqrt(lead_time_days / 30.0)
	reorder_point = (avg_monthly / 30.0) * lead_time_days + safety_stock

	# Cost projections
	expected_carrying_cost = (eoq / 2.0) * holding_cost_per_unit + safety_stock * holding_cost_per_unit
	expected_order_cost = (annual_demand / eoq) * order_cost
	total_annual_cost = expected_carrying_cost + expected_order_cost

	current_stock = _get_current_stock(item_code, company)
	risk = _stockout_risk_label(current_stock, reorder_point, safety_stock)

	# Chart: current stock vs key thresholds
	echart = build_bar_chart(
		title=f"Inventory Plan — {item_name}",
		categories=["Current Stock", "Safety Stock", "Reorder Point", "EOQ (Order Qty)"],
		series_data=[
			round(current_stock, 2),
			round(safety_stock, 2),
			round(reorder_point, 2),
			round(eoq, 2),
		],
		y_axis_name="Units",
		series_name="Quantity",
	)

	action = (
		f"Order {round(eoq)} units of {item_name} when stock falls to {round(reorder_point)} units. "
		f"Maintain {round(safety_stock)} units of safety stock."
	)

	data = {
		"item_code": item_code,
		"item_name": item_name,
		"inputs": {
			"average_monthly_demand": flt(avg_monthly, 2),
			"demand_std_dev": flt(std_monthly, 2),
			"annual_demand": flt(annual_demand, 2),
			"unit_cost": flt(unit_cost, 2),
			"order_cost": flt(order_cost, 2),
			"holding_cost_pct": flt(holding_cost_pct, 4),
			"holding_cost_per_unit_per_year": flt(holding_cost_per_unit, 2),
			"lead_time_days": lead_time_days,
			"service_level": str(service_level),
			"z_score": z_score,
		},
		"recommended_order_quantity": flt(eoq, 2),
		"recommended_reorder_point": flt(reorder_point, 2),
		"safety_stock": flt(safety_stock, 2),
		"current_stock": flt(current_stock, 2),
		"stockout_risk": risk,
		"expected_annual_carrying_cost": flt(expected_carrying_cost, 2),
		"expected_annual_order_cost": flt(expected_order_cost, 2),
		"total_annual_cost": flt(total_annual_cost, 2),
		"orders_per_year": flt(annual_demand / eoq, 2),
		"action": action,
		"echart_option": echart,
	}
	return build_currency_response(data, _primary(company))
