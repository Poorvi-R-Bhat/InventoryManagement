frappe.query_reports["Stock Balance"] = {
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
            "options": "Warehouse"
        },
        {
            "fieldname": "item_code",
            "label": __("Item"),
            "fieldtype": "Link",
            "options": "Item"
        },
        {
            "fieldname": "include_uom",
            "label": __("Include UOM"),
            "fieldtype": "Link",
            "options": "UOM"
        }
    ],

    "formatter": function(value, row, column, data, default_formatter) {
        value = default_formatter(value, row, column, data);

        console.log('Value:', value, 'Row:', row, 'Column:', column, 'Data:', data); 

        if (column.fieldname === "out_qty" && data && data.out_qty > 0) {
            value = "<span style='color:red'>" + value + "</span>";
        } else if (column.fieldname === "in_qty" && data && data.in_qty > 0) {
            value = "<span style='color:green'>" + value + "</span>";
        }

        return value;
    }
};

erpnext.utils.add_inventory_dimensions("Stock Balance", 8);
