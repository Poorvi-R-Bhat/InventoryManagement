import frappe
from typing import List, Dict, Any
from frappe import _
from frappe.utils import flt
from frappe.query_builder import DocType, Field
from frappe.query_builder.functions import Cast

def execute(filters: Dict[str, Any] = None) -> List[Dict[str, Any]]:
    columns, data = [], []

    columns = get_columns()
    data = get_data(filters)

    return columns, data

def get_columns():
    return [
        {"label": _("Posting Date"), "fieldname": "posting_date", "fieldtype": "Date", "width": 100},
        {"label": _("Item Code"), "fieldname": "item_code", "fieldtype": "Link", "options": "Item", "width": 100},
        {"label": _("Warehouse"), "fieldname": "warehouse", "fieldtype": "Link", "options": "Warehouse", "width": 100},
        {"label": _("Quantity"), "fieldname": "quantity", "fieldtype": "Float", "width": 100},
        {"label": _("Rate"), "fieldname": "rate", "fieldtype": "Currency", "width": 100},
        {"label": _("Balance Qty"), "fieldname": "balance_qty", "fieldtype": "Float", "width": 100},
        {"label": _("Voucher Number"), "fieldname": "voucher_number", "fieldtype": "Link", "options": "Stock Entry", "width": 100},
        {"label": _("In Qty"), "fieldname": "in_qty", "fieldtype": "Float", "width": 100},
        {"label": _("Out Qty"), "fieldname": "out_qty", "fieldtype": "Float", "width": 100},
        {"label": _("In Rate"), "fieldname": "in_rate", "fieldtype": "Currency", "width": 100},
        {"label": _("Out Rate"), "fieldname": "out_rate", "fieldtype": "Currency", "width": 100},
        {"label": _("In Value"), "fieldname": "in_val", "fieldtype": "Currency", "width": 100},
        {"label": _("Out Value"), "fieldname": "out_val", "fieldtype": "Currency", "width": 100},
        {"label": _("Balance Value"), "fieldname": "balance_val", "fieldtype": "Currency", "width": 100},
    ]

def get_data(filters: Dict[str, Any]) -> List[Dict[str, Any]]:
    sl_entries = get_stock_ledger_entries(filters)
    balance_qty = 0
    balance_val = 0
    data = []

    for entry in sl_entries:
        in_qty = flt(entry.get("quantity")) if entry.get("quantity") > 0 else 0
        out_qty = -flt(entry.get("quantity")) if entry.get("quantity") < 0 else 0
        in_val = in_qty * flt(entry.get("rate"))
        out_val = out_qty * flt(entry.get("rate"))
        balance_qty += flt(entry.get("quantity"))
        balance_val += flt(entry.get("quantity")) * flt(entry.get("rate"))

        data.append({
            "posting_date": entry.get("posting_date"),
            "item_code": entry.get("item_code"),
            "warehouse": entry.get("warehouse"),
            "quantity": entry.get("quantity"),
            "rate": entry.get("rate"),
            "balance_qty": balance_qty,
            "voucher_number": entry.get("voucher_number"),
            "in_qty": in_qty,
            "out_qty": out_qty,
            "in_rate": entry.get("rate") if in_qty else 0,
            "out_rate": entry.get("rate") if out_qty else 0,
            "in_val": in_val,
            "out_val": out_val,
            "balance_val": balance_val,
        })

    return data

def get_stock_ledger_entries(filters: Dict[str, Any]) -> List[Dict[str, Any]]:
    sle = DocType("Stock Ledger Entry")

    query = (
        frappe.qb.from_(sle)
        .select(
            sle.posting_date.as_("date"),
            sle.item_code,
            sle.warehouse,
            Cast(sle.quantity, 'DECIMAL(10, 2)').as_("quantity"),
            sle.rate,
            sle.voucher_number,
            sle.posting_date
        )
    )

    if filters.get("from_date"):
        query = query.where(sle.posting_date >= filters.get("from_date"))
    if filters.get("to_date"):
        query = query.where(sle.posting_date <= filters.get("to_date"))
    if filters.get("item_code"):
        query = query.where(sle.item_code == filters.get("item_code"))
    if filters.get("warehouse"):
        query = query.where(sle.warehouse == filters.get("warehouse"))

    query = query.orderby(sle.posting_date).orderby(sle.creation)

    return query.run(as_dict=True)
