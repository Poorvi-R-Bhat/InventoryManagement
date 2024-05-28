import frappe
from typing import List, Dict, Any
from frappe import _

def execute(filters: Dict[str, Any] = None) -> List[Dict[str, Any]]:
    columns, data = [], []
    
    columns = [
        {"label": _("Date"), "fieldname": "date", "fieldtype": "Datetime", "width": 150},
        {"label": _("Item Code"), "fieldname": "item_code", "fieldtype": "Link", "options": "Item", "width": 100},
        {"label": _("Warehouse"), "fieldname": "warehouse", "fieldtype": "Link", "options": "Warehouse", "width": 100},
        {"label": _("Quantity"), "fieldname": "quantity", "fieldtype": "Float", "width": 100},
        {"label": _("Rate"), "fieldname": "rate", "fieldtype": "Currency", "width": 100},
        {"label": _("Balance Qty"), "fieldname": "balance_qty", "fieldtype": "Float", "width": 100},
        {"label": _("Voucher Number"), "fieldname": "voucher_number", "fieldtype": "Link", "options": "Stock Entry", "width": 100},
        {"label": _("Posting Date"), "fieldname": "posting_date", "fieldtype": "Date", "width": 100},
    ]
    
    sl_entries = get_stock_ledger_entries(filters)
    
    balance_qty = 0
    for entry in sl_entries:
        balance_qty += entry.get("quantity")
        data.append({
            "date": entry.get("date"),
            "item_code": entry.get("item_code"),
            "warehouse": entry.get("warehouse"),
            "quantity": entry.get("quantity"),
            "rate": entry.get("rate"),
            "balance_qty": balance_qty,
            "voucher_number": entry.get("voucher_number"),
            "posting_date": entry.get("posting_date"),
        })
    
    return columns, data

def get_stock_ledger_entries(filters: Dict[str, Any]) -> List[Dict[str, Any]]:
    conditions = []
    if filters.get("from_date"):
        conditions.append(f"posting_date >= '{filters.get('from_date')}'")
    if filters.get("to_date"):
        conditions.append(f"posting_date <= '{filters.get('to_date')}'")
    if filters.get("item_code"):
        conditions.append(f"item_code = '{filters.get('item_code')}'")
    if filters.get("warehouse"):
        conditions.append(f"warehouse = '{filters.get('warehouse')}'")
    
    condition_str = " AND ".join(conditions) if conditions else "1=1"
    
    query = f"""
        SELECT
            posting_date as date,
            item_code,
            warehouse,
            CAST(quantity AS DECIMAL(10, 2)) as quantity,
            rate,
            voucher_number,
            posting_date
        FROM
            `tabStock Ledger Entry`
        WHERE
            {condition_str}
        ORDER BY
            posting_date, creation
    """
    
    return frappe.db.sql(query, as_dict=1)
