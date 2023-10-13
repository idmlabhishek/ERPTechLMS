import frappe
from frappe import _
from frappe import get_doc

def get_context(context):
	module = frappe.form_dict.module
	docname = frappe.form_dict.modulename
	doctype = "LMS Course" if module == "course" else "LMS Batch"

	context.isLogin = frappe.session.user == "Guest"
	user_doc = get_doc("User", frappe.session.user)
	context.mobile_no = user_doc.get("mobile_no")
	context.email = user_doc.get("email")
	context.full_name = user_doc.get("full_name")
	context.country = user_doc.get("country")

	context.module = module
	context.docname = docname
	context.doctype = doctype