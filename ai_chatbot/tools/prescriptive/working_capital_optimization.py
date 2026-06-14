# Copyright (c) 2026, Sanjay Kumar and contributors
# For license information, please see license.txt
"""
Working Capital Optimisation Tool

Computes the cash conversion cycle (CCC = DSO + DIO - DPO) from current
ERPNext balances and recommends payment-terms / credit-policy changes
when DSO, DPO, or DIO drift from configurable targets.

Definitions:
	DSO = (Outstanding AR / Net Sales) * period_days
	DPO = (Outstanding AP / Net Purchases) * period_days
	DIO = (Inventory Value / Net Purchases) * period_days
	CCC = DSO + DIO - DPO

A higher CCC means cash is tied up longer in operations.
"""

import frappe
from frappe.query_builder import functions as fn
from frappe.utils import add_months, flt, get_first_day, get_last_day, nowdate

from ai_chatbot.core.session_context import get_company_filter
from ai_chatbot.data.charts import build_multi_series_chart
from ai_chatbot.data.currency import build_currency_response
from ai_chatbot.tools.common import apply_company_filter as _apply_company_filter
from ai_chatbot.tools.common import primary as _primary
from ai_chatbot.tools.registry import register_tool

# Default benchmarks (overridable per call)
_DEFAULT_TARGET_DSO = 45
_DEFAULT_TARGET_DPO = 30
_DEFAULT_TARGET_DIO = 60


def _sum_in_period(doctype: str, field: str, company, from_date=None, to_date=None) -> float:
	"""Sum a numeric field on submitted documents, optionally bounded by posting_date."""
	table = frappe.qb.DocType(doctype)
	q = (
		frappe.qb.from_(table)
		.select(fn.Sum(table[field]).as_("total"))
		.where(table.docstatus == 1)
	)
	if from_date is not None:
		q = q.where(table.posting_date >= from_date)
	if to_date is not None:
		q = q.where(table.posting_date <= to_date)
	q = _apply_company_filter(q, table, company)
	rows = q.run(as_dict=True)
	return flt(rows[0].total) if rows and rows[0].total else 0.0


def _get_inventory_value(company) -> float:
	"""Sum Bin.stock_value for all warehouses belonging to company."""
	bin_dt = frappe.qb.DocType("Bin")
	wh = frappe.qb.DocType("Warehouse")
	q = (
		frappe.qb.from_(bin_dt)
		.join(wh)
		.on(bin_dt.warehouse == wh.name)
		.select(fn.Sum(bin_dt.stock_value).as_("total"))
	)
	q = _apply_company_filter(q, wh, company)
	rows = q.run(as_dict=True)
	return flt(rows[0].total) if rows and rows[0].total else 0.0


@register_tool(
	name="optimize_working_capital",
	category="prescriptive",
	description=(
		"Compute the cash conversion cycle (DSO + DIO - DPO) from current ERPNext balances and "
		"recommend payment-terms, credit-policy, or inventory-reduction actions when metrics "
		"drift from configurable targets. Returns metrics, dollar-impact estimates per "
		"recommendation, and a chart comparing current vs target."
	),
	parameters={
		"months_back": {
			"type": "integer",
			"description": "Months of sales/purchase history used to compute daily flow (default 12, max 24).",
		},
		"target_dso": {
			"type": "number",
			"description": "Target Days Sales Outstanding (default 45).",
		},
		"target_dpo": {
			"type": "number",
			"description": "Target Days Payable Outstanding (default 30).",
		},
		"target_dio": {
			"type": "number",
			"description": "Target Days Inventory Outstanding (default 60).",
		},
		"company": {
			"type": "string",
			"description": "Company name. Optional — defaults to the user's default company.",
		},
	},
	doctypes=["Sales Invoice", "Purchase Invoice", "Bin"],
)
def optimize_working_capital(
	months_back=12,
	target_dso=None,
	target_dpo=None,
	target_dio=None,
	company=None,
):
	"""Compute DSO/DPO/DIO/CCC and recommend changes vs targets."""
	company = get_company_filter(company)
	months_back = min(max(3, int(months_back or 12)), 24)

	from_date = get_first_day(add_months(nowdate(), -months_back + 1))
	to_date = get_last_day(nowdate())
	period_days = months_back * 30

	# Period-window aggregates
	net_sales = _sum_in_period("Sales Invoice", "base_grand_total", company, from_date, to_date)
	net_purchases = _sum_in_period("Purchase Invoice", "base_grand_total", company, from_date, to_date)

	# Current outstanding balances (point-in-time snapshot, not date-bounded)
	ar_outstanding = _sum_in_period("Sales Invoice", "base_outstanding_amount", company)
	ap_outstanding = _sum_in_period("Purchase Invoice", "base_outstanding_amount", company)
	inventory_value = _get_inventory_value(company)

	if net_sales <= 0 or net_purchases <= 0:
		return {
			"error": (
				"Insufficient transaction volume to compute working-capital metrics. "
				"Net sales and net purchases must both be positive in the analysis window."
			),
			"period": {"from": str(from_date), "to": str(to_date)},
			"net_sales": flt(net_sales, 2),
			"net_purchases": flt(net_purchases, 2),
		}

	daily_sales = net_sales / period_days
	daily_purchases = net_purchases / period_days

	dso = (ar_outstanding / net_sales) * period_days
	dpo = (ap_outstanding / net_purchases) * period_days
	dio = (inventory_value / net_purchases) * period_days
	ccc = dso + dio - dpo

	t_dso = flt(target_dso) if target_dso else _DEFAULT_TARGET_DSO
	t_dpo = flt(target_dpo) if target_dpo else _DEFAULT_TARGET_DPO
	t_dio = flt(target_dio) if target_dio else _DEFAULT_TARGET_DIO
	t_ccc = t_dso + t_dio - t_dpo

	recommendations = []

	if dso > t_dso:
		impact = (dso - t_dso) * daily_sales
		recommendations.append(
			{
				"type": "credit_policy",
				"priority": "high" if dso - t_dso > 15 else "medium",
				"action": (
					f"Tighten credit policy — reduce DSO from {round(dso, 1)} to {round(t_dso, 1)} days."
				),
				"impact": (
					f"Frees approximately {round(impact, 2)} in cash. Consider stricter credit limits, "
					"earlier dunning, or early-payment discounts."
				),
				"cash_freed": flt(impact, 2),
			}
		)

	if dpo < t_dpo:
		impact = (t_dpo - dpo) * daily_purchases
		recommendations.append(
			{
				"type": "payment_terms",
				"priority": "medium",
				"action": (
					f"Negotiate longer payment terms — extend DPO from {round(dpo, 1)} to {round(t_dpo, 1)} days."
				),
				"impact": (
					f"Improves cash position by approximately {round(impact, 2)}. Be mindful of supplier "
					"relationships and any early-payment discounts forgone."
				),
				"cash_freed": flt(impact, 2),
			}
		)

	if dio > t_dio:
		impact = (dio - t_dio) * daily_purchases
		recommendations.append(
			{
				"type": "inventory_reduction",
				"priority": "high" if dio - t_dio > 30 else "medium",
				"action": (
					f"Reduce inventory days — current {round(dio, 1)}, target {round(t_dio, 1)}."
				),
				"impact": (
					f"Releases approximately {round(impact, 2)} from inventory. "
					"Use the inventory optimisation tool to set EOQ + safety stock per item."
				),
				"cash_freed": flt(impact, 2),
			}
		)

	if ccc > t_ccc * 1.5:
		recommendations.append(
			{
				"type": "ccc_alert",
				"priority": "high",
				"action": (
					f"Cash conversion cycle is {round(ccc, 1)} days vs target {round(t_ccc, 1)} — "
					"working capital is heavily tied up."
				),
				"impact": "Address DSO/DPO/DIO drivers above; consider short-term financing if cash is critical.",
			}
		)

	if not recommendations:
		recommendations.append(
			{
				"type": "no_action",
				"priority": "info",
				"action": "Working-capital metrics are within target ranges.",
				"impact": "Monitor monthly; review targets quarterly.",
			}
		)

	echart = build_multi_series_chart(
		title="Working Capital — Current vs Target",
		categories=["DSO", "DPO", "DIO", "CCC"],
		series_list=[
			{"name": "Current", "data": [round(dso, 1), round(dpo, 1), round(dio, 1), round(ccc, 1)]},
			{"name": "Target", "data": [round(t_dso, 1), round(t_dpo, 1), round(t_dio, 1), round(t_ccc, 1)]},
		],
		y_axis_name="Days",
		chart_type="bar",
	)

	data = {
		"period": {"from": str(from_date), "to": str(to_date), "days": period_days},
		"net_sales": flt(net_sales, 2),
		"net_purchases": flt(net_purchases, 2),
		"daily_sales": flt(daily_sales, 2),
		"daily_purchases": flt(daily_purchases, 2),
		"ar_outstanding": flt(ar_outstanding, 2),
		"ap_outstanding": flt(ap_outstanding, 2),
		"inventory_value": flt(inventory_value, 2),
		"metrics": {
			"dso": flt(dso, 2),
			"dpo": flt(dpo, 2),
			"dio": flt(dio, 2),
			"ccc": flt(ccc, 2),
		},
		"targets": {
			"dso": flt(t_dso, 2),
			"dpo": flt(t_dpo, 2),
			"dio": flt(t_dio, 2),
			"ccc": flt(t_ccc, 2),
		},
		"recommendations": recommendations,
		"echart_option": echart,
	}
	return build_currency_response(data, _primary(company))
