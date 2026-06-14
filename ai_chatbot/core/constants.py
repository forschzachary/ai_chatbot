# Copyright (c) 2026, Sanjay Kumar and contributors
# For license information, please see license.txt
"""
App-wide Constants for AI Chatbot
"""

# Date format used in tool parameters
DATE_FORMAT = "YYYY-MM-DD"

# Default limits
DEFAULT_QUERY_LIMIT = 20
DEFAULT_TOP_N_LIMIT = 10
MAX_QUERY_LIMIT = 100

# Aging buckets for receivables/payables (in days)
AGING_BUCKETS = [
	{"label": "0-30", "min": 0, "max": 30},
	{"label": "31-60", "min": 31, "max": 60},
	{"label": "61-90", "min": 61, "max": 90},
	{"label": "90+", "min": 91, "max": None},
]

# Tool categories — maps settings field to tool module
TOOL_CATEGORIES = {
	"crm": "enable_crm_tools",
	"selling": "enable_sales_tools",
	"buying": "enable_purchase_tools",
	"finance": "enable_finance_tools",
	"inventory": "enable_inventory_tools",
	"hrms": "enable_hrms_tools",
	"operations": "enable_write_operations",
	"idp": "enable_idp_tools",
	"predictive": "enable_predictive_tools",
	"prescriptive": "enable_prescriptive_tools",
}

# Predictive analytics defaults
MAX_FORECAST_MONTHS = 12
DEFAULT_FORECAST_MONTHS = 3
MIN_FORECAST_HISTORY = 3

# Base amount fields for multi-currency support
# Maps doctype to the field that holds the company-currency amount
BASE_AMOUNT_FIELDS = {
	"Sales Invoice": "base_grand_total",
	"Purchase Invoice": "base_grand_total",
	"Sales Order": "base_grand_total",
	"Purchase Order": "base_grand_total",
	"Payment Entry": "base_paid_amount",
	"Quotation": "base_grand_total",
	"Delivery Note": "base_grand_total",
	"Purchase Receipt": "base_grand_total",
}

# Transaction amount fields (original currency)
TRANSACTION_AMOUNT_FIELDS = {
	"Sales Invoice": "grand_total",
	"Purchase Invoice": "grand_total",
	"Sales Order": "grand_total",
	"Purchase Order": "grand_total",
	"Payment Entry": "paid_amount",
	"Quotation": "grand_total",
	"Delivery Note": "grand_total",
	"Purchase Receipt": "grand_total",
}

# Automation defaults
AUTOMATION_MAX_TOOL_ROUNDS = 5

# Logging title prefix
LOG_TITLE = "AI Chatbot"
