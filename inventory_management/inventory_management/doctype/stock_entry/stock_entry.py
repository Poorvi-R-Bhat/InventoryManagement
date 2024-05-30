import frappe
from frappe.model.document import Document
from frappe.utils import today, flt
from frappe import _

class StockEntry(Document):
    def validate(self):
        self.calculate_totals()
        if not self.get('stock_entry_details'):
            frappe.throw(_("At least one item must be entered in the stock entry details."))

    def calculate_totals(self):
        total_quantity = 0.0
        total_rate1 = 0.0
        for item in self.get('stock_entry_details'):
            item_quantity = flt(item.quantity)
            item_price = flt(item.item_price)
            total_quantity += item_quantity
            total_rate1 += item_quantity * item_price
        self.total_quantity = total_quantity
        self.total_rate1 = total_rate1

    def on_submit(self):
        self.process_stock_entries()
        frappe.msgprint(_("Stock Ledger Entries have been created."))

    def process_stock_entries(self):
        for item in self.get('stock_entry_details'):
            flow = "in" if self.stock_entry_type == "Receive" else "out"
            entry = self.update_stock_ledger(item, flow)
            if entry:
                self.update_moving_average(item.item_code, item.to_warehouse if flow == "in" else item.from_warehouse)

    def update_stock_ledger(self, item, flow):
        return self._update_stock_ledger_entry(item, flow)

    def update_moving_average(self, item_code, warehouse):
        StockLedgerEntry = frappe.qb.DocType("Stock Ledger Entry")

        stock_entries = (
            frappe.qb.from_(StockLedgerEntry)
            .select(StockLedgerEntry.quantity, StockLedgerEntry.rate)
            .where(
                (StockLedgerEntry.item_code == item_code) &
                (StockLedgerEntry.warehouse == warehouse)
            )
        ).run(as_dict=True)
        
        total_qty = sum(flt(entry['quantity']) for entry in stock_entries)
        total_value = sum(flt(entry['quantity']) * flt(entry['rate']) for entry in stock_entries)
        
        new_avg_rate = total_value / total_qty if total_qty else 0
        
        frappe.db.set_value("Item", item_code, "moving_average_rate", new_avg_rate)

    def on_cancel(self):
        for item in self.get('stock_entry_details'):
            if self.stock_entry_type == "Receive":
                if not item.get('to_warehouse'):
                    frappe.throw(_("Warehouse not specified for item code {0} on cancellation of Receive type entry").format(item.item_code))
                self.update_stock_ledger(item, "out")
            elif self.stock_entry_type == "Transfer":
                if not item.get('from_warehouse'):
                    frappe.throw(_("Warehouse not specified for item code {0} on cancellation of Transfer type entry").format(item.item_code))
                self.update_stock_ledger(item, "in")

    def _update_stock_ledger_entry(self, item, flow, warehouse=None):
        item_quantity = flt(item.quantity)
        item_price = flt(item.item_price)
        warehouse = warehouse or (item.to_warehouse if flow == "in" else item.from_warehouse)

        if not warehouse:
            frappe.throw(_("Warehouse not specified for item code {0} in flow {1}").format(item.item_code, flow))

        new_qty = item_quantity if flow == "in" else -item_quantity
        StockLedgerEntry = frappe.qb.DocType("Stock Ledger Entry")

        existing_entry = (
            frappe.qb.from_(StockLedgerEntry)
            .select(StockLedgerEntry.name, StockLedgerEntry.quantity, StockLedgerEntry.rate)
            .where(
                (StockLedgerEntry.item_code == item.item_code) &
                (StockLedgerEntry.warehouse == warehouse)
            )
        ).run(as_dict=True)

        if existing_entry:
            ledger_entry = frappe.get_doc("Stock Ledger Entry", existing_entry[0]['name'])
            existing_quantity = flt(existing_entry[0]['quantity'])
            existing_rate = flt(existing_entry[0]['rate']) if existing_entry[0]['rate'] else item_price

            if flow == "in":
                new_total_qty = existing_quantity + new_qty
                new_total_value = (existing_quantity * existing_rate) + (new_qty * item_price)
                new_avg_rate = new_total_value / new_total_qty if new_total_qty else 0.0
                ledger_entry.rate = new_avg_rate
            else:
                ledger_entry.rate = existing_rate  
            
            ledger_entry.quantity = existing_quantity + new_qty
            ledger_entry.posting_date = self.posting_date
            ledger_entry.save()
            return ledger_entry
        else:
            ledger_entry = frappe.new_doc("Stock Ledger Entry")
            ledger_entry.item_code = item.item_code
            ledger_entry.warehouse = warehouse
            ledger_entry.quantity = new_qty
            ledger_entry.posting_date = self.posting_date
            ledger_entry.rate = item_price  # initial rate for the first entry
            ledger_entry.voucher_number = self.name
            ledger_entry.insert()
            return ledger_entry
