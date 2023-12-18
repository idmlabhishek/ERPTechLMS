import frappe
from frappe import _
from frappe.utils import nowdate
 
 
@frappe.whitelist(allow_guest=True)
def getSalesInvoice(**kwargs):
	data = list(frappe.form_dict.values())
 
	# Create Customer
	customer = None
	exit_customer = frappe.get_value("Customer", filters={"customer_name": data[2]}, fieldname='name')
	if exit_customer is None:
		customer = frappe.new_doc('Customer')
		customer.customer_group = "Individual"
		customer.territory = "India"
		customer.customer_name = data[2]
		customer.insert(ignore_permissions=True)
	
	print("Customer Update")
	# Create Sales Invoice
	new_sales_invoice = frappe.new_doc("Sales Order")
	new_sales_invoice.customer = exit_customer if customer is None else customer.name
	new_sales_invoice.transaction_date = nowdate()
	new_sales_invoice.set("items", [{"item_code": "Courses", "delivery_date": nowdate(), "qty": 1, "rate": data[3]}])
	new_sales_invoice.insert(ignore_permissions=True)
	print("invoice Created")