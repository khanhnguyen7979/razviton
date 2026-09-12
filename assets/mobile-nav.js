(function () {
    "use strict";

    function initRazvitonMobileNav() {

        var nav = document.querySelector(".nav .n");
        if (!nav) return;

        var links = nav.querySelector(".links");
        if (!links) return;

        if (nav.querySelector(".mobile-menu-btn")) return;

        var button = document.createElement("button");

        button.type = "button";
        button.className = "mobile-menu-btn";
        button.setAttribute("aria-label", "Open navigation");
        button.setAttribute("aria-expanded", "false");

        button.innerHTML =
            "<span></span>" +
            "<span></span>" +
            "<span></span>";

        nav.insertBefore(button, links);

        function closeMenu() {
            links.classList.remove("open");
            button.setAttribute("aria-expanded", "false");
            button.setAttribute("aria-label", "Open navigation");
        }

        function openMenu() {
            links.classList.add("open");
            button.setAttribute("aria-expanded", "true");
            button.setAttribute("aria-label", "Close navigation");
        }

        button.addEventListener("click", function (event) {
            event.stopPropagation();

            if (links.classList.contains("open")) {
                closeMenu();
            } else {
                openMenu();
            }
        });

        links.querySelectorAll("a").forEach(function (link) {
            link.addEventListener("click", closeMenu);
        });

        document.addEventListener("click", function (event) {
            if (!nav.contains(event.target)) {
                closeMenu();
            }
        });

        document.addEventListener("keydown", function (event) {
            if (event.key === "Escape") {
                closeMenu();
            }
        });

        window.addEventListener("resize", function () {
            if (window.innerWidth > 900) {
                closeMenu();
            }
        });
    }

    if (document.readyState === "loading") {
        document.addEventListener(
            "DOMContentLoaded",
            initRazvitonMobileNav
        );
    } else {
        initRazvitonMobileNav();
    }
})();