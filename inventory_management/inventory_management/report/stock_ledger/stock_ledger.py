import frappe
from typing import List, Dict, Any
from frappe import _
from frappe.utils import flt
from frappe.query_builder import Order

def execute(filters: Dict[str, Any] = None) -> List[Dict[str, Any]]:
    columns, data = get_columns(), get_data(filters)
    return columns, data

def get_columns():
    return [
        {"label": _("Item Code"), "fieldname": "item_code", "fieldtype": "Link", "options": "Item", "width": 100},
        {"label": _("Warehouse"), "fieldname": "warehouse", "fieldtype": "Link", "options": "Warehouse", "width": 100},
        {"label": _("Quantity"), "fieldname": "quantity", "fieldtype": "Float", "width": 100},
        {"label": _("Rate"), "fieldname": "rate", "fieldtype": "Currency", "width": 100},
        {"label": _("Balance Qty"), "fieldname": "balance_qty", "fieldtype": "Float", "width": 100},
        {"label": _("Voucher Number"), "fieldname": "voucher_number", "fieldtype": "Link", "options": "Stock Entry", "width": 100},
        {"label": _("Posting Date"), "fieldname": "posting_date", "fieldtype": "Date", "width": 100},
        {"label": _("In Qty"), "fieldname": "in_qty", "fieldtype": "Float", "width": 100},
        {"label": _("Out Qty"), "fieldname": "out_qty", "fieldtype": "Float", "width": 100},
        {"label": _("Avg Rate"), "fieldname": "avg_rate", "fieldtype": "Currency", "width": 100},
        {"label": _("Valuation Rate"), "fieldname": "valuation_rate", "fieldtype": "Currency", "width": 100},
        {"label": _("Balance Value"), "fieldname": "balance_value", "fieldtype": "Currency", "width": 100},
    ]

def get_data(filters: Dict[str, Any]) -> List[Dict[str, Any]]:
    sl_entries = get_stock_ledger_entries(filters)
    balance_qty, balance_value = {}, {}
    data = []

    for entry in sl_entries:
        key = (entry.get("item_code"), entry.get("warehouse"))
        balance_qty[key] = balance_qty.get(key, 0) + flt(entry.get("quantity"))
        balance_value[key] = balance_value.get(key, 0) + flt(entry.get("quantity")) * flt(entry.get("rate"))

        in_qty = flt(entry.get("quantity")) if flt(entry.get("quantity")) > 0 else 0
        out_qty = -flt(entry.get("quantity")) if flt(entry.get("quantity")) < 0 else 0
        avg_rate = flt(balance_value[key]) / flt(balance_qty[key]) if flt(balance_qty[key]) else 0
        valuation_rate = flt(entry.get("rate"))

        data.append({
            "item_code": entry.get("item_code"),
            "warehouse": entry.get("warehouse"),
            "quantity": entry.get("quantity"),
            "rate": entry.get("rate"),
            "balance_qty": balance_qty[key],
            "voucher_number": entry.get("voucher_number"),
            "posting_date": entry.get("posting_date"),
            "in_qty": in_qty,
            "out_qty": out_qty,
            "avg_rate": avg_rate,
            "valuation_rate": valuation_rate,
            "balance_value": balance_value[key],
        })

    return data

def get_stock_ledger_entries(filters: Dict[str, Any]) -> List[Dict[str, Any]]:
    sle = frappe.qb.DocType("Stock Ledger Entry")
    query = (
        frappe.qb.from_(sle)
        .select(
            sle.item_code,
            sle.warehouse,
            sle.quantity,
            sle.rate,
            sle.voucher_number,
            sle.posting_date,
        )
        .where(sle.docstatus < 2)
        .orderby(sle.posting_date, Order.asc)
        .orderby(sle.creation, Order.asc)
    )

    if filters.get("from_date"):
        query = query.where(sle.posting_date >= filters.get("from_date"))
    if filters.get("to_date"):
        query = query.where(sle.posting_date <= filters.get("to_date"))
    if filters.get("item_code"):
        query = query.where(sle.item_code == filters.get("item_code"))
    if filters.get("warehouse"):
        query = query.where(sle.warehouse == filters.get("warehouse"))

    return query.run(as_dict=True)
