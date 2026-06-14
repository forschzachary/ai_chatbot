# Copyright (c) 2026, Sanjay Kumar and contributors
# For license information, please see license.txt
"""
Production Scheduling Optimisation Tool

Generates a monthly production schedule for an item from its demand
forecast using the Silver-Meal heuristic for dynamic lot sizing.

Silver-Meal balances setup cost against holding cost period-by-period:
	For each open period t, accumulate periods t, t+1, ... t+k into one
	lot while average-per-period cost (setup + cumulative holding) keeps
	decreasing. Issue the lot when the next period would push avg cost up,
	then restart at t+k+1.

Optionally caps each month's production at a user-supplied monthly capacity
and rolls excess to the next period.
"""

import frappe
from frappe.query_builder import functions as fn
from frappe.utils import add_months, flt, get_first_day, get_last_day, nowdate

from ai_chatbot.core.constants import MAX_FORECAST_MONTHS, MIN_FORECAST_HISTORY
from ai_chatbot.core.exceptions import InsufficientDataError
from ai_chatbot.core.session_context import get_company_filter
from ai_chatbot.data.charts import build_multi_series_chart
from ai_chatbot.data.currency import build_company_context
from ai_chatbot.data.forecasting import fill_month_gaps, forecast_time_series, generate_month_labels
from ai_chatbot.tools.common import apply_company_filter as _apply_company_filter
from ai_chatbot.tools.common import primary as _primary
from ai_chatbot.tools.registry import register_tool

_DEFAULT_SETUP_COST = 100.0
_DEFAULT_HOLDING_COST_PCT = 0.25


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


def _get_monthly_demand(item_code: str, company, months_back: int = 24) -> list[float]:
	si = frappe.qb.DocType("Sales Invoice")
	sii = frappe.qb.DocType("Sales Invoice Item")
	start_date = get_first_day(add_months(nowdate(), -months_back + 1))
	end_date = get_last_day(nowdate())
	month_expr = fn.DateFormat(si.posting_date, "%Y-%m")

	query = (
		frappe.qb.from_(sii)
		.join(si)
		.on(sii.parent == si.name)
		.select(month_expr.as_("month"), fn.Sum(sii.stock_qty).as_("total_qty"))
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


def _silver_meal(demand: list[float], setup_cost: float, holding_cost_per_unit: float) -> list[tuple[int, int]]:
	"""Run Silver-Meal lot sizing on monthly demand.

	Returns a list of (start_period_index, periods_covered) tuples, one per lot.
	"""
	n = len(demand)
	lots: list[tuple[int, int]] = []
	t = 0
	while t < n:
		# Find best k (periods covered = k+1) starting at t
		best_k = 0
		# TC(k) = setup + h * sum_{i=0..k} (i * demand[t+i])
		# avg_cost(k) = TC(k) / (k+1)
		prev_avg = float("inf")
		cum_holding = 0.0
		k = 0
		while t + k < n:
			cum_holding += k * holding_cost_per_unit * demand[t + k]
			avg_cost = (setup_cost + cum_holding) / (k + 1)
			if avg_cost > prev_avg:
				break
			prev_avg = avg_cost
			best_k = k
			k += 1
		lots.append((t, best_k + 1))
		t += best_k + 1
	return lots


def _build_schedule(
	demand: list[float],
	lots: list[tuple[int, int]],
	labels: list[str],
	monthly_capacity: float | None,
) -> list[dict]:
	"""Materialise the lot list into a per-month schedule, honouring capacity."""
	n = len(demand)
	production = [0.0] * n
	reasons = [""] * n

	for start, span in lots:
		lot_qty = sum(demand[start : start + span])
		production[start] = lot_qty
		reasons[start] = (
			f"Single lot covers periods {labels[start]}..{labels[min(start + span - 1, n - 1)]}"
		)

	# Apply capacity cap: roll excess forward
	if monthly_capacity and monthly_capacity > 0:
		for i in range(n):
			if production[i] > monthly_capacity:
				overflow = production[i] - monthly_capacity
				production[i] = monthly_capacity
				if i + 1 < n:
					production[i + 1] += overflow
					reasons[i] = (reasons[i] + " — capped at capacity, overflow deferred").strip(" —")
				else:
					reasons[i] = (reasons[i] + " — capped at capacity, overflow not schedulable").strip(" —")

	# Build ending-inventory and assemble schedule
	schedule = []
	inventory = 0.0
	for i in range(n):
		inventory += production[i] - demand[i]
		schedule.append(
			{
				"month": labels[i],
				"forecast_demand": flt(demand[i], 2),
				"recommended_production": flt(production[i], 2),
				"ending_inventory": flt(max(inventory, 0.0), 2),
				"reason": reasons[i] or "Carried from earlier lot",
			}
		)
	return schedule


@register_tool(
	name="optimize_production_schedule",
	category="prescriptive",
	description=(
		"Build a monthly production schedule for an item using the Silver-Meal lot-sizing "
		"heuristic. Forecasts demand from historical Sales Invoices, then groups demand into "
		"production lots that balance setup cost against inventory holding cost. Optionally "
		"caps each month at a user-provided capacity. Returns the schedule, total cost, and a chart."
	),
	parameters={
		"item_code": {
			"type": "string",
			"description": "Item code or item name to schedule (required).",
		},
		"months_ahead": {
			"type": "integer",
			"description": "Number of months to schedule (default 6, max 12).",
		},
		"setup_cost": {
			"type": "number",
			"description": "Fixed cost per production run / setup. Default 100.",
		},
		"holding_cost_pct": {
			"type": "number",
			"description": "Annual holding cost as a fraction of unit cost (default 0.25 = 25%).",
		},
		"monthly_capacity": {
			"type": "number",
			"description": "Optional max units producible per month. Excess rolls to next month.",
		},
		"company": {
			"type": "string",
			"description": "Company name. Optional — defaults to the user's default company.",
		},
	},
	doctypes=["Sales Invoice", "Item"],
)
def optimize_production_schedule(
	item_code=None,
	months_ahead=6,
	setup_cost=None,
	holding_cost_pct=None,
	monthly_capacity=None,
	company=None,
):
	"""Generate a Silver-Meal production schedule for an item."""
	if not item_code:
		return {"error": "item_code is required"}

	company = get_company_filter(company)
	months_ahead = min(max(1, int(months_ahead or 6)), MAX_FORECAST_MONTHS)

	resolved = _resolve_item(item_code)
	if not resolved:
		return {"error": f"Item '{item_code}' not found"}
	item_code = resolved
	item_name = frappe.db.get_value("Item", item_code, "item_name") or item_code

	# Historical demand for forecast
	monthly = _get_monthly_demand(item_code, company)
	first_nonzero = next((i for i, v in enumerate(monthly) if v > 0), len(monthly))
	monthly = monthly[first_nonzero:]
	if len(monthly) < MIN_FORECAST_HISTORY:
		return {
			"error": (
				f"Insufficient sales history for '{item_name}'. "
				f"Need at least {MIN_FORECAST_HISTORY} months, found {len(monthly)}."
			),
			"item_code": item_code,
		}

	try:
		forecast = forecast_time_series(monthly, months_ahead=months_ahead)
	except InsufficientDataError:
		return {
			"error": f"Not enough data to forecast demand for '{item_name}'.",
			"item_code": item_code,
		}

	demand_forecast = [max(0.0, flt(v)) for v in forecast["forecast"]]

	# Build month labels starting from the current month
	last_hist_label = add_months(nowdate(), -1)[:7]
	labels = generate_month_labels(last_hist_label, months_ahead)

	# Costs
	unit_cost = _get_unit_cost(item_code)
	if unit_cost <= 0:
		return {
			"error": (
				f"Cannot determine unit cost for '{item_name}'. "
				"Set valuation_rate, last_purchase_rate, or standard_rate on the Item."
			),
			"item_code": item_code,
		}

	setup_cost = flt(setup_cost) if setup_cost else _DEFAULT_SETUP_COST
	holding_cost_pct = flt(holding_cost_pct) if holding_cost_pct else _DEFAULT_HOLDING_COST_PCT
	holding_cost_per_unit_per_month = unit_cost * holding_cost_pct / 12.0

	# Silver-Meal lots
	lots = _silver_meal(demand_forecast, setup_cost, holding_cost_per_unit_per_month)
	cap = flt(monthly_capacity) if monthly_capacity else None
	schedule = _build_schedule(demand_forecast, lots, labels, cap)

	# Costs and utilisation
	total_setup = setup_cost * sum(1 for row in schedule if row["recommended_production"] > 0)
	total_holding = sum(row["ending_inventory"] * holding_cost_per_unit_per_month for row in schedule)
	total_cost = total_setup + total_holding
	utilisation_pct = None
	if cap and cap > 0:
		utilisations = [row["recommended_production"] / cap for row in schedule]
		utilisation_pct = flt(sum(utilisations) / len(utilisations) * 100, 2)

	echart = build_multi_series_chart(
		title=f"Production Schedule — {item_name}",
		categories=labels,
		series_list=[
			{"name": "Forecast Demand", "data": [row["forecast_demand"] for row in schedule]},
			{"name": "Recommended Production", "data": [row["recommended_production"] for row in schedule]},
			{"name": "Ending Inventory", "data": [row["ending_inventory"] for row in schedule]},
		],
		y_axis_name="Units",
		chart_type="bar",
	)

	data = {
		"item_code": item_code,
		"item_name": item_name,
		"forecast_method": forecast["method_used"],
		"inputs": {
			"unit_cost": flt(unit_cost, 2),
			"setup_cost": flt(setup_cost, 2),
			"holding_cost_pct": flt(holding_cost_pct, 4),
			"holding_cost_per_unit_per_month": flt(holding_cost_per_unit_per_month, 4),
			"monthly_capacity": flt(cap, 2) if cap else None,
		},
		"production_schedule": schedule,
		"total_setup_cost": flt(total_setup, 2),
		"total_holding_cost": flt(total_holding, 2),
		"total_cost": flt(total_cost, 2),
		"production_runs": sum(1 for row in schedule if row["recommended_production"] > 0),
		"average_capacity_utilisation_pct": utilisation_pct,
		"echart_option": echart,
	}
	# Quantities are non-monetary — use company context, not currency
	return build_company_context(data, _primary(company))
