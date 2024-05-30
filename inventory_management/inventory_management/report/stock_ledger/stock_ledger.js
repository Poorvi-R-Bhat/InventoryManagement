frappe.query_reports["Stock Ledger"] = {
    "filters": [
        {
            "fieldname": "from_date",
            "label": __("From Date"),
            "fieldtype": "Date",
            "default": frappe.datetime.add_months(frappe.datetime.get_today(), -1),
            "reqd": 1
        },
        {
            "fieldname": "to_date",
            "label": __("To Date"),
            "fieldtype": "Date",
            "default": frappe.datetime.get_today(),
            "reqd": 1
        },
        {
            "fieldname": "warehouse",
            "label": __("Warehouse"),
            "fieldtype": "Link",
            "options": "Warehouse",
            "get_query": function() {
                const company = frappe.query_report.get_filter_value("company");
                return {
                    "filters": {
                        "company": company
                    }
                };
            }
        },
        {
            "fieldname": "item_code",
            "label": __("Item"),
            "fieldtype": "Link",
            "options": "Item"
        },
        {
            "fieldname": "item_group",
            "label": __("Item Group"),
            "fieldtype": "Link",
            "options": "Item Group"
        }
    ],

    "formatter": function(value, row, column, data, default_formatter) {
        value = default_formatter(value, row, column, data);

        if (column.fieldname === "quantity" && data) {
            if (data.quantity < 0) {
                value = "<span style='color:red'>" + value + "</span>";
            } else if (data.quantity > 0) {
                value = "<span style='color:green'>" + value + "</span>";
            }
        }

        return value;
    }
};

erpnext.utils.add_inventory_dimensions("Stock Ledger", 10);
