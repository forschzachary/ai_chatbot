# AI Chatbot — Tools Reference

Complete reference for all 76 registered business intelligence tools. Each tool is callable by the AI through natural language prompts.

All parameters are optional unless marked **(required)**. Date parameters default to the current fiscal year. Company defaults to the user's default company.

---

## CRM (5 tools)

### get_lead_statistics
Get statistics about leads including count, status breakdown, and conversion rates.

| Parameter | Type | Description |
|-----------|------|-------------|
| from_date | string | Start date (YYYY-MM-DD) |
| to_date | string | End date (YYYY-MM-DD) |
| company | string | Company name |

### get_opportunity_analytics
Get sales opportunity pipeline with stages and values.

| Parameter | Type | Description |
|-----------|------|-------------|
| status | string | Filter by status (Open, Converted, Lost, Quotation, Replied, Closed) |
| company | string | Company name |

### get_lead_conversion_rate
Get lead conversion rate showing how many leads converted to opportunities or customers.

| Parameter | Type | Description |
|-----------|------|-------------|
| from_date | string | Start date (YYYY-MM-DD) |
| to_date | string | End date (YYYY-MM-DD) |
| company | string | Company name |

### get_lead_source_analysis
Analyze leads by source/campaign to identify the best-performing lead channels.

| Parameter | Type | Description |
|-----------|------|-------------|
| from_date | string | Start date (YYYY-MM-DD) |
| to_date | string | End date (YYYY-MM-DD) |
| company | string | Company name |

### get_sales_funnel
Get sales funnel showing conversion from leads to opportunities to quotations to sales orders.

| Parameter | Type | Description |
|-----------|------|-------------|
| from_date | string | Start date (YYYY-MM-DD) |
| to_date | string | End date (YYYY-MM-DD) |
| company | string | Company name |

---

## Sales / Selling (7 tools)

### get_sales_analytics
Get sales analytics including revenue, orders, and growth trends.

| Parameter | Type | Description |
|-----------|------|-------------|
| from_date | string | Start date (YYYY-MM-DD) |
| to_date | string | End date (YYYY-MM-DD) |
| customer | string | Filter by customer name |
| company | string | Company name |

### get_top_customers
Get top customers by revenue.

| Parameter | Type | Description |
|-----------|------|-------------|
| limit | integer | Number of customers to return (default 10) |
| from_date | string | Start date (YYYY-MM-DD) |
| to_date | string | End date (YYYY-MM-DD) |
| company | string | Company name |

### get_transaction_trend
Get monthly transaction trend for sales or purchases over time.

| Parameter | Type | Description |
|-----------|------|-------------|
| months | integer | Number of months to show (default 12) |
| transaction_type | string | 'sales' or 'purchase' (default: sales) |
| company | string | Company name |

### get_sales_by_territory
Get sales breakdown by territory/region.

| Parameter | Type | Description |
|-----------|------|-------------|
| from_date | string | Start date (YYYY-MM-DD) |
| to_date | string | End date (YYYY-MM-DD) |
| company | string | Company name |

### get_by_item_group
Get transaction breakdown by item group/product category (sales or purchase).

| Parameter | Type | Description |
|-----------|------|-------------|
| from_date | string | Start date (YYYY-MM-DD) |
| to_date | string | End date (YYYY-MM-DD) |
| transaction_type | string | 'sales' or 'purchase' (default: sales) |
| limit | integer | Number of item groups to return (default 10) |
| company | string | Company name |

### report_sales_register
Run ERPNext Sales Register — shows all sales transactions for a period with invoiced amount and tax details. Each tax type gets a separate column.

| Parameter | Type | Description |
|-----------|------|-------------|
| company | string | Company name |
| from_date | string | Start date (YYYY-MM-DD) |
| to_date | string | End date (YYYY-MM-DD) |
| customer | string | Filter by customer name |
| customer_group | string | Filter by customer group |

### report_item_wise_sales_register
Run ERPNext Item-wise Sales Register — shows all sales transactions broken down by item with rate, quantity, amount, and tax details.

| Parameter | Type | Description |
|-----------|------|-------------|
| company | string | Company name |
| from_date | string | Start date (YYYY-MM-DD) |
| to_date | string | End date (YYYY-MM-DD) |
| customer | string | Filter by customer name |
| item_code | string | Filter by specific item code |
| item_group | string | Filter by item group |

---

## Buying / Purchase (4 tools)

### get_purchase_analytics
Get purchase analytics including spending, orders, and supplier performance.

| Parameter | Type | Description |
|-----------|------|-------------|
| from_date | string | Start date (YYYY-MM-DD) |
| to_date | string | End date (YYYY-MM-DD) |
| company | string | Company name |

### get_supplier_performance
Analyze supplier performance metrics.

| Parameter | Type | Description |
|-----------|------|-------------|
| supplier | string | Supplier name |
| company | string | Company name |

### report_purchase_register
Run ERPNext Purchase Register — shows all purchase transactions for a period with invoiced amount and tax details. Each tax type gets a separate column.

| Parameter | Type | Description |
|-----------|------|-------------|
| company | string | Company name |
| from_date | string | Start date (YYYY-MM-DD) |
| to_date | string | End date (YYYY-MM-DD) |
| supplier | string | Filter by supplier name |
| supplier_group | string | Filter by supplier group |

### report_item_wise_purchase_register
Run ERPNext Item-wise Purchase Register — shows all purchase transactions broken down by item with rate, quantity, amount, and tax details.

| Parameter | Type | Description |
|-----------|------|-------------|
| company | string | Company name |
| from_date | string | Start date (YYYY-MM-DD) |
| to_date | string | End date (YYYY-MM-DD) |
| supplier | string | Filter by supplier name |
| item_code | string | Filter by specific item code |
| item_group | string | Filter by item group |

---

## Finance — Custom Analytics (8 tools)

### get_financial_overview
High-level financial overview with key KPIs sourced from ERPNext's P&L, Balance Sheet, AR, and AP reports: revenue, total expenses, net profit, cash position, receivables, and payables. Returns BI metric cards and a bar chart.

| Parameter | Type | Description |
|-----------|------|-------------|
| from_date | string | Start date (YYYY-MM-DD) |
| to_date | string | End date (YYYY-MM-DD) |
| company | string | Company name |

### get_cfo_dashboard
Comprehensive CFO dashboard with BI metric cards (Revenue, Net Profit, Cash, AR, AP with YoY comparisons), financial highlights, KPIs (net margin, gross profit ratio, current ratio, quick ratio from ERPNext Financial Ratios report), cash flow summary, receivables/payables aging, and balance sheet snapshot.

| Parameter | Type | Description |
|-----------|------|-------------|
| from_date | string | Start date (YYYY-MM-DD) |
| to_date | string | End date (YYYY-MM-DD) |
| company | string | Company name |

### get_monthly_comparison
Month-over-month comparison of revenue, expenses, and net profit with variance tracking.

| Parameter | Type | Description |
|-----------|------|-------------|
| months | integer | Number of recent months to compare (default 6, max 12) |
| company | string | Company name |

### get_cash_flow
Payment Entry-based cash flow analysis with monthly trend. Shows inflow, outflow, and net cash flow by payment type.

| Parameter | Type | Description |
|-----------|------|-------------|
| months | integer | Number of months to analyze (default 12) |
| company | string | Company name |

### get_bank_balance
Current bank and cash account balances from General Ledger.

| Parameter | Type | Description |
|-----------|------|-------------|
| account | string | Specific bank or cash account name |
| company | string | Company name |

### get_gl_summary
General Ledger summary with flexible grouping by root type, account type, party type, voucher type, or account name. Uses GL entries for authoritative accounting data.

| Parameter | Type | Description |
|-----------|------|-------------|
| group_by | string | Grouping: root_type, account_type, party_type, voucher_type, account_name (default: root_type) |
| root_type | string | Filter: Asset, Liability, Equity, Income, Expense |
| account_type | string | Filter: Bank, Cash, Receivable, Payable, etc. |
| party_type | string | Filter: Customer, Supplier, Employee |
| party | string | Filter by specific party name |
| from_date | string | Start date (YYYY-MM-DD) |
| to_date | string | End date (YYYY-MM-DD) |
| company | string | Company name |

### get_profitability
Profitability analysis by customer, item, or territory with revenue, cost, and margin calculations.

| Parameter | Type | Description |
|-----------|------|-------------|
| analysis_type | string | 'customer', 'item', or 'territory' (default: customer) |
| from_date | string | Start date (YYYY-MM-DD) |
| to_date | string | End date (YYYY-MM-DD) |
| limit | integer | Number of results to return (default 10) |
| company | string | Company name |

### get_multidimensional_summary
Generate a multi-dimensional summary grouped by any combination of dimensions and time periods. Supports built-in dimensions (company, territory, customer_group, customer, item_group, cost_center, department) and any custom Accounting Dimensions.

| Parameter | Type | Description |
|-----------|------|-------------|
| metric | string | What to measure: revenue, expenses, profit, orders (default: revenue) |
| group_by | array | Dimensions to group by, in order (max 3). E.g. ["territory", "customer_group"] |
| period | string | Time grouping: monthly, quarterly, yearly (default: quarterly) |
| from_date | string | Start date (YYYY-MM-DD) |
| to_date | string | End date (YYYY-MM-DD) |
| company | string | Company name |

---

## Finance — ERPNext Standard Reports (14 tools)

These tools are thin wrappers around ERPNext's standard report `execute()` functions (Phase 12B). They source data directly from ERPNext reports for consistency with the numbers shown in the ERPNext UI.

### report_general_ledger
Run ERPNext General Ledger report — a detailed view of all accounting transactions posted to each account. Shows posting date, account, party, debit, credit, and running balance for every GL Entry.

| Parameter | Type | Description |
|-----------|------|-------------|
| company | string | Company name |
| from_date | string | Start date (YYYY-MM-DD) |
| to_date | string | End date (YYYY-MM-DD) |
| account | string | Filter by specific account name (e.g. 'Cash - TC', 'Debtors - TC') |
| party_type | string | Filter by party type: Customer, Supplier, Employee |
| party | string | Filter by specific party name |

### report_accounts_receivable
Run ERPNext Accounts Receivable report — tracks invoice-wise outstanding amounts from Customers with aging analysis (0-30, 31-60, 61-90, 90+ days).

| Parameter | Type | Description |
|-----------|------|-------------|
| company | string | Company name |
| report_date | string | Report date (YYYY-MM-DD, default: today) |
| customer | string | Filter by specific customer name |

### report_accounts_receivable_summary
Run ERPNext Accounts Receivable Summary — shows total outstanding amount per Customer with aging buckets (0-30, 31-60, 61-90, 90+ days).

| Parameter | Type | Description |
|-----------|------|-------------|
| company | string | Company name |
| report_date | string | Report date (YYYY-MM-DD, default: today) |
| customer | string | Filter by specific customer name |

### report_accounts_payable
Run ERPNext Accounts Payable report — tracks invoice-wise outstanding amounts owed to Suppliers with aging analysis (0-30, 31-60, 61-90, 90+ days).

| Parameter | Type | Description |
|-----------|------|-------------|
| company | string | Company name |
| report_date | string | Report date (YYYY-MM-DD, default: today) |
| supplier | string | Filter by specific supplier name |

### report_accounts_payable_summary
Run ERPNext Accounts Payable Summary — shows total outstanding amount per Supplier with aging buckets (0-30, 31-60, 61-90, 90+ days).

| Parameter | Type | Description |
|-----------|------|-------------|
| company | string | Company name |
| report_date | string | Report date (YYYY-MM-DD, default: today) |
| supplier | string | Filter by specific supplier name |

### report_trial_balance
Run ERPNext Trial Balance report — lists account balances for all accounts (Ledger and Group) for a reporting period. Shows opening balance, period debit/credit, and closing balance.

| Parameter | Type | Description |
|-----------|------|-------------|
| company | string | Company name |
| fiscal_year | string | Fiscal year name (e.g. '2025-2026') |
| from_date | string | Start date (YYYY-MM-DD) |
| to_date | string | End date (YYYY-MM-DD) |
| cost_center | string | Filter by cost center |
| project | string | Filter by project |

### report_profit_and_loss
Run ERPNext Profit and Loss Statement — summarizes all revenues and expenses for a period, showing net profit/loss. Supports monthly, quarterly, half-yearly, or yearly periodicity.

| Parameter | Type | Description |
|-----------|------|-------------|
| company | string | Company name |
| from_date | string | Start date (YYYY-MM-DD) |
| to_date | string | End date (YYYY-MM-DD) |
| periodicity | string | Period grouping: Monthly, Quarterly, Half-Yearly, Yearly (default: Yearly) |
| cost_center | string | Filter by cost center |
| project | string | Filter by project |

### report_balance_sheet
Run ERPNext Balance Sheet — states assets, liabilities, and equity at a particular point in time. Can run across multiple periods to compare values.

| Parameter | Type | Description |
|-----------|------|-------------|
| company | string | Company name |
| from_date | string | Start date (YYYY-MM-DD) |
| to_date | string | End date (YYYY-MM-DD) |
| periodicity | string | Period grouping: Monthly, Quarterly, Half-Yearly, Yearly (default: Yearly) |
| cost_center | string | Filter by cost center |
| project | string | Filter by project |

### report_cash_flow
Run ERPNext Cash Flow Statement — shows incoming and outgoing cash based on GL entries. Shows operating, investing, and financing activities.

| Parameter | Type | Description |
|-----------|------|-------------|
| company | string | Company name |
| from_date | string | Start date (YYYY-MM-DD) |
| to_date | string | End date (YYYY-MM-DD) |
| periodicity | string | Period grouping: Monthly, Quarterly, Half-Yearly, Yearly (default: Yearly) |

### report_consolidated_financial_statement
Run ERPNext Consolidated Financial Statement — shows a consolidated view of Balance Sheet, Profit and Loss, or Cash Flow for a group company by merging subsidiary financial statements.

| Parameter | Type | Description |
|-----------|------|-------------|
| company | string | Parent company name |
| report | string | Report type: 'Profit and Loss Statement', 'Balance Sheet', or 'Cash Flow' (default: Profit and Loss Statement) |
| from_date | string | Start date (YYYY-MM-DD) |
| to_date | string | End date (YYYY-MM-DD) |
| periodicity | string | Period grouping: Monthly, Quarterly, Half-Yearly, Yearly (default: Yearly) |
| presentation_currency | string | Currency for the report (e.g. 'USD') |

### report_consolidated_trial_balance
Run ERPNext Consolidated Trial Balance — shows a consolidated view of trial balance across selected companies.

| Parameter | Type | Description |
|-----------|------|-------------|
| company | string | Parent company name (or comma-separated list) |
| fiscal_year | string | Fiscal year name (e.g. '2025-2026') |
| from_date | string | Start date (YYYY-MM-DD) |
| to_date | string | End date (YYYY-MM-DD) |
| presentation_currency | string | Currency for the report (e.g. 'USD') |

### report_account_balance
Run ERPNext Account Balance report — shows group account balances on a specific date. Useful for a quick snapshot by root type or account type.

| Parameter | Type | Description |
|-----------|------|-------------|
| company | string | Company name |
| report_date | string | Report date (YYYY-MM-DD, default: today) |
| root_type | string | Filter: Asset, Liability, Equity, Income, Expense |
| account_type | string | Filter: Bank, Cash, Receivable, Payable, etc. |

### report_financial_ratios
Run ERPNext Financial Ratios report — calculates key financial ratios across periods. Includes Liquidity Ratios (Current Ratio, Quick Ratio), Solvency Ratios (Debt Equity, Gross Profit, Net Profit, ROA, ROE), and Turnover Ratios (Fixed Asset, Debtor, Creditor, Inventory Turnover).

| Parameter | Type | Description |
|-----------|------|-------------|
| company | string | Company name |
| from_fiscal_year | string | Start fiscal year name (e.g. '2024-2025') |
| to_fiscal_year | string | End fiscal year name (e.g. '2025-2026') |
| periodicity | string | Period grouping: Monthly, Quarterly, Half-Yearly, Yearly (default: Yearly) |

### report_budget_variance
Run ERPNext Budget Variance report — compares budgeted amounts against actuals for each account, grouped by period.

| Parameter | Type | Description |
|-----------|------|-------------|
| company | string | Company name |
| fiscal_year | string | Fiscal year name (e.g. '2025-2026') |
| budget_against | string | Budget dimension: Cost Center, Department, or Project (default: Cost Center) |
| period | string | Period grouping: Monthly, Quarterly, Half-Yearly, Yearly (default: Yearly) |

---

## Finance — Session Management (2 tools)

### set_include_subsidiaries
Enable or disable child company inclusion for the current chat session.

| Parameter | Type | Description |
|-----------|------|-------------|
| include | boolean | **(required)** True to include subsidiaries, False to exclude |

### set_target_currency
Set or reset the display currency for the current chat session.

| Parameter | Type | Description |
|-----------|------|-------------|
| currency | string | Currency code (e.g. 'USD', 'EUR'). Empty to reset to default. |

---

## Inventory / Stock (7 tools)

### get_inventory_summary
Get inventory summary including stock levels and valuation.

| Parameter | Type | Description |
|-----------|------|-------------|
| warehouse | string | Filter by warehouse |
| company | string | Company name |

### get_low_stock_items
Get items with stock below reorder level.

| Parameter | Type | Description |
|-----------|------|-------------|
| limit | integer | Maximum items to return (default 50) |
| company | string | Company name |

### get_stock_movement
Get stock movement (in/out quantities) for items over a period.

| Parameter | Type | Description |
|-----------|------|-------------|
| item_code | string | Filter by specific item code |
| warehouse | string | Filter by specific warehouse |
| from_date | string | Start date (YYYY-MM-DD) |
| to_date | string | End date (YYYY-MM-DD) |
| company | string | Company name |

### get_stock_ageing
Get age of stock in warehouse — how long items have been sitting.

| Parameter | Type | Description |
|-----------|------|-------------|
| warehouse | string | Filter by specific warehouse |
| company | string | Company name |

### report_stock_ledger
Run ERPNext Stock Ledger report — a detailed record of all stock movements. Shows inward/outward transactions related to manufacturing, purchasing, selling, and stock transfers.

| Parameter | Type | Description |
|-----------|------|-------------|
| company | string | Company name |
| from_date | string | Start date (YYYY-MM-DD) |
| to_date | string | End date (YYYY-MM-DD) |
| warehouse | string | Filter by warehouse name |
| item_code | string | Filter by specific item code |
| item_group | string | Filter by item group |

### report_stock_balance
Run ERPNext Stock Balance report — provides a real-time summary of current inventory quantities, valuation rates, and total stock value broken down by item and warehouse.

| Parameter | Type | Description |
|-----------|------|-------------|
| company | string | Company name |
| from_date | string | Start date (YYYY-MM-DD) |
| to_date | string | End date (YYYY-MM-DD) |
| warehouse | string | Filter by warehouse name |
| item_code | string | Filter by specific item code |
| item_group | string | Filter by item group |

### report_stock_ageing
Run ERPNext Stock Ageing report — monitors how long inventory has been in warehouses, helping identify slow-moving or obsolete items.

| Parameter | Type | Description |
|-----------|------|-------------|
| company | string | Company name |
| to_date | string | Report date (YYYY-MM-DD, default: today) |
| warehouse | string | Filter by warehouse name |
| item_code | string | Filter by specific item code |

---

## HRMS (6 tools)

Requires the HRMS app to be installed.

### get_employee_count
Get employee headcount with optional breakdown by department, status, or designation.

| Parameter | Type | Description |
|-----------|------|-------------|
| department | string | Filter by department |
| status | string | Active, Inactive, Suspended, or Left (default: Active) |
| designation | string | Filter by designation/job title |
| company | string | Company name |

### get_attendance_summary
Get attendance summary showing present, absent, on leave, half day, and WFH counts.

| Parameter | Type | Description |
|-----------|------|-------------|
| from_date | string | Start date (YYYY-MM-DD, default: current month start) |
| to_date | string | End date (YYYY-MM-DD, default: current month end) |
| department | string | Filter by department |
| company | string | Company name |

### get_leave_balance
Get leave balance showing allocated, used, and remaining leaves by type.

| Parameter | Type | Description |
|-----------|------|-------------|
| employee | string | Employee ID or name (omit for company-wide summary) |
| leave_type | string | Filter by leave type (e.g. 'Casual Leave', 'Sick Leave') |
| company | string | Company name |

### get_payroll_summary
Get payroll summary with total gross pay, deductions, and net pay.

| Parameter | Type | Description |
|-----------|------|-------------|
| from_date | string | Start date (YYYY-MM-DD, default: current month start) |
| to_date | string | End date (YYYY-MM-DD, default: current month end) |
| company | string | Company name |

### get_department_wise_salary
Get salary distribution by department showing gross and net pay per department.

| Parameter | Type | Description |
|-----------|------|-------------|
| from_date | string | Start date (YYYY-MM-DD, default: current month start) |
| to_date | string | End date (YYYY-MM-DD, default: current month end) |
| company | string | Company name |

### get_employee_turnover
Get employee turnover showing new hires vs exits with turnover rate.

| Parameter | Type | Description |
|-----------|------|-------------|
| from_date | string | Start date (YYYY-MM-DD) |
| to_date | string | End date (YYYY-MM-DD) |
| company | string | Company name |

---

## IDP — Intelligent Document Processing (3 tools)

### extract_document_data
Extract structured data from an uploaded document (invoice, PO, quotation, receipt) and map it to an ERPNext DocType schema. Handles any language, any format (PDF, image, Excel, Word), non-uniform headers, and naming discrepancies. Returns extracted fields for user review before record creation.

| Parameter | Type | Description |
|-----------|------|-------------|
| file_url | string | **(required)** Frappe file URL of the uploaded document |
| target_doctype | string | **(required)** ERPNext DocType to map to (Sales Invoice, Purchase Invoice, Quotation, Sales Order, Purchase Order, Delivery Note, Purchase Receipt) |
| company | string | Company name |
| output_language | string | Language for extracted output values (default: per settings or English) |

### create_from_extracted_data
Create an ERPNext record from previously extracted document data. Only called after user confirms the extraction.

| Parameter | Type | Description |
|-----------|------|-------------|
| extracted_data_json | string | **(required)** JSON string of extracted data from extract_document_data |
| target_doctype | string | **(required)** ERPNext DocType to create |
| company | string | Company name |
| create_missing_masters | string | Set to 'true' to auto-create missing Customer, Supplier, Item, UOM records |
| item_defaults_json | string | JSON with defaults for missing Items: {"is_stock_item": 1, "is_fixed_asset": 0, "item_group": "Consumable"} |

### compare_document_with_record
Compare an uploaded document with an existing ERPNext record and highlight differences. Useful for reconciliation (e.g. vendor invoice vs Purchase Order).

| Parameter | Type | Description |
|-----------|------|-------------|
| file_url | string | **(required)** Frappe file URL of the document to compare |
| doctype | string | **(required)** ERPNext DocType of the existing record |
| docname | string | **(required)** Name/ID of the existing record |
| company | string | Company name |

---

## Predictive Analytics (6 tools)

### analyse_trend
Analyse historical trends in revenue, expenses, or item demand over time. Returns linear regression, growth rates, moving averages, seasonality detection, and a chart with trend line overlay.

| Parameter | Type | Description |
|-----------|------|-------------|
| metric | string | What to analyse: 'revenue' (Sales Invoice totals), 'expenses' (Purchase Invoice totals), 'demand' (item quantity — requires item_code). Default: 'revenue' |
| months | integer | Number of months of history to analyse (default 12, max 36) |
| item_code | string | Item code for demand trend analysis (only used when metric='demand') |
| company | string | Company name |

### forecast_revenue
Forecast future revenue based on historical sales invoice data. Uses statistical methods (moving average, exponential smoothing, Holt-Winters, trend analysis). Returns predictions with confidence intervals and chart.

| Parameter | Type | Description |
|-----------|------|-------------|
| months_ahead | integer | Months to forecast (default 3, max 12) |
| company | string | Company name |

### forecast_by_territory
Forecast revenue by territory/region. Runs separate forecasts for top territories with comparison chart.

| Parameter | Type | Description |
|-----------|------|-------------|
| months_ahead | integer | Months to forecast (default 3, max 6) |
| company | string | Company name |

### forecast_demand
Forecast future demand (quantity) for a specific item based on historical sales.

| Parameter | Type | Description |
|-----------|------|-------------|
| item_code | string | **(required)** Item code or item name to forecast |
| months_ahead | integer | Months to forecast (default 3, max 12) |
| company | string | Company name |

### forecast_cash_flow
Forecast future cash flow (inflows and outflows) based on historical Payment Entry data.

| Parameter | Type | Description |
|-----------|------|-------------|
| months_ahead | integer | Months to forecast (default 3, max 12) |
| company | string | Company name |

### detect_anomalies
Detect unusual transactions and patterns in financial data. Flags large amounts and new suppliers/customers with big first orders. Uses z-score and IQR methods.

| Parameter | Type | Description |
|-----------|------|-------------|
| from_date | string | Start date (YYYY-MM-DD) |
| to_date | string | End date (YYYY-MM-DD) |
| sensitivity | string | Detection sensitivity: low (z>3.0), medium (z>2.5, default), high (z>2.0) |
| company | string | Company name |

---

## Prescriptive Analytics (5 tools)

Optimisation and recommendation tools. Each builds on the underlying historical data and forecasts to suggest specific actions, with quantified expected impact where possible. Toggle via **Enable Prescriptive Tools** in Chatbot Settings (off by default).

### optimize_inventory
Recommend Economic Order Quantity (EOQ), safety stock, and reorder point for an item. Combines historical monthly demand with the item's lead time and valuation rate; reports expected annual carrying/order costs and a qualitative stockout risk for current stock.

| Parameter | Type | Description |
|-----------|------|-------------|
| item_code | string | **(required)** Item code or item name to optimise |
| service_level | string | Target service level: '90', '95' (default), or '99' |
| order_cost | number | Fixed cost per purchase order (default 50) |
| holding_cost_pct | number | Annual holding cost as a fraction of unit cost (default 0.25) |
| lead_time_days | integer | Override the item's lead_time_days |
| company | string | Company name |

### optimize_pricing
Estimate price elasticity of demand for an item from historical monthly price/quantity and recommend a profit-maximising price. Uses log-log OLS regression; returns elasticity, recommended price, expected volume/margin impact, and a confidence label derived from R².

| Parameter | Type | Description |
|-----------|------|-------------|
| item_code | string | **(required)** Item code or item name to analyse |
| months_back | integer | Months of history to use (default 12, max 36) |
| marginal_cost | number | Override the per-unit marginal cost (defaults to item valuation rate) |
| company | string | Company name |

### optimize_procurement
Recommend procurement-strategy improvements: supplier consolidation when top-5 share is below target, new-supplier risk flags for abnormally large first orders, and bulk-purchase candidates for frequently-ordered items. Returns a prioritised list of recommendations plus a top-suppliers Pareto chart.

| Parameter | Type | Description |
|-----------|------|-------------|
| months_back | integer | Months of purchase history to analyse (default 12, max 24) |
| company | string | Company name |

### optimize_production_schedule
Build a monthly production schedule for an item using the Silver-Meal lot-sizing heuristic. Forecasts demand from historical Sales Invoices, groups demand into lots that balance setup against holding cost, and optionally caps each month at a user-supplied capacity (with overflow rolling forward).

| Parameter | Type | Description |
|-----------|------|-------------|
| item_code | string | **(required)** Item code or item name to schedule |
| months_ahead | integer | Months to schedule (default 6, max 12) |
| setup_cost | number | Fixed cost per production run (default 100) |
| holding_cost_pct | number | Annual holding cost as a fraction of unit cost (default 0.25) |
| monthly_capacity | number | Optional max units producible per month — excess rolls to next month |
| company | string | Company name |

### optimize_working_capital
Compute the cash conversion cycle (DSO + DIO − DPO) from current ERPNext balances and recommend payment-terms, credit-policy, or inventory-reduction actions when metrics drift from configurable targets. Each recommendation includes an estimated cash-freed amount.

| Parameter | Type | Description |
|-----------|------|-------------|
| months_back | integer | Months of sales/purchase history used to compute daily flow (default 12, max 24) |
| target_dso | number | Target Days Sales Outstanding (default 45) |
| target_dpo | number | Target Days Payable Outstanding (default 30) |
| target_dio | number | Target Days Inventory Outstanding (default 60) |
| company | string | Company name |

---

## Operations — Create (3 tools)

### create_lead
Create a new Lead in ERPNext.

| Parameter | Type | Description |
|-----------|------|-------------|
| first_name | string | **(required)** First name of the lead |
| last_name | string | Last name |
| company_name | string | Company/organization name |
| email_id | string | Email address |
| mobile_no | string | Mobile phone number |
| source | string | Lead source (Website, Referral, Campaign, Cold Calling) |
| company | string | Company name |

### create_opportunity
Create a new Opportunity in ERPNext. Accepts document ID or human name as party_name.

| Parameter | Type | Description |
|-----------|------|-------------|
| party_name | string | **(required)** Customer or Lead reference (ID or name) |
| opportunity_from | string | Source type: Customer or Lead (default: Lead) |
| opportunity_amount | number | Expected opportunity value |
| currency | string | Currency code |
| sales_stage | string | Sales stage (Prospecting, Qualification, Proposal/Price Quote) |
| company | string | Company name |

### create_todo
Create a new ToDo task in ERPNext.

| Parameter | Type | Description |
|-----------|------|-------------|
| description | string | **(required)** Task description |
| allocated_to | string | Email of user to assign to (defaults to current user) |
| date | string | Due date (YYYY-MM-DD) |
| priority | string | Low, Medium (default), or High |

---

## Operations — Search (3 tools)

### search_customers
Search for customers by name, customer group, or territory.

| Parameter | Type | Description |
|-----------|------|-------------|
| query | string | Search text for customer name |
| customer_group | string | Filter by customer group |
| territory | string | Filter by territory |
| limit | integer | Maximum results (default 10) |
| company | string | Company name |

### search_items
Search for items by name, item code, or item group.

| Parameter | Type | Description |
|-----------|------|-------------|
| query | string | Search text for item name or code |
| item_group | string | Filter by item group |
| limit | integer | Maximum results (default 10) |
| company | string | Company name |

### search_documents
Search for documents of any DocType by name or status.

| Parameter | Type | Description |
|-----------|------|-------------|
| doctype | string | **(required)** DocType to search (e.g. 'Sales Invoice', 'Lead') |
| query | string | Search text for document name |
| status | string | Filter by status |
| limit | integer | Maximum results (default 10) |
| company | string | Company name |

---

## Operations — Update (3 tools)

### update_lead_status
Update the status of an existing Lead.

| Parameter | Type | Description |
|-----------|------|-------------|
| lead_name | string | **(required)** Lead document name/ID |
| status | string | **(required)** New status: Lead, Open, Replied, Opportunity, Quotation, Lost Quotation, Interested, Converted, Do Not Contact |

### update_opportunity_status
Update the status of an existing Opportunity.

| Parameter | Type | Description |
|-----------|------|-------------|
| opportunity_name | string | **(required)** Opportunity document name/ID |
| status | string | **(required)** New status: Open, Quotation, Converted, Lost, Replied, Closed |

### update_todo
Update an existing ToDo task.

| Parameter | Type | Description |
|-----------|------|-------------|
| todo_name | string | **(required)** ToDo document name/ID |
| status | string | Open, Closed, or Cancelled |
| priority | string | Low, Medium, or High |
| description | string | Updated task description |
| date | string | Updated due date (YYYY-MM-DD) |

---

## Summary

| Category | Tools |
|----------|-------|
| CRM | 5 |
| Sales / Selling (custom + report) | 7 |
| Buying / Purchase (custom + report) | 4 |
| Finance — Custom Analytics | 8 |
| Finance — ERPNext Standard Reports | 14 |
| Finance — Session Management | 2 |
| Inventory / Stock (custom + report) | 7 |
| HRMS | 6 |
| IDP (Document Processing) | 3 |
| Predictive Analytics | 6 |
| Prescriptive Analytics | 5 |
| Operations (Create, Search, Update) | 9 |
| **Total** | **76** |
