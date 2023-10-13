frappe.ready(() => {
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