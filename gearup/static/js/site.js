function gmailAuthenticate() {
	$.ajax({
		type: "GET",
		url: "ajax/gmailAuthenticate",
		success: function (data) {
			console.log("Done");
		},
	});
}

function initDisableOnSubmit(formSelector, buttonSelector) {
	const forms = document.querySelectorAll(formSelector);
	forms.forEach((form) => {
		form.querySelectorAll("input, select").forEach((el) => {
			el.addEventListener("keydown", (e) => {
				if (e.key === "Enter") {
					e.preventDefault();
				}
			});
		});
		form.addEventListener("submit", () => {
			const submitButton = form.querySelector(buttonSelector);
			if (submitButton) {
				submitButton.disabled = true;
				submitButton.classList.add("opacity-50", "cursor-not-allowed");
				submitButton.innerHTML = '<span class="loading loading-infinity loading-lg text-black"></span>';
			}
		});
	});
}
