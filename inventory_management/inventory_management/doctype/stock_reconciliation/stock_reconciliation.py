import frappe
from frappe.model.document import Document

class StockReconciliation(Document):
    def on_submit(self):
        self.update_stock_ledger()

    def update_stock_ledger(self):
        # Iterate over each item in the child table 'stock_reconciliation_details'
        for item in self.get("stock_reconciliation_details"):
            # Fetch the existing stock ledger entry for the item and warehouse
            existing_entry = frappe.db.get_value("Stock Ledger Entry", {
                "item_code": item.item_code,
                "warehouse": item.warehouse
            }, ["name", "quantity"], as_dict=True)

            if existing_entry:
                # Update the existing stock ledger entry with the new quantity
                existing_quantity = float(existing_entry.quantity) if existing_entry.quantity else 0.0
                new_quantity = existing_quantity + item.quantity  # item.quantity should be a float or int

                if new_quantity < 0:
                    frappe.throw(f"Stock levels cannot go negative for item {item.item_code} in warehouse {item.warehouse}.")
                frappe.db.set_value("Stock Ledger Entry", existing_entry.name, "quantity", new_quantity)
                frappe.db.set_value("Stock Ledger Entry", existing_entry.name, "posting_date", self.posting_date)
                frappe.db.set_value("Stock Ledger Entry", existing_entry.name, "warehouse", item.warehouse)
                frappe.db.set_value("Stock Ledger Entry", existing_entry.name, "voucher_number", self.name)


            else:
                # Create a new stock ledger entry if it does not exist
                new_entry = frappe.get_doc({
                    "doctype": "Stock Ledger Entry",
                    "item_code": item.item_code,
                    "warehouse": item.warehouse,
                    "quantity": item.quantity,
                    "rate": item.rate,
                    "posting_date": self.posting_date,
                    "voucher_number": self.name
                })
                new_entry.insert()

    def on_cancel(self):
        # Reverse the stock adjustments when the reconciliation entry is cancelled
        self.reverse_stock_ledger()

    def reverse_stock_ledger(self):
        for item in self.get("stock_reconciliation_details"):
            existing_entry = frappe.db.get_value("Stock Ledger Entry", {
            "item_code": item.item_code,
            "warehouse": item.warehouse
        }, ["name", "quantity"], as_dict=True)

        if existing_entry:
            # Ensure the quantity from the database is treated as a float
            existing_quantity = float(existing_entry.quantity) if existing_entry.quantity else 0.0
            new_quantity = existing_quantity - item.quantity
            if new_quantity < 0:
                frappe.throw("Reversing this entry would result in negative stock for item: {}".format(item.item_code))
            frappe.db.set_value("Stock Ledger Entry", existing_entry.name, "quantity", new_quantity)
