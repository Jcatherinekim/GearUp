module.exports = {
	content: [
		"./gearup/templates/**/*.html",
		"./gearup/templates/components/**/*.html",
		"./gearup/static/**/*.js",
		"./gear/templates/**/*.html",
		"./gear/templates/add/**/*.html",
		"./users/templates/**/*.html",
		"./users/templates/librarian/**/*.html",
	],
	theme: {
		extend: {
			fontFamily: {
				sans: ["Inter", "sans-serif"],
			},
		},
	},
	plugins: [require("daisyui"), require("@tailwindcss/forms")],
	daisyui: {
		themes: [
			{
				customtheme: {
					primary: "#0081ce",
					success: "oklch(70% 0.143782 166.8156)",
					secondary: "#7b92b2",
					accent: "#67cba0",
					neutral: "#181a2a",
					"neutral-content": "#edf2f7",
					"base-100": "oklch(100% 0 0)",
					"base-content": "#181a2a",
					"rounded-box": "0.25rem",
					"rounded-btn": ".125rem",
					"rounded-badge": ".125rem",
					"tab-radius": "0.25rem",
					"animation-btn": "0",
					"animation-input": "0",
					"btn-focus-scale": "1",
				},
			},
		],
	},
};
