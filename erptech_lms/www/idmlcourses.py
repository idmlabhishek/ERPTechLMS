import frappe
from frappe import _
from lms.lms.utils import (
	can_create_courses,
	check_profile_restriction,
	get_restriction_details,
	has_course_moderator_role,
	get_courses_under_review,
	get_average_rating,
	has_course_instructor_role
)
from lms.overrides.user import get_enrolled_courses, get_authored_courses

def get_context(context):
	context.no_cache = 1
	context.manufacturer_courses = get_courses('custom_manufacturer')
	context.wholeseller_courses = get_courses('custom_wholeseller')
	context.retail_courses = get_courses('custom_retail')
	context.services_courses = get_courses('custom_services')
	context.small_business_courses = get_courses('custom_small_business')
	context.enrolled_courses = (
		get_enrolled_courses()["in_progress"] + get_enrolled_courses()["completed"]
	)
	context.created_courses = get_authored_courses(None, False)
	context.review_courses = get_courses_under_review()
	context.restriction = check_profile_restriction()

	portal_course_creation = frappe.db.get_single_value(
		"LMS Settings", "portal_course_creation"
	)
	context.show_creators_section = (
		True
		if portal_course_creation == "Anyone"
		or has_course_moderator_role()
		or has_course_instructor_role()
		else False
	)
	context.show_review_section = (
		has_course_moderator_role() and frappe.session.user != "Guest"
	)

	if context.restriction:
		context.restriction_details = get_restriction_details()

	context.metatags = {
		"title": _("Course List"),
		"image": frappe.db.get_single_value("Website Settings", "banner_image"),
		"description": "This page lists all the courses published on our website",
		"keywords": "All Courses, Courses, Learn",
	}


def get_courses(filter):
	courses = frappe.get_all(
		"LMS Course",
		filters={filter: True},
		fields=[
			"name",
			"custom_manufacturer",
			"custom_wholeseller",
			"custom_retail",
			"custom_services",
			"custom_small_business",
			"title",
			"short_introduction",
			"image",
			"paid_course",
			"course_price",
			"currency",
			"creation",
		],
	)

	filter_courses = []
	for course in courses:
		course.avg_rating = get_average_rating(course.name) or 0
		filter_courses.append(course)
		
	return filter_courses