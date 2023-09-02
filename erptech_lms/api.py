import frappe
import requests
from frappe import _
from frappe.utils import cint, escape_html, random_string
from frappe.website.utils import is_signup_disabled

from lms.lms.utils import get_chapters, can_create_courses

@frappe.whitelist(allow_guest=True)
def sign_up(email, full_name, signup_phone, verify_terms, exact_business, signup_employees, user_types, yearly_sales, user_experience, new_password):
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

	user = frappe.get_doc(
		{
			"doctype": "User",
			"email": email,
			"first_name": escape_html(full_name),
			"signup_phone": signup_phone,
			"number_of_employees": signup_employees,
			"user_experience": user_experience,
			"exact_business": exact_business,
			"verify_terms": verify_terms,
			"user_types": user_types,
			"yearly_sales": yearly_sales,
			"country": "",
			"enabled": 1,
			# "new_password": random_string(10),
			"new_password": new_password,
			"user_type": "Website User",
		}
	)
	user.flags.ignore_permissions = True
	user.flags.ignore_password_policy = True
	user.insert()
	set_country_from_ip(None, user.name)

	# set default signup role as per Portal Settings
	default_role = frappe.db.get_value("Portal Settings", None, "default_role")
	if default_role:
		user.add_roles(default_role)

	return 1, _("Registered successfully")
	# if user.flags.email_sent:
	# 	return 1, _("Please check your email for verification")
	# else:
	# 	return 2, _("Please ask your administrator to verify your sign-up")

def set_country_from_ip(login_manager=None, user=None):
	if not user and login_manager:
		user = login_manager.user
	user_country = frappe.db.get_value("User", user, "country")
	# if user_country:
	#    return
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

@frappe.whitelist()
def new_enrollment(doctype, member_type, course, member):
	todo = frappe.get_doc({
		"doctype":doctype,
		"member_type":member_type,
		"course":course,
		"member":member
	})
	todo.insert(ignore_permissions = True)
	return todo.name

@frappe.whitelist()
def save_course(
	tags,
	title,
	short_introduction,
	video_link,
	description,
	course,
	custom_manufacturer,
	custom_wholeseller,
	custom_retail,
	custom_services,
	published,
	upcoming,
	image=None,
	paid_course=False,
	course_price=None,
	currency=None,
):
	if not can_create_courses():
		return

	if course:
		doc = frappe.get_doc("LMS Course", course)
	else:
		doc = frappe.get_doc({"doctype": "LMS Course"})
	doc.update(
		{
			"title": title,
			"short_introduction": short_introduction,
			"video_link": video_link,
			"image": image,
			"description": description,
			"tags": tags,
			"custom_manufacturer": cint(custom_manufacturer),
			"custom_wholeseller": cint(custom_wholeseller),
			"custom_retail": cint(custom_retail),
			"custom_services": cint(custom_services),
			"published": cint(published),
			"upcoming": cint(upcoming),
			"paid_course": cint(paid_course),
			"course_price": course_price,
			"currency": currency,
		}
	)
	doc.save(ignore_permissions=True)
	return doc.name


@frappe.whitelist(allow_guest=True)
def courses_completion_data():
	all_membership = frappe.db.count("LMS Enrollment")
	completed = frappe.db.count("LMS Enrollment", {"progress": ["like", "%100%"]})

	return {
		"labels": ["Completed", "In Progress"],
		"datasets": [
			{
				"name": "Course Completion",
				"values": [completed, all_membership - completed],
			}
		],
	}