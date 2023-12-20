import frappe
from frappe import _
from frappe.utils import nowdate
 
 
@frappe.whitelist(allow_guest=True)
def create_sales_order(**kwargs):
	data = list(frappe.form_dict.values())
	print('data ', data)
 
	# Create Customer
	customer = None
	exit_customer = frappe.get_value("Customer", filters={"name": data[4]}, fieldname='name')
	if exit_customer is None:
		customer = frappe.new_doc('Customer')
		customer.customer_group = "Individual"
		customer.territory = "India"
		customer.customer_name = data[4]
		customer.custom_customer_phone = data[5]
		customer.custom_customer_email = data[4]
		customer.insert(ignore_permissions=True)
	
	print("Customer Update")
	# Create Sales Order
	new_sales_order = frappe.new_doc("Sales Order")
	new_sales_order.customer = exit_customer if customer is None else customer.name
	new_sales_order.transaction_date = nowdate()
	new_sales_order.set("items", [{"item_code": "Courses", "delivery_date": nowdate(), "qty": 1, "rate": data[2]}])
	new_sales_order.insert(ignore_permissions=True)
	print("invoice Created")
 
	# Create Payment Entry
	# new_payment_entry = frappe.new_doc("Payment Entry")
	# new_payment_entry.customer = exit_customer if customer is None else customer.name
	# new_payment_entry.transaction_date = nowdate()
	# new_payment_entry.insert(ignore_permissions=True)
	# print("Payment Entry Created")