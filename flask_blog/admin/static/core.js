"use strict";

{
    // Determine the order in which the themes will be cycled:
    //   -> if dark by default, toggle from auto to light and back to dark
    //   -> if light by default, toggle from auto to dark and back to light
    const prefersDark = window.matchMedia("(prefers-color-scheme: dark)").matches;
    const themeCycleOrder = prefersDark ? ["auto", "light", "dark"] : ["auto", "dark", "light"];

    const toggleIconByTheme = {
       "auto": "bi-circle-half",
       "light": "bi-sun-fill",
       "dark": "bi-moon-fill",
    };

    function getCurrentTheme() {
        let theme = localStorage.getItem("admin-theme");

        if (theme !== "auto" && theme !== "light" && theme !== "dark") {
            theme = "auto";
        }

        return theme;
    }

    function applyTheme(theme) {
        if (theme === "auto") {
            delete document.documentElement.dataset.theme;
        }
        else {
            document.documentElement.dataset.theme = theme;
        }

        localStorage.setItem("admin-theme", theme);
    }

    function cycleTheme() {
        const currentTheme = getCurrentTheme();
        let currentThemeIndex = themeCycleOrder.indexOf(currentTheme);

        const newThemeIndex = (currentThemeIndex + 1) % themeCycleOrder.length;
        applyTheme(themeCycleOrder[newThemeIndex]);
    }

    function cycleToggleIcon(iconElement) {
        const currentTheme = getCurrentTheme();

        const allThemes = Object.keys(toggleIconByTheme);
        for (let i = 0; i < allThemes.length; i++) {
            const iconClass = toggleIconByTheme[allThemes[i]];
            if (allThemes[i] === currentTheme) {
                iconElement.classList.add(iconClass);
            }
            else {
                iconElement.classList.remove(iconClass);
            }
        }
    }

    window.addEventListener("load", function() {
        const toggle = document.querySelector("#theme-toggle");
        if (toggle !== undefined) {
            toggle.addEventListener("click", function(event) {
                cycleTheme();
                cycleToggleIcon(event.target);
            });

            cycleToggleIcon(toggle);
        }

        applyTheme(getCurrentTheme());
    });
}
