import re
import string
import frappe
import json
import razorpay
import requests
import base64
from frappe import _
from frappe.desk.doctype.dashboard_chart.dashboard_chart import get_result
from frappe.utils import cint, escape_html, random_string
from frappe.desk.doctype.notification_log.notification_log import make_notification_logs
from frappe.website.utils import is_signup_disabled
from frappe.utils import (
	add_months,
	cint,
	cstr,
	flt,
	fmt_money,
	format_date,
	get_datetime,
	getdate,
	validate_phone_number,
	ceil,
)
from frappe.utils.dateutils import get_period
from lms.lms.md import find_macros, markdown_to_html

RE_SLUG_NOTALLOWED = re.compile("[^a-z0-9]+")

def get_client():
	settings = frappe.get_single("LMS Settings")
	razorpay_key = settings.razorpay_key
	razorpay_secret = settings.get_password("razorpay_secret", raise_exception=True)

	if not razorpay_key and not razorpay_secret:
		frappe.throw(
			_(
				"There is a problem with the payment gateway. Please contact the Administrator to proceed."
			)
		)

	return razorpay.Client(auth=(razorpay_key, razorpay_secret))


def check_multicurrency(amount, currency, country=None):
	show_usd_equivalent = frappe.db.get_single_value("LMS Settings", "show_usd_equivalent")
	exception_country = frappe.get_all(
		"Payment Country", filters={"parent": "LMS Settings"}, pluck="country"
	)
	apply_rounding = frappe.db.get_single_value("LMS Settings", "apply_rounding")
	country = country or frappe.db.get_value(
		"Address", {"email_id": frappe.session.user}, "country"
	)

	if not show_usd_equivalent or currency == "USD":
		return amount, currency

	if not country or (exception_country and country in exception_country):
		return amount, currency

	exchange_rate = get_current_exchange_rate(currency, "USD")
	amount = amount * exchange_rate
	currency = "USD"

	if apply_rounding and amount % 100 != 0:
		amount = ceil(amount + 100 - amount % 100)

	return amount, currency


def apply_gst(amount, country=None):
	gst_applied = False
	apply_gst = frappe.db.get_single_value("LMS Settings", "apply_gst")

	if not country:
		country = frappe.db.get_value("User", frappe.session.user, "country")

	if apply_gst and country == "India":
		gst_applied = True
		amount = amount * 1.18

	return amount, gst_applied



@frappe.whitelist()
def verify_payment(response, doctype, docname, address, order_id):
	response = json.loads(response)
	client = get_client()
	# client.utility.verify_payment_signature(
	# 	{
	# 		"razorpay_order_id": order_id,
	# 		"razorpay_payment_id": response["razorpay_payment_id"],
	# 		"razorpay_signature": response["razorpay_signature"],
	# 	}
	# )
	payment = record_payment(address, response, client, doctype, docname)
	if doctype == "LMS Course":
		return create_membership(docname, payment)
	else:
		return add_student_to_batch(docname, payment)


def record_payment(address, response, client, doctype, docname):
	address = frappe._dict(json.loads(address))

	payment_details = get_payment_details(doctype, docname, address)
	payment_doc = frappe.new_doc("LMS Payment")
	payment_doc.update(
		{
			"member": frappe.session.user,
			"billing_name": address.billing_name,
			"payment_received": 1,
			# "order_id": response["razorpay_order_id"],
			# "payment_id": response["razorpay_payment_id"],
			"order_id": response["paymentId"],
			"payment_id": response["paymentId"],
			"amount": payment_details["amount"],
			"currency": payment_details["currency"],
			"amount_with_gst": payment_details["amount_with_gst"],
			"gstin": address.gstin,
			"pan": address.pan,
		}
	)
	payment_doc.save(ignore_permissions=True)
	return payment_doc.name


def get_payment_details(doctype, docname, address):
	amount_field = "course_price" if doctype == "LMS Course" else "amount"
	amount = frappe.db.get_value(doctype, docname, amount_field)
	currency = frappe.db.get_value(doctype, docname, "currency")
	amount_with_gst = 0

	amount, currency = check_multicurrency(amount, currency)
	if currency == "INR" and address.country == "India":
		amount_with_gst, gst_applied = apply_gst(amount, address.country)

	return {
		"amount": amount,
		"currency": currency,
		"amount_with_gst": amount_with_gst,
	}

@frappe.whitelist()
def create_membership(course, payment):
	membership = frappe.new_doc("LMS Enrollment")
	membership.update(
		{"member": frappe.session.user, "course": course, "payment": payment}
	)
	membership.save(ignore_permissions=True)
	return f"/courses/{course}/learn/1.1"


def add_student_to_batch(batchname, payment):
	student = frappe.new_doc("Batch Student")
	student.update(
		{
			"student": frappe.session.user,
			"payment": payment,
			"parent": batchname,
			"parenttype": "LMS Batch",
			"parentfield": "students",
		}
	)
	student.save(ignore_permissions=True)
	return f"/batches/{batchname}"

def get_current_exchange_rate(source, target="USD"):
	url = f"https://api.frankfurter.app/latest?from={source}&to={target}"

	response = requests.request("GET", url)
	details = response.json()
	return details["rates"][target]


@frappe.whitelist(allow_guest=True)
def create_new_user(full_name, email, mobile_no, user_types=None, yearly_sales=None, signup_employees=None, password=None, user_experience=None, exact_business=None):
	if is_signup_disabled():
		frappe.throw(_("Sign Up is disabled"), _("Not Allowed"))

	user = frappe.db.get("User", {"email": email})
	if user:
		if user.enabled:
			return 0, _("Already Registered. Please click Login below to login")
		else:
			return 0, _("Registered but disabled")
	else:
		if frappe.db.get_creation_count("User", 60) > 300:
			frappe.respond_as_web_page(
				_("Temporarily Disabled"),
				_(
					"Too many users signed up recently, so the registration is disabled. Please try back in an hour"
				),
				http_status_code=429,
			)

	new_password = password if password else random_string(10)
	user = frappe.get_doc(
		{
			"doctype": "User",
			"email": email,
			"first_name": escape_html(full_name),
			"mobile_no": mobile_no,
			"enabled": 1,
			"user_type": "Website User",
			"number_of_employees": signup_employees,
			"user_experience": user_experience,
			"exact_business": exact_business,
			"user_types": user_types,
			"yearly_sales": yearly_sales,
			"new_password": new_password,
		}
	)
	user.flags.ignore_permissions = True
	user.flags.ignore_password_policy = True
	user.insert()

	# add roles
	user.add_roles("System Manager")
	user.add_roles("LMS Student")

	# set_country_from_ip(None, user.name)
	return 1, _(new_password)

def set_country_from_ip(login_manager=None, user=None):
	if not user and login_manager:
		user = login_manager.user
	frappe.db.set_value("User", user, "country", get_country_code())
	return

def get_country_code():
	ip = frappe.local.request_ip
	res = requests.get(f"http://ip-api.com/json/{ip}")

	try:
		data = res.json()
		if data.get("status") != "fail":
			return frappe.db.get_value("Country", {"code": data.get("countryCode")}, "name")
	except Exception:
		pass
	return


def get_details(doctype, docname):
	if doctype == "LMS Course":
		details = frappe.db.get_value(
			"LMS Course",
			docname,
			["name", "title", "paid_course", "currency", "course_price as amount"],
			as_dict=True,
		)
		if not details.paid_course:
			frappe.throw(_("This course is free."))
	else:
		details = frappe.db.get_value(
			"LMS Batch",
			docname,
			["name", "title", "paid_batch", "currency", "amount"],
			as_dict=True,
		)
		if not details.paid_batch:
			frappe.throw(_("To join this batch, please contact the Administrator."))

	return details

def create_order(client, amount, currency):
	try:
		return client.order.create(
			{
				"amount": amount * 100,
				"currency": currency,
			}
		)
	except Exception as e:
		frappe.throw(
			_("Error during payment: {0}. Please contact the Administrator.").format(e)
		)
		
@frappe.whitelist(allow_guest=True)
def get_payment_options(doctype, docname, phone, country):
	if not frappe.db.exists(doctype, docname):
		frappe.throw(_("Invalid document provided."))

	validate_phone_number(phone, True)
	details = get_details(doctype, docname)
	details.amount, details.currency = check_multicurrency(
		details.amount, details.currency, country
	)
	if details.currency == "INR":
		details.amount, details.gst_applied = apply_gst(details.amount, country)

	client = get_client()
	order = create_order(client, details.amount, details.currency)

	options = {
		"key_id": frappe.db.get_single_value("LMS Settings", "razorpay_key"),
		"name": frappe.db.get_single_value("Website Settings", "app_name"),
		"description": _("Payment for {0} course").format(details["title"]),
		"order_id": order["id"],
		"amount": order["amount"] * 100,
		"currency": order["currency"],
		"prefill": {
			"name": frappe.db.get_value("User", frappe.session.user, "full_name"),
			"email": frappe.session.user,
			"contact": phone,
		},
	}
	return options


@frappe.whitelist(allow_guest=True)
def get_payment_options_instamojo(doctype, docname, phone, country):
	if not frappe.db.exists(doctype, docname):
		frappe.throw(_("Invalid document provided."))

	validate_phone_number(phone, True)
	details = get_details(doctype, docname)
	details.amount, details.currency = check_multicurrency(
		details.amount, details.currency, country
	)
	if details.currency == "INR":
		details.amount, details.gst_applied = apply_gst(details.amount, country)

	options = {
		"purpose": details.title,
		"amount": details.amount,
		"name": frappe.db.get_value("User", frappe.session.user, "full_name"),
		"email": frappe.session.user,
		"phone": phone,
	}
	return options