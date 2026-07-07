/** @odoo-module ignore **/
/**
 * Desktop (lg+): dark nav uses CSS sticky; this adds smooth shadow when the bar locks to the top (pic 2).
 * Mobile: whole .master-header is sticky via CSS — no nav strip in DOM.
 */
(function () {
  "use strict";

  function updateNavStuck() {
    var nav = document.querySelector(".master-header > .header-menu");
    if (!nav) return;
    if (!window.matchMedia("(min-width: 992px)").matches) {
      nav.classList.remove("is-nav-stuck");
      return;
    }
    var rect = nav.getBoundingClientRect();
    nav.classList.toggle("is-nav-stuck", rect.top <= 0.5);
  }

  var ticking = false;
  function onScroll() {
    if (ticking) return;
    ticking = true;
    window.requestAnimationFrame(function () {
      updateNavStuck();
      ticking = false;
    });
  }

  document.addEventListener("DOMContentLoaded", function () {
    updateNavStuck();
    window.addEventListener("scroll", onScroll, { passive: true });
    window.addEventListener("resize", updateNavStuck);
  });
})();
