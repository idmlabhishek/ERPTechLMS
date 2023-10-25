frappe.ready(() => {
	$("#signup_name").css("color", "#000");
	$("#signup_email").css("color", "#000");
	$("#signup_phone").css("color", "#000");
	$("#signup_employees").css("color", "#000");
	$("#new_password").css("color", "#000");
	$("#exact_business").css("color", "#000");
	$("#user_types").on("change", (e) => {
		if (e.target.value) {
			$("#user_types").css("color", "#000");
		} else {
			$("#user_types").css("color", "#7f7979");
		}

	});
	$("#yearly_sales").on("change", (e) => {
		if (e.target.value) {
			$("#yearly_sales").css("color", "#000");
		} else {
			$("#yearly_sales").css("color", "#7f7979");
		}

	});
	$("#user_experience").on("change", (e) => {
		if (e.target.value) {
			$("#user_experience").css("color", "#000");
		} else {
			$("#user_experience").css("color", "#7f7979");
		}

	});
	$(".payment-form").on("submit", (e) => {
		enrolling_link(e);
	});
});

const enrolling_link = (e) => {
	e.preventDefault();
	let buttonElement = document.querySelector('.payment-form button.btn-pay');
	let mobile_no = buttonElement.getAttribute('data-mobile_no')
	let email = buttonElement.getAttribute('data-email')
	let full_name = buttonElement.getAttribute('data-full_name')
	let docname = buttonElement.getAttribute('data-name')
	let isNotLogin = buttonElement.getAttribute('data-is_not_login')
	let user_types = $("#user_types").length ? $("#user_types").val() : "";
	let yearly_sales = $("#yearly_sales").length ? $("#yearly_sales").val() : "";
	let signup_employees = frappe.utils.xss_sanitise(($("#signup_employees").val() || "").trim());
	let new_password = frappe.utils.xss_sanitise(($("#new_password").val() || "").trim());
	let user_experience = $("#user_experience").length ? $("#user_experience").val() : "";
	let exact_business = frappe.utils.xss_sanitise(($("#exact_business").val() || "").trim());
	if (isNotLogin == "True") {
		full_name = frappe.utils.xss_sanitise(($("#signup_name").val() || "").trim());
		email = frappe.utils.xss_sanitise(($("#signup_email").val() || "").trim());
		mobile_no = frappe.utils.xss_sanitise(($("#signup_phone").val() || "").trim());
		frappe.call({
			method: "erptech_lms.erptech_lms.utils.create_new_user",
			args: {
				"full_name": full_name,
				"email": email,
				"mobile_no": mobile_no,
				"user_types": user_types,
				"yearly_sales": yearly_sales,
				"signup_employees": signup_employees,
				"new_password": new_password,
				"user_experience": user_experience,
				"exact_business": exact_business,
			},
			callback: (data) => {
				if (data.message && data.message[0] == 1) {
					frappe.call({
						method: "login",
						args: {
							usr: email,
							pwd: data.message[1],
							device: "desktop"
						},
						callback: (response) => {
							if (response.message === 'Logged In') {
								enrolling_course(docname)
							} else {
								alert('Login failed');
							}
						}
					});
				} else {
					alert(data.message[1]);
				}
			},
		})
	} else {
		enrolling_course(docname)
	}
};

const enrolling_course = (docname) => {
	frappe.call({
		method: "erptech_lms.erptech_lms.utils.create_membership",
		args: {
			course: docname,
			payment: null,
		},
		callback: (data) => {
			window.location.href = data.message;
		},
	});
}