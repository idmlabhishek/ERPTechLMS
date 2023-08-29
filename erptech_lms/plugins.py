import frappe

def show_custom_signup():
	if frappe.db.get_single_value(
		"LMS Settings", "terms_of_use"
	) or frappe.db.get_single_value("LMS Settings", "privacy_policy"):
		return "erptech_lms/templates/signup-form.html"
	return "frappe/templates/signup.html"