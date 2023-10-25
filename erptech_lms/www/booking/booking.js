frappe.ready(() => {
	$(".payment-form").on("submit", (e) => {
		generate_payment_link(e);
	});
});

const generate_payment_link = (e) => {
	e.preventDefault();
	let buttonElement = document.querySelector('.payment-form button.btn-pay');
	let country = buttonElement.getAttribute('data-country')
	let mobile_no = buttonElement.getAttribute('data-mobile_no')
	let email = buttonElement.getAttribute('data-email')
	let full_name = buttonElement.getAttribute('data-full_name')
	let doctype = buttonElement.getAttribute('data-doctype')
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
								enrolling_course(doctype, docname, mobile_no, full_name, country)
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
		enrolling_course(doctype, docname, mobile_no, full_name, country)
	}
};

const enrolling_course = (doctype, docname, mobile_no, full_name, country) => {
	let new_address = { billing_name: full_name }
	frappe.call({
		method: "lms.lms.utils.get_payment_options",
		// method: "erptech_lms.erptech_lms.utils.get_payment_options",
		args: {
			doctype: doctype,
			docname: docname,
			phone: mobile_no,
			country: country,
		},
		callback: (data) => {
			let options = data.message
			data.message.handlers = (response) => {
				console.log(response)
				handle_success(
					response,
					doctype,
					docname,
					new_address,
					data.message.order_id
				);
			};
			let rzp1 = new Razorpay(options);
			rzp1.open();
			// Instamojo.open(`https://test.instamojo.com/@sumit_fb76c/?embed=form&purpose=${options.purpose}&amount=${options.amount}&name=John+Doe&email=johndoe@example.com&phone=1234567890`, options);
			// Instamojo.open(`https://www.instamojo.com/@carvemylife/?embed=form&purpose=${options.purpose}&amount=${options.amount}&name=John+Doe&email=johndoe@example.com&phone=1234567890`, options);
		},
	});
}

const handle_success = (response, doctype, docname, address, order_id) => {
	frappe.call({
		method: "erptech_lms.erptech_lms.utils.verify_payment",
		args: {
			response: response,
			doctype: doctype,
			docname: docname,
			address: address,
			order_id: order_id,
		},
		callback: (data) => {
			frappe.show_alert({
				message: __("Payment Successful"),
				indicator: "green",
			});
			setTimeout(() => {
				window.location.href = data.message;
			}, 1000);
		},
	});
};

const change_currency = () => {
	$("#gst-message").removeClass("hide");
	let country = this.billing.get_value("country");
	if (exception_country.includes(country)) {
		update_price(original_price_formatted);
		return;
	}
	frappe.call({
		method: "lms.lms.utils.change_currency",
		args: {
			country: country,
			amount: amount,
			currency: currency,
		},
		callback: (data) => {
			let current_price = $(".total-price").text();
			if (current_price != data.message) {
				update_price(data.message);
			}
			if (!data.message.includes("INR")) {
				$("#gst-message").addClass("hide");
			}
		},
	});
};

const update_price = (price) => {
	$(".total-price").text(price);
	frappe.show_alert({
		message: "Total Price has been updated.",
		indicator: "yellow",
	});
};
