# Copyright (c) 2024, Poorvi Solutions and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import today

class StockEntry(Document):
    def validate(self):
        self.calculate_totals()
        if not self.get('stock_entry_details'):
            frappe.throw("At least one item must be entered in the stock entry details.")

    def calculate_totals(self):
        total_quantity = 0.0
        total_rate1 = 0.0
        for item in self.get('stock_entry_details'):
            item_quantity = float(item.quantity) if item.quantity else 0.0
            item_price = float(item.item_price) if item.item_price else 0.0
            total_quantity += item_quantity
            total_rate1 += item_quantity * item_price
        self.total_quantity = total_quantity
        self.total_rate1 = total_rate1

    def on_submit(self):
        self.process_stock_entries()
			# frappe.msgprint("Stock Ledger Entry has been created.")

    def process_stock_entries(self):
        for item in self.get('stock_entry_details'):
            flow = "in" if self.stock_entry_type == "Receive" else "out"
            entry = self.update_stock_ledger(item, flow)
            if entry:
                frappe.msgprint(f"Stock Ledger Entry {entry.name} has been created.")

    def update_stock_ledger(self, item, flow):
        item_quantity = float(item.quantity)
        item_price = float(item.item_price)
        warehouse = item.to_warehouse if flow == "in" else item.from_warehouse

        if not warehouse:
            frappe.throw(f"Warehouse not specified for item code {item.item_code} in flow {flow}")

        new_qty = item_quantity if flow == "in" else -item_quantity
        existing_entry = frappe.db.get_value("Stock Ledger Entry", {
            "item_code": item.item_code,
            "warehouse": warehouse
        }, ["name", "quantity"])

        if existing_entry:
            ledger_entry = frappe.get_doc("Stock Ledger Entry", existing_entry[0])
            existing_quantity = float(existing_entry[1]) if existing_entry[1] else 0.0
            existing_rate =  float(existing_entry[2]) if existing_entry[2] else item_price
            ledger_entry.quantity = existing_quantity + new_qty
            ledger_entry.posting_date = self.posting_date
            ledger_entry.rate = item_price
            ledger_entry.save()
            return ledger_entry
        else:
            ledger_entry = frappe.new_doc("Stock Ledger Entry")
            ledger_entry.item_code = item.item_code
            ledger_entry.warehouse = warehouse
            ledger_entry.quantity = new_qty
            ledger_entry.posting_date = self.posting_date
            ledger_entry.item_price1 = item_price
            ledger_entry.voucher_number = self.name
            ledger_entry.insert()
            return ledger_entry


def on_cancel(self):
    for item in self.get('stock_entry_details'):
        if self.stock_entry_type == "Receive":
            if not item.get('from_warehouse'):
                frappe.throw(f"Warehouse not specified for item code {item.item_code} on cancellation of Receive type entry")
            self.update_stock_ledger(item, "out", item.from_warehouse)
        elif self.stock_entry_type == "Transfer":
            if not item.get('to_warehouse'):
                frappe.throw(f"Warehouse not specified for item code {item.item_code} on cancellation of Transfer type entry")
            self.update_stock_ledger(item, "in", item.to_warehouse)