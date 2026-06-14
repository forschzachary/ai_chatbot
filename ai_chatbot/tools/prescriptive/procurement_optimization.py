# Copyright (c) 2026, Sanjay Kumar and contributors
# For license information, please see license.txt
"""
Procurement Optimisation Tool

Analyses purchase patterns and supplier behaviour to recommend sourcing
strategy improvements. Heuristic — operational signals rather than a
formal optimisation model.

Signals considered:
	- Supplier concentration (top-5 share of spend)
	- New suppliers in the analysis window with abnormally large first orders
	- Items ordered frequently in small lots (consolidation candidates)
"""

import frappe
from frappe.query_builder import functions as fn
from frappe.utils import add_days, add_months, flt, get_first_day, get_last_day, getdate, nowdate

from ai_chatbot.core.session_context import get_company_filter
from ai_chatbot.data.charts import build_horizontal_bar
from ai_chatbot.data.currency import build_currency_response
from ai_chatbot.data.forecasting import _mean, _std
from ai_chatbot.tools.common import apply_company_filter as _apply_company_filter
from ai_chatbot.tools.common import primary as _primary
from ai_chatbot.tools.registry import register_tool

_TOP_SUPPLIER_LIMIT = 10
_NEW_SUPPLIER_WINDOW_DAYS = 90
_NEW_SUPPLIER_Z_THRESHOLD = 2.0
_BULK_CANDIDATE_MIN_ORDERS = 4  # In the last NEW_SUPPLIER_WINDOW_DAYS days
_BULK_CANDIDATE_WINDOW_DAYS = 90
_TARGET_TOP5_SHARE = 0.70  # Below this we recommend consolidation


def _get_supplier_spend(company, from_date, to_date) -> list[dict]:
	"""Return [{supplier, total_spend, invoice_count}, ...] sorted by spend desc."""
	pi = frappe.qb.DocType("Purchase Invoice")
	query = (
		frappe.qb.from_(pi)
		.select(
			pi.supplier.as_("supplier"),
			fn.Sum(pi.base_grand_total).as_("total_spend"),
			fn.Count(pi.name).as_("invoice_count"),
		)
		.where(pi.docstatus == 1)
		.where(pi.posting_date >= from_date)
		.where(pi.posting_date <= to_date)
		.where(pi.supplier.isnotnull())
	)
	query = _apply_company_filter(query, pi, company)
	rows = query.groupby(pi.supplier).orderby(fn.Sum(pi.base_grand_total), order=frappe.qb.desc).run(as_dict=True)
	return [{"supplier": r.supplier, "total_spend": flt(r.total_spend), "invoice_count": int(r.invoice_count)} for r in rows]


def _find_risky_new_suppliers(company, from_date, to_date) -> list[dict]:
	"""New suppliers (first PI in window) whose first order is z-score outlier."""
	pi = frappe.qb.DocType("Purchase Invoice")
	first_q = (
		frappe.qb.from_(pi)
		.select(
			pi.supplier.as_("supplier"),
			fn.Min(pi.posting_date).as_("first_date"),
			fn.Min(pi.name).as_("first_doc"),
		)
		.where(pi.docstatus == 1)
		.where(pi.supplier.isnotnull())
	)
	first_q = _apply_company_filter(first_q, pi, company)
	first_txn = first_q.groupby(pi.supplier).run(as_dict=True)

	window_start = getdate(from_date)
	new_supplier_docs = [
		(r.supplier, r.first_doc) for r in first_txn if getdate(r.first_date) >= window_start
	]
	if not new_supplier_docs:
		return []

	# Compute mean/std of all Purchase Invoice amounts for the company in the window
	amount_q = (
		frappe.qb.from_(pi)
		.select(pi.name.as_("name"), pi.base_grand_total.as_("amount"))
		.where(pi.docstatus == 1)
		.where(pi.posting_date >= from_date)
		.where(pi.posting_date <= to_date)
		.limit(5000)
	)
	amount_q = _apply_company_filter(amount_q, pi, company)
	all_rows = amount_q.run(as_dict=True)
	if len(all_rows) < 5:
		return []
	amounts = [flt(r.amount) for r in all_rows]
	mean = _mean(amounts)
	std = _std(amounts)
	if std < 1e-9:
		return []

	first_doc_names = [d for _, d in new_supplier_docs]
	first_doc_amounts = {
		r.name: flt(r.amount)
		for r in frappe.db.get_all(
			"Purchase Invoice",
			filters={"name": ["in", first_doc_names]},
			fields=["name", "base_grand_total as amount"],
		)
	}

	risky = []
	for supplier, doc in new_supplier_docs:
		amount = first_doc_amounts.get(doc, 0.0)
		z = (amount - mean) / std
		if z > _NEW_SUPPLIER_Z_THRESHOLD:
			risky.append(
				{
					"supplier": supplier,
					"first_invoice": doc,
					"first_amount": flt(amount, 2),
					"z_score": round(z, 2),
				}
			)
	risky.sort(key=lambda r: r["z_score"], reverse=True)
	return risky


def _find_bulk_candidates(company, window_days: int) -> list[dict]:
	"""Items ordered ≥ N times in recent window — candidates to consolidate into bulk orders."""
	pi = frappe.qb.DocType("Purchase Invoice")
	pii = frappe.qb.DocType("Purchase Invoice Item")
	cutoff = add_days(nowdate(), -window_days)

	query = (
		frappe.qb.from_(pii)
		.join(pi)
		.on(pii.parent == pi.name)
		.select(
			pii.item_code.as_("item_code"),
			fn.Count(pi.name.distinct()).as_("order_count"),
			fn.Sum(pii.qty).as_("total_qty"),
			fn.Sum(pii.base_amount).as_("total_spend"),
		)
		.where(pi.docstatus == 1)
		.where(pi.posting_date >= cutoff)
	)
	query = _apply_company_filter(query, pi, company)
	rows = query.groupby(pii.item_code).having(
		fn.Count(pi.name.distinct()) >= _BULK_CANDIDATE_MIN_ORDERS
	).orderby(fn.Sum(pii.base_amount), order=frappe.qb.desc).limit(10).run(as_dict=True)

	candidates = []
	for r in rows:
		count = int(r.order_count)
		total_qty = flt(r.total_qty)
		total_spend = flt(r.total_spend)
		if count <= 0 or total_qty <= 0:
			continue
		avg_qty_per_order = total_qty / count
		candidates.append(
			{
				"item_code": r.item_code,
				"order_count": count,
				"average_qty_per_order": flt(avg_qty_per_order, 2),
				"total_qty": flt(total_qty, 2),
				"total_spend": flt(total_spend, 2),
			}
		)
	return candidates


@register_tool(
	name="optimize_procurement",
	category="prescriptive",
	description=(
		"Recommend procurement strategy improvements based on recent purchase patterns: "
		"supplier consolidation when top-5 share is low, new-supplier risk flags for abnormally "
		"large first orders, and bulk-purchase candidates for frequently-ordered items. "
		"Returns a structured list of recommendations with priority."
	),
	parameters={
		"months_back": {
			"type": "integer",
			"description": "Months of purchase history to analyse (default 12, max 24).",
		},
		"company": {
			"type": "string",
			"description": "Company name. Optional — defaults to the user's default company.",
		},
	},
	doctypes=["Purchase Invoice"],
)
def optimize_procurement(months_back=12, company=None):
	"""Generate procurement recommendations from recent purchase data."""
	company = get_company_filter(company)
	months_back = min(max(3, int(months_back or 12)), 24)

	from_date = get_first_day(add_months(nowdate(), -months_back + 1))
	to_date = get_last_day(nowdate())

	supplier_spend = _get_supplier_spend(company, from_date, to_date)
	if not supplier_spend:
		return {
			"error": "No submitted Purchase Invoices found in the analysis window.",
			"period": {"from": str(from_date), "to": str(to_date)},
		}

	total_spend = sum(s["total_spend"] for s in supplier_spend)
	top5 = supplier_spend[:5]
	top5_spend = sum(s["total_spend"] for s in top5)
	top5_share = top5_spend / total_spend if total_spend > 0 else 0.0

	new_window_start = add_days(nowdate(), -_NEW_SUPPLIER_WINDOW_DAYS)
	risky_new = _find_risky_new_suppliers(company, new_window_start, to_date)
	bulk_candidates = _find_bulk_candidates(company, _BULK_CANDIDATE_WINDOW_DAYS)

	recommendations: list[dict] = []

	if top5_share < _TARGET_TOP5_SHARE and len(supplier_spend) > 5:
		recommendations.append(
			{
				"type": "supplier_consolidation",
				"priority": "high",
				"action": (
					f"Consolidate spend onto top 5 suppliers — they currently hold "
					f"{round(top5_share * 100, 1)}% of total spend across {len(supplier_spend)} suppliers."
				),
				"impact": "Volume discounts, simpler vendor management, stronger negotiating position.",
			}
		)
	elif top5_share >= 0.90:
		recommendations.append(
			{
				"type": "supplier_concentration_risk",
				"priority": "medium",
				"action": (
					f"Top 5 suppliers hold {round(top5_share * 100, 1)}% of spend — concentration is high."
				),
				"impact": "Add 1-2 secondary suppliers for critical categories to reduce single-source risk.",
			}
		)

	if risky_new:
		recommendations.append(
			{
				"type": "new_supplier_risk",
				"priority": "high",
				"action": (
					f"Flag {len(risky_new)} new supplier(s) whose first invoice is more than "
					f"{_NEW_SUPPLIER_Z_THRESHOLD}sigma above average."
				),
				"impact": "Verify credit, negotiate payment terms, cap initial exposure.",
				"details": risky_new[:5],
			}
		)

	if bulk_candidates:
		recommendations.append(
			{
				"type": "bulk_purchasing",
				"priority": "medium",
				"action": (
					f"Consolidate frequent small orders into bulk purchases for "
					f"{len(bulk_candidates)} item(s)."
				),
				"impact": "Reduce per-order overhead, qualify for volume discounts.",
				"details": bulk_candidates[:5],
			}
		)

	if not recommendations:
		recommendations.append(
			{
				"type": "no_action",
				"priority": "info",
				"action": "Procurement profile looks healthy — no high-priority signals detected.",
				"impact": "Continue monitoring monthly.",
			}
		)

	# Top suppliers chart
	top_chart_data = supplier_spend[:_TOP_SUPPLIER_LIMIT]
	echart = build_horizontal_bar(
		title="Top Suppliers by Spend",
		categories=[s["supplier"] for s in top_chart_data],
		series_data=[round(s["total_spend"], 2) for s in top_chart_data],
		x_axis_name="Spend",
	)

	data = {
		"period": {"from": str(from_date), "to": str(to_date)},
		"total_spend": flt(total_spend, 2),
		"total_suppliers": len(supplier_spend),
		"top5_share_pct": flt(top5_share * 100, 2),
		"top_suppliers": [
			{
				"supplier": s["supplier"],
				"total_spend": flt(s["total_spend"], 2),
				"invoice_count": s["invoice_count"],
				"share_pct": flt(s["total_spend"] / total_spend * 100, 2) if total_spend else 0.0,
			}
			for s in supplier_spend[:_TOP_SUPPLIER_LIMIT]
		],
		"risky_new_suppliers": risky_new,
		"bulk_purchase_candidates": bulk_candidates,
		"recommendations": recommendations,
		"echart_option": echart,
	}
	return build_currency_response(data, _primary(company))
