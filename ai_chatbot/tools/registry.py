# Copyright (c) 2026, Sanjay Kumar and contributors
# For license information, please see license.txt
"""
Tool Registry for AI Chatbot

Provides a decorator-based registration system for tools.
Tools self-register with metadata (name, category, description, schema).
The registry handles discovery, filtering by settings, and execution.
"""

import frappe

from ai_chatbot.core.config import is_tool_category_enabled
from ai_chatbot.core.constants import TOOL_CATEGORIES
from ai_chatbot.core.logger import log_error, log_tool_call, log_tool_error, timer

# Global tool store — populated by @register_tool decorator at import time
_TOOL_REGISTRY = {}

# Extra categories registered by external apps via register_tool_category()
_EXTRA_CATEGORIES = {}


def register_tool(name, category, description, parameters=None, doctypes=None):
	"""Decorator to register a tool function.

	Usage:
		@register_tool(
			name="get_sales_analytics",
			category="selling",
			description="Get sales analytics including revenue and orders",
			parameters={
				"from_date": {"type": "string", "description": "Start date (YYYY-MM-DD)"},
				"to_date": {"type": "string", "description": "End date (YYYY-MM-DD)"},
				"company": {"type": "string", "description": "Company name. Defaults to user's default company."},
			},
			doctypes=["Sales Invoice"],
		)
		def get_sales_analytics(from_date=None, to_date=None, company=None):
			...

	Args:
		name: Unique tool name (must match function name).
		category: Tool category key (e.g. "crm", "selling", "buying", "finance", "inventory").
		description: Human-readable description for the LLM.
		parameters: Dict of parameter definitions for OpenAI function calling schema.
		doctypes: List of DocType names the tool accesses. Used for permission checks.
	"""

	def decorator(func):
		_TOOL_REGISTRY[name] = {
			"name": name,
			"category": category,
			"description": description,
			"parameters": parameters or {},
			"doctypes": doctypes or [],
			"function": func,
		}
		return func

	return decorator


def get_all_tools_schema():
	"""Get OpenAI function calling schema for all enabled tools.

	Checks Chatbot Settings to determine which categories are enabled,
	then filters by user permissions on declared doctypes,
	and builds the schema from the remaining tools.

	Returns:
		List of dicts in OpenAI function calling format.
	"""
	_ensure_tools_loaded()

	all_categories = {**TOOL_CATEGORIES, **_EXTRA_CATEGORIES}
	tools = []
	for _tool_name, tool_info in _TOOL_REGISTRY.items():
		category = tool_info["category"]
		settings_field = all_categories.get(category)

		# If the category has a settings flag, check it
		if settings_field and not is_tool_category_enabled(settings_field):
			continue

		# Skip tools the user has no permission for
		tool_doctypes = tool_info.get("doctypes", [])
		if tool_doctypes:
			has_perm = all(
				frappe.has_permission(dt, "read", user=frappe.session.user) for dt in tool_doctypes
			)
			if not has_perm:
				continue

		tools.append(_build_schema(tool_info))

	return tools


def execute_tool(tool_name: str, arguments: dict) -> dict:
	"""Execute a registered tool by name.

	Checks user permissions on declared doctypes before executing.

	Args:
		tool_name: The registered tool name.
		arguments: Dict of arguments to pass to the tool function.

	Returns:
		Dict with "success" (bool) and "data" or "error".
	"""
	_ensure_tools_loaded()

	tool_info = _TOOL_REGISTRY.get(tool_name)
	if not tool_info:
		log_tool_error(tool_name, "Tool not found", arguments)
		return {"success": False, "error": f"Tool '{tool_name}' not found"}

	# Permission check on declared doctypes
	for dt in tool_info.get("doctypes", []):
		if not frappe.has_permission(dt, "read", user=frappe.session.user):
			return {
				"error": True,
				"error_type": "permission_denied",
				"message": f"You do not have permission to access {dt}",
				"suggestion": f"The user doesn't have access to {dt}. Inform them that they need the appropriate role/permission.",
			}

	conversation_id = getattr(frappe.flags, "current_conversation_id", None)
	try:
		with timer() as t:
			result = tool_info["function"](**arguments)
		log_tool_call(
			tool_name,
			arguments=arguments,
			duration_ms=t.duration_ms,
			conversation_id=conversation_id,
		)

		# Phase 13F: Audit successful tool call
		from ai_chatbot.core.audit import log_audit_event

		result_summary = str(result)[:500] if result else None
		log_audit_event(
			"tool_call",
			conversation=conversation_id,
			tool_name=tool_name,
			tool_args=arguments,
			tool_result_summary=result_summary,
			duration_ms=t.duration_ms,
			status="success",
		)

		# Phase 14B: Record tool usage for user preference learning
		try:
			from ai_chatbot.core.user_preferences import record_tool_usage

			record_tool_usage(tool_name)
		except Exception:
			pass  # Non-critical — don't break tool execution

		return {"success": True, "data": result}
	except Exception as e:
		log_tool_error(tool_name, e, arguments)

		# Phase 13F: Audit tool error
		from ai_chatbot.core.audit import log_audit_event

		log_audit_event(
			"tool_call",
			conversation=conversation_id,
			tool_name=tool_name,
			tool_args=arguments,
			status="error",
			error_message=str(e),
		)

		from ai_chatbot.core.resilience import classify_tool_error

		return classify_tool_error(e, tool_name, arguments)


def get_tool_info(tool_name: str) -> dict | None:
	"""Get metadata for a registered tool.

	Args:
		tool_name: The registered tool name.

	Returns:
		Tool info dict or None if not found.
	"""
	_ensure_tools_loaded()
	return _TOOL_REGISTRY.get(tool_name)


def get_registered_tools():
	"""Get all registered tool names and categories.

	Returns:
		Dict of {tool_name: category}.
	"""
	_ensure_tools_loaded()
	return {name: info["category"] for name, info in _TOOL_REGISTRY.items()}


def get_tools_by_categories(categories: set[str], extra_tool_names: set[str] | None = None) -> list[dict]:
	"""Get tool schemas filtered to specific categories.

	Like ``get_all_tools_schema()`` but only returns tools whose category
	is in the provided set.  Also includes any tools explicitly named in
	*extra_tool_names* (for always-include tools like session management).

	Still respects settings flags and user permission checks.

	Args:
		categories: Set of category keys (e.g. ``{"selling", "finance"}``).
		extra_tool_names: Optional set of tool names to always include
			regardless of category.

	Returns:
		List of dicts in OpenAI function calling format.
	"""
	_ensure_tools_loaded()

	all_categories = {**TOOL_CATEGORIES, **_EXTRA_CATEGORIES}
	extra = extra_tool_names or set()
	tools = []

	for tool_name, tool_info in _TOOL_REGISTRY.items():
		category = tool_info["category"]

		# Include if category matches OR tool name is in the extra set
		if category not in categories and tool_name not in extra:
			continue

		# Check settings flag
		settings_field = all_categories.get(category)
		if settings_field and not is_tool_category_enabled(settings_field):
			continue

		# Skip tools the user has no permission for
		tool_doctypes = tool_info.get("doctypes", [])
		if tool_doctypes:
			has_perm = all(
				frappe.has_permission(dt, "read", user=frappe.session.user) for dt in tool_doctypes
			)
			if not has_perm:
				continue

		tools.append(_build_schema(tool_info))

	return tools


def register_tool_category(name, settings_field=None):
	"""Register a new tool category from an external app.

	External apps can call this to declare new tool categories.
	If settings_field is None, the category is always enabled
	(no toggle in Chatbot Settings).

	Args:
		name: Category key (e.g. "manufacturing").
		settings_field: Chatbot Settings field name (e.g. "enable_manufacturing_tools").
			If None, tools in this category are always enabled.
	"""
	_EXTRA_CATEGORIES[name] = settings_field


def _build_schema(tool_info):
	"""Build OpenAI function calling schema for a tool.

	Args:
		tool_info: Tool registry entry dict.

	Returns:
		Dict in OpenAI function calling format.
	"""
	return {
		"type": "function",
		"function": {
			"name": tool_info["name"],
			"description": tool_info["description"],
			"parameters": {
				"type": "object",
				"properties": tool_info["parameters"],
			},
		},
	}


_tools_loaded = False


def _ensure_tools_loaded():
	"""Import all tool modules to trigger @register_tool decorators.

	Called lazily on first access. Module imports are idempotent —
	Python caches them after first import.

	ERPNext and HRMS tool imports are conditional — they are only loaded
	when the respective app is installed.
	"""
	global _tools_loaded
	if _tools_loaded:
		return
	_tools_loaded = True

	from ai_chatbot.core.config import is_erpnext_installed, is_hrms_installed

	# ERPNext tools (CRM, selling, buying, finance, inventory, operations,
	# IDP, predictive analytics, session management)
	if is_erpnext_installed():
		import ai_chatbot.tools.buying
		import ai_chatbot.tools.crm
		import ai_chatbot.tools.crud
		import ai_chatbot.tools.finance.analytics
		import ai_chatbot.tools.finance.cash_flow
		import ai_chatbot.tools.finance.cfo
		import ai_chatbot.tools.finance.gl_analytics
		import ai_chatbot.tools.finance.profitability
		import ai_chatbot.tools.idp
		import ai_chatbot.tools.operations.create
		import ai_chatbot.tools.operations.search
		import ai_chatbot.tools.operations.update
		import ai_chatbot.tools.predictive.anomaly_detection
		import ai_chatbot.tools.predictive.cash_flow_forecast
		import ai_chatbot.tools.predictive.demand_forecast
		import ai_chatbot.tools.predictive.sales_forecast
		import ai_chatbot.tools.predictive.trends
		import ai_chatbot.tools.prescriptive.inventory_optimization
		import ai_chatbot.tools.prescriptive.pricing_optimization
		import ai_chatbot.tools.prescriptive.procurement_optimization
		import ai_chatbot.tools.prescriptive.production_optimization
		import ai_chatbot.tools.prescriptive.working_capital_optimization
		import ai_chatbot.tools.reports.finance
		import ai_chatbot.tools.reports.purchase
		import ai_chatbot.tools.reports.sales
		import ai_chatbot.tools.reports.stock
		import ai_chatbot.tools.selling
		import ai_chatbot.tools.session
		import ai_chatbot.tools.stock

	# Phase 5: HRMS tools (only if HRMS app is installed)
	if is_hrms_installed():
		import ai_chatbot.tools.hrms

	# Load external plugin tools via Frappe hooks
	for module_path in frappe.get_hooks("ai_chatbot_tool_modules") or []:
		try:
			frappe.get_module(module_path)
		except Exception as e:
			log_error(
				f"Failed to load AI Chatbot tool plugin: {module_path}: {e}",
				title="Plugin Loader",
			)
