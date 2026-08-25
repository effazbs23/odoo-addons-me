/**
 * Pricelist up/down stepper inside the unified language/currency dropdown.
 * Navigates to /shop/change_pricelist/<id> without closing on button mousedown.
 */
(function () {
    "use strict";

    function getLinks(root) {
        return Array.prototype.slice.call(
            root.querySelectorAll("[data-kingdom-pl-links] a[data-pl-id]")
        );
    }

    function currentIndex(links, currentId) {
        if (!currentId) return 0;
        for (var i = 0; i < links.length; i++) {
            if (links[i].getAttribute("data-pl-id") === String(currentId)) {
                return i;
            }
        }
        return 0;
    }

    function onStepClick(ev) {
        var btn = ev.target.closest("[data-kingdom-pl-dir]");
        if (!btn) return;
        var root = btn.closest("[data-kingdom-pricelist-stepper]");
        if (!root) return;
        ev.preventDefault();
        ev.stopPropagation();

        var links = getLinks(root);
        if (links.length < 2) return;

        var currentEl = root.querySelector(".k-unified-switcher__pl-current");
        var idx = currentIndex(links, currentEl && currentEl.getAttribute("data-pl-id"));
        var dir = btn.getAttribute("data-kingdom-pl-dir");
        var next =
            dir === "prev"
                ? (idx - 1 + links.length) % links.length
                : (idx + 1) % links.length;
        var href = links[next].getAttribute("href");
        if (href) {
            window.location.href = href;
        }
    }

    function bind(root) {
        if (!root || root.getAttribute("data-kingdom-pl-bound")) return;
        root.setAttribute("data-kingdom-pl-bound", "1");
        root.addEventListener("click", onStepClick);
    }

    function init() {
        document
            .querySelectorAll("[data-kingdom-pricelist-stepper]")
            .forEach(bind);
    }

    if (document.readyState === "loading") {
        document.addEventListener("DOMContentLoaded", init);
    } else {
        init();
    }
    document.addEventListener("kingdom:dom-ready", init);
})();
