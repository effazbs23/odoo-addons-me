/** @odoo-module ignore **/
/**
 * Kingdom Mega Store — site scripts only.
 * Swiper (js/vendor/swiper-bundle.min.js): product/deal carousels when those sections exist in the page.
 */

(function () {
  "use strict";

  function initSwiper(selector, options) {
    if (typeof Swiper === "undefined") return null;
    var el = document.querySelector(selector);
    if (!el) return null;
    var opts = Object.assign({}, options || {});
    if (opts.pagination && typeof opts.pagination.el === "string") {
      var pag =
        el.querySelector(".swiper-pagination") ||
        document.querySelector(opts.pagination.el);
      if (pag) {
        opts.pagination = Object.assign({}, opts.pagination, { el: pag });
      }
    }
    try {
      return new Swiper(el, opts);
    } catch (e) {
      return null;
    }
  }

  /** Deal countdown — every `[data-deal-countdown]` / `[data-deal-end-ms]`. */
  function initDealCountdown(defaultEndMs) {
    var roots = document.querySelectorAll(
      "[data-deal-countdown], [data-deal-end-ms], .carousel-countdown, .dealoftheday-counter"
    );
    if (!roots.length) return;

    function pad(n) {
      return String(n).padStart(2, "0");
    }

    function setUnit(root, selector, value) {
      var el = root.querySelector(selector);
      if (el) el.textContent = pad(value);
    }

    function parseEndMs(root) {
      var msAttr = root.getAttribute("data-deal-end-ms");
      if (msAttr) {
        var parsed = parseInt(msAttr, 10);
        if (!Number.isNaN(parsed) && parsed > 0) return parsed;
      }
      var iso = root.getAttribute("data-deal-countdown") || "";
      if (iso) {
        var fromIso = Date.parse(iso.replace(" ", "T"));
        if (!Number.isNaN(fromIso)) return fromIso;
      }
      return defaultEndMs;
    }

    function tick() {
      var now = Date.now();
      roots.forEach(function (root) {
        var endMs;
        try {
          endMs = parseEndMs(root);
        } catch (e) {
          endMs = defaultEndMs;
        }
        var diff = Math.max(0, endMs - now);
        var totalSeconds = Math.floor(diff / 1000);
        var days = Math.floor(totalSeconds / 86400);
        var s = totalSeconds - days * 86400;
        var hours = Math.floor(s / 3600);
        s -= hours * 3600;
        var mins = Math.floor(s / 60);
        var secs = s - mins * 60;
        setUnit(root, ".cd-days", days);
        setUnit(root, ".cd-hours", hours);
        setUnit(root, ".cd-mins", mins);
        setUnit(root, ".cd-secs", secs);
      });
    }

    tick();
    window.setInterval(tick, 1000);
  }

  function initMobileChrome() {
    var bottomNav = document.querySelector(".mobile-bottom-navigation");
    if (!bottomNav) return;

    document.documentElement.classList.add("k-mobile-chrome");

    var searchBox = document.querySelector(".store-search-box");
    var searchBtn = document.querySelector(".mobile-search-button");
    if (searchBtn && searchBox) {
      searchBtn.addEventListener("click", function (e) {
        e.preventDefault();
        e.stopPropagation();
        searchBox.classList.toggle("open");
        document.documentElement.classList.toggle("search-open");
      });
    }

    var accountBtn = document.querySelector(".customer-pupup-button");
    var accountPopup = document.querySelector(".customer-popup");
    if (accountBtn && accountPopup) {
      accountBtn.addEventListener("click", function (e) {
        e.preventDefault();
        e.stopPropagation();
        accountPopup.classList.toggle("show");
      });
    }

    document.addEventListener("click", function () {
      if (searchBox) searchBox.classList.remove("open");
      document.documentElement.classList.remove("search-open");
      if (accountPopup) accountPopup.classList.remove("show");
    });

    [searchBox, bottomNav, accountPopup].forEach(function (el) {
      if (!el) return;
      el.addEventListener("click", function (e) {
        e.stopPropagation();
      });
    });
  }

  function runKingdomFrontend() {
    /* Countdown first — must run even if Swiper failed to load. */
    var dealEnd = Date.now() + 72 * 60 * 60 * 1000;
    initDealCountdown(dealEnd);

    function initMobileNavigationDrawer() {
      var drawerEl = document.getElementById("MobileNavigationDrawer");
      if (!drawerEl) return;

      function bindTriggers() {
        var Offcanvas = window.Offcanvas;
        document.querySelectorAll(".mobile-menu-trigger").forEach(function (btn) {
          if (btn.dataset.kMobileDrawerBound) return;
          btn.dataset.kMobileDrawerBound = "1";
          btn.addEventListener("click", function (e) {
            if (!Offcanvas) return;
            e.preventDefault();
            Offcanvas.getOrCreateInstance(drawerEl).toggle();
          });
        });
      }

      if (window.Offcanvas) {
        bindTriggers();
      } else {
        window.addEventListener("load", bindTriggers, { once: true });
      }

      drawerEl.querySelectorAll(".k-mobile-cat-toggle").forEach(function (btn) {
        btn.addEventListener("click", function (e) {
          e.preventDefault();
          e.stopPropagation();
          var target = drawerEl.querySelector(btn.getAttribute("data-k-target"));
          if (target) {
            target.classList.toggle("show");
            btn.classList.toggle("is-open");
          }
        });
      });
    }

    function initHeaderMegaMenu() {
      document.querySelectorAll(".header-menu .mm-nav-item.has-children .right-arrow").forEach(function (arrow) {
        arrow.addEventListener("click", function (e) {
          e.preventDefault();
          e.stopPropagation();
          var link = arrow.closest("a");
          var sublist = link && link.parentElement.querySelector(":scope > .sublist");
          if (sublist) sublist.classList.add("show");
        });
      });
      var menuClose = document.querySelector(".header-menu > .mobile-menu-close");
      if (menuClose) {
        menuClose.addEventListener("click", function () {
          document.querySelectorAll(".header-menu .sublist").forEach(function (el) {
            el.classList.remove("show");
          });
          document.querySelector(".header-menu")?.classList.remove("open");
          document.documentElement.classList.remove("mobile-menu-added");
        });
      }
    }

    initMobileChrome();
    initHeaderMegaMenu();
    initMobileNavigationDrawer();
    var dismissKey = "kingdomMegaStore_topbarDismissed_v2";
    try {
      if (localStorage.getItem(dismissKey) === "1") {
        document.documentElement.classList.add("k-no-topbar");
      }
    } catch (e) {}

    var topbar = document.getElementById("AnnouncementBanner");
    var topbarClose = document.getElementById("announcement-close");
    if (topbarClose && topbar) {
      topbarClose.addEventListener("click", function () {
        try {
          localStorage.setItem(dismissKey, "1");
        } catch (e) {}
        document.documentElement.classList.add("k-no-topbar");
      });
    }

    var minimizeBtn = document.getElementById("announcement-minimize");
    if (minimizeBtn) {
      minimizeBtn.addEventListener("click", function () {
        document.documentElement.classList.toggle("announcement-minimized");
      });
    }

    initSwiper("#announcement-slider", {
      effect: "fade",
      fadeEffect: { crossFade: true },
      speed: 450,
      autoplay: { delay: 6000, disableOnInteraction: false },
      watchOverflow: true,
      loop: document.querySelectorAll("#announcement-slider .swiper-slide").length > 1,
    });

    /* Featured categories — mobile strip only (.k-cat-mobile) */
    document.querySelectorAll(".k-cat-mobile .home-category-swiper").forEach(function (el) {
      if (typeof Swiper === "undefined" || !el.querySelector(".swiper-slide")) return;
      try {
        new Swiper(el, {
          slidesPerView: 3.5,
          spaceBetween: 10,
          speed: 450,
          watchOverflow: true,
          autoplay: { delay: 5000, disableOnInteraction: false },
          breakpoints: {
            576: { slidesPerView: 3, spaceBetween: 10 },
          },
        });
      } catch (e) {}
    });

    function initHeroSwiper(heroEl) {
      if (!heroEl || heroEl.classList.contains("carousel") || typeof Swiper === "undefined") return;
      var slides = heroEl.querySelectorAll(".swiper-slide");
      if (!slides.length) return;

      if (heroEl.swiper && heroEl.swiper.destroy) {
        heroEl.swiper.destroy(true, true);
      }

      var effect = heroEl.getAttribute("data-k-effect") || "slide";
      var speed = parseInt(heroEl.getAttribute("data-k-speed"), 10);
      var delay = parseInt(heroEl.getAttribute("data-k-delay"), 10);
      var autoplayEnabled = heroEl.getAttribute("data-k-autoplay") !== "false";
      var indicatorsMode = heroEl.getAttribute("data-k-indicators") || "dots";

      var opts = {
        slidesPerView: 1,
        spaceBetween: 0,
        loop: slides.length > 1,
        speed: isNaN(speed) ? 650 : speed,
        watchOverflow: true,
        autoHeight: false,
        effect: effect === "fade" ? "fade" : "slide",
        navigation: {
          nextEl: heroEl.querySelector(".swiper-button-next"),
          prevEl: heroEl.querySelector(".swiper-button-prev"),
        },
      };
      if (effect === "fade") {
        opts.fadeEffect = { crossFade: true };
      }
      if (autoplayEnabled) {
        opts.autoplay = {
          delay: isNaN(delay) ? 6500 : delay,
          disableOnInteraction: false,
        };
      } else {
        opts.autoplay = false;
      }
      if (indicatorsMode !== "hidden") {
        opts.pagination = {
          el: heroEl.querySelector(".swiper-pagination"),
          clickable: true,
          type: indicatorsMode === "bars" ? "progressbar" : "bullets",
        };
        if (indicatorsMode === "numbers") {
          opts.pagination.renderBullet = function (index, className) {
            return '<span class="' + className + '">' + (index + 1) + "</span>";
          };
        }
      }
      try {
        new Swiper(heroEl, opts);
      } catch (e) {}
    }

    document.querySelectorAll(".home-page-main-slider").forEach(initHeroSwiper);

    (function initDealSwiper() {
      var wrapper = document.querySelector(".dealoftheday-wrapper");
      if (!wrapper || typeof Swiper === "undefined") return;
      var swiperEl = wrapper.querySelector(".deal-swiper");
      if (!swiperEl || !swiperEl.querySelector(".swiper-slide")) return;
      var slideCount = swiperEl.querySelectorAll(".swiper-slide").length;
      var nav = wrapper.querySelector(".deal-swiper-nav");
      try {
        new Swiper(swiperEl, {
          slidesPerView: "auto",
          observer: true,
          observeParents: true,
          lazy: true,
          loop: slideCount > 1,
          centeredSlides: false,
          initialSlide: 0,
          autoplay: {
            delay: 5000,
            disableOnInteraction: false,
            pauseOnMouseEnter: true,
          },
          pagination: {
            el: swiperEl.querySelector(".swiper-pagination"),
            clickable: true,
          },
          navigation: {
            nextEl: nav && nav.querySelector(".swiper-button-next"),
            prevEl: nav && nav.querySelector(".swiper-button-prev"),
          },
        });
      } catch (e) {}
    })();

    /** Product carousel blocks: tabs swap panels; optional fraction counter in nav. */
    function initProductCarouselBlock(root) {
      if (!root || typeof Swiper === "undefined") return;

      var tabButtons = root.querySelectorAll("[data-product-carousel-tab]");
      if (!tabButtons.length) return;

      var swiperOpts = {
        slidesPerView: 1,
        spaceBetween: 0,
        speed: 450,
        watchOverflow: true,
        observer: true,
        observeParents: true,
      };

      var swipers = {};

      function updateFraction(swiper, fractionEl) {
        if (!swiper || !fractionEl) return;
        var cur = fractionEl.querySelector("[data-fraction-current]");
        var tot = fractionEl.querySelector("[data-fraction-total]");
        if (cur) cur.textContent = String(swiper.realIndex + 1);
        if (tot) tot.textContent = String(swiper.slides.length);
      }

      tabButtons.forEach(function (btn) {
        var id = btn.getAttribute("data-product-carousel-tab");
        if (!id || swipers[id]) return;

        var swiperEl = root.querySelector(".product-carousel-swiper--" + id);
        if (!swiperEl) return;

        var nav = root.querySelector('[data-nav-for="' + id + '"]');
        var fractionEl = nav && nav.querySelector("[data-carousel-fraction]");

        swipers[id] = new Swiper(swiperEl, Object.assign({}, swiperOpts, {
          navigation: {
            prevEl: nav && nav.querySelector(".swiper-button-prev"),
            nextEl: nav && nav.querySelector(".swiper-button-next"),
          },
          on: {
            init: function () {
              updateFraction(swipers[id], fractionEl);
            },
            slideChange: function () {
              updateFraction(swipers[id], fractionEl);
            },
          },
        }));
      });

      function showTab(id) {
        tabButtons.forEach(function (btn) {
          var active = btn.getAttribute("data-product-carousel-tab") === id;
          btn.classList.toggle("is-active", active);
          btn.setAttribute("aria-selected", active ? "true" : "false");
          btn.tabIndex = active ? 0 : -1;
        });

        root.querySelectorAll("[data-product-carousel-panel]").forEach(function (panel) {
          var active = panel.getAttribute("data-product-carousel-panel") === id;
          panel.classList.toggle("d-none", !active);
          if (active) panel.removeAttribute("hidden");
          else panel.setAttribute("hidden", "");
        });

        root.querySelectorAll("[data-nav-for]").forEach(function (nav) {
          var active = nav.getAttribute("data-nav-for") === id;
          nav.classList.toggle("d-none", !active);
          if (active) nav.removeAttribute("hidden");
          else nav.setAttribute("hidden", "");
        });

        var sw = swipers[id];
        if (sw && typeof sw.update === "function") {
          requestAnimationFrame(function () {
            sw.update();
            if (sw.navigation && sw.navigation.update) sw.navigation.update();
            var nav = root.querySelector('[data-nav-for="' + id + '"]');
            updateFraction(sw, nav && nav.querySelector("[data-carousel-fraction]"));
          });
        }
      }

      tabButtons.forEach(function (btn) {
        btn.addEventListener("click", function () {
          var id = btn.getAttribute("data-product-carousel-tab");
          if (!id) return;
          showTab(id);
        });
      });

      var initial = root.querySelector(".product-carousel-tab.is-active");
      showTab(
        (initial && initial.getAttribute("data-product-carousel-tab")) ||
          tabButtons[0].getAttribute("data-product-carousel-tab")
      );
    }

    document.querySelectorAll(".product-carousel-section").forEach(initProductCarouselBlock);

    var productRowOpts = {
      spaceBetween: 14,
      slidesPerView: 2,
      pagination: { clickable: true },
      breakpoints: {
        576: { slidesPerView: 2 },
        768: { slidesPerView: 3 },
        992: { slidesPerView: 4 },
        1200: { slidesPerView: 5 },
        1400: { slidesPerView: 6 },
      },
    };

    function initProductRowSwiper(sectionSelector, swiperSelector, swiperOpts) {
      var section = document.querySelector(sectionSelector);
      if (!section || typeof Swiper === "undefined") return;
      var swiperEl = section.querySelector(swiperSelector);
      if (!swiperEl) return;
      var nav = section.querySelector(".featured-products-nav");
      var opts = swiperOpts || productRowOpts;
      new Swiper(swiperEl, Object.assign({}, opts, {
        watchOverflow: true,
        preventClicks: false,
        preventClicksPropagation: false,
        navigation: {
          prevEl: nav && nav.querySelector(".swiper-button-prev"),
          nextEl: nav && nav.querySelector(".swiper-button-next"),
        },
      }));
    }

    initProductRowSwiper(".featured-products-section", ".featured-swiper");
    initProductRowSwiper(".bestsale-products-section", ".bestsale-swiper");

    initSwiper(".secondary-hero-swiper", {
      loop: true,
      speed: 600,
      autoplay: { delay: 6500, disableOnInteraction: false },
      pagination: { el: ".secondary-hero-swiper .swiper-pagination", clickable: true },
      navigation: false,
    });

    function initManufacturerCarousel() {
      var section = document.querySelector(".home-manufacturers-section");
      if (!section || typeof Swiper === "undefined") return;
      var carousel = section.querySelector(".carousel-container");
      var swiperEl = section.querySelector(".manufacturer-swiper");
      var prevEl = section.querySelector(".manufacturer-carousel-arrow.swiper-button-prev");
      var nextEl = section.querySelector(".manufacturer-carousel-arrow.swiper-button-next");
      if (!swiperEl || !carousel || !prevEl || !nextEl) return;
      if (!swiperEl.querySelector(".swiper-slide")) return;

      if (swiperEl.swiper && swiperEl.swiper.destroy) {
        swiperEl.swiper.destroy(true, true);
      }

      var config = {
        loop: true,
        speed: 450,
        spaceBetween: 15,
        slidesPerView: 3,
        watchOverflow: true,
        observer: true,
        observeParents: true,
        navigation: {
          prevEl: prevEl,
          nextEl: nextEl,
        },
        breakpoints: {
          576: {
            slidesPerView: 4,
            spaceBetween: 15,
          },
          992: {
            slidesPerView: 6,
            spaceBetween: 15,
          },
          1600: {
            slidesPerView: 8,
            spaceBetween: 15,
          },
        },
      };

      try {
        new Swiper(swiperEl, config);
      } catch (e) {
        new Swiper(swiperEl, Object.assign({}, config, { loop: false }));
      }
    }

    initManufacturerCarousel();
    window.addEventListener("load", initManufacturerCarousel);
    if (typeof MutationObserver !== "undefined") {
      var wrapRoot = document.getElementById("wrap") || document.body;
      if (wrapRoot) {
        new MutationObserver(function () {
          var swiperEl = document.querySelector(".home-manufacturers-section .manufacturer-swiper");
          if (swiperEl && !swiperEl.classList.contains("swiper-initialized")) {
            initManufacturerCarousel();
          }
        }).observe(wrapRoot, { childList: true, subtree: true });
      }
    }

    document.querySelectorAll(".dealoftheday-wrapper .deal-qty").forEach(function (wrap) {
      if (wrap.closest(".deal-card-actions--disabled")) return;
      var input = wrap.querySelector(".deal-qty-input");
      var dec = wrap.querySelector('.deal-qty-btn[aria-label="Decrease quantity"]');
      var inc = wrap.querySelector('.deal-qty-btn[aria-label="Increase quantity"]');
      if (!input || !dec || !inc) return;
      dec.addEventListener("click", function () {
        var v = parseInt(input.value, 10) || 1;
        input.value = String(Math.max(1, v - 1));
      });
      inc.addEventListener("click", function () {
        var v = parseInt(input.value, 10) || 1;
        var max = parseInt(input.getAttribute("max"), 10) || 99;
        input.value = String(Math.min(max, v + 1));
      });
    });

    window.KingdomTheme = window.KingdomTheme || {};
    window.KingdomTheme.reinitHeroSlider = function (root) {
      var scope = root || document;
      scope.querySelectorAll(".home-page-main-slider:not(.carousel)").forEach(initHeroSwiper);
    };

    document.querySelectorAll(".featured-products-section .featured-product-qty").forEach(function (wrap) {
      if (wrap.closest(".featured-product-card--soldout")) return;
      var input = wrap.querySelector(".featured-qty-input, input[type='number']");
      var dec = wrap.querySelector('[aria-label="Decrease quantity"]');
      var inc = wrap.querySelector('[aria-label="Increase quantity"]');
      if (!input || !dec || !inc || input.disabled) return;
      dec.addEventListener("click", function () {
        var v = parseInt(input.value, 10) || 1;
        input.value = String(Math.max(1, v - 1));
      });
      inc.addEventListener("click", function () {
        var v = parseInt(input.value, 10) || 1;
        var max = parseInt(input.getAttribute("max"), 10) || 99;
        input.value = String(Math.min(max, v + 1));
      });
    });

  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", runKingdomFrontend);
  } else {
    runKingdomFrontend();
  }
})();
