/** @odoo-module ignore **/
/**
 * Kingdom Mega Store — site scripts only.
 * Swiper (js/vendor/swiper-bundle.min.js): product/deal carousels when those sections exist in the page.
 */

(function () {
  "use strict";

  var kingdomFlyoutPendingOpen = false;
  var kingdomFlyoutInitialized = false;

  window.KingdomTheme = window.KingdomTheme || {};

  function kingdomGetFlyout() {
    return document.querySelector(".js_kingdom_flyout_cart");
  }

  function kingdomSetFlyoutOpen(open) {
    var flyout = kingdomGetFlyout();
    document.documentElement.classList.toggle("flyout-cart-open", open);
    document.body.classList.toggle("flyout-cart-open", open);
    if (flyout) {
      flyout.setAttribute("aria-hidden", open ? "false" : "true");
    }
  }

  function kingdomIsFlyoutOpen() {
    return document.documentElement.classList.contains("flyout-cart-open")
      || document.body.classList.contains("flyout-cart-open");
  }

  function kingdomMoveFlyoutToBody() {
    var wrapper = document.getElementById("advance-cart-flyout-cart-wrapper");
    if (wrapper && wrapper.parentElement !== document.body) {
      document.body.appendChild(wrapper);
    }
  }

  function kingdomRemoveLegacyFlyoutCarts() {
    document.querySelectorAll(
      "#flyout-cart, .flyout-cart:not(.js_kingdom_flyout_cart)"
    ).forEach(function (legacyFlyout) {
      legacyFlyout.remove();
    });
  }

  function kingdomApplyFlyoutData(data, open) {
    var flyout = kingdomGetFlyout();
    if (!flyout || !data) {
      return;
    }
    var itemsEl = flyout.querySelector(".js_kingdom_flyout_items");
    var subtotalEl = flyout.querySelector(".js_kingdom_flyout_subtotal");
    var totalProductsEl = flyout.querySelector(".js_kingdom_flyout_total_products");
    if (itemsEl) {
      itemsEl.innerHTML = data.html;
    }
    if (subtotalEl) {
      subtotalEl.textContent = data.amount_total_formatted;
    }
    if (totalProductsEl) {
      totalProductsEl.textContent = data.cart_quantity;
    }
    document.querySelectorAll(".cart-ammount").forEach(function (el) {
      el.textContent = data.amount_total_formatted;
    });
    document.querySelectorAll(".my_cart_quantity").forEach(function (el) {
      if (data.cart_quantity === 0) {
        el.classList.add("d-none");
      } else {
        el.classList.remove("d-none");
        el.textContent = data.cart_quantity;
      }
    });
    try {
      sessionStorage.setItem("website_sale_cart_quantity", String(data.cart_quantity));
    } catch (e) {}
    if (open) {
      kingdomSetFlyoutOpen(true);
    }
  }

  function kingdomFetchFlyoutData() {
    return fetch("/theme_kingdom/cart/flyout", {
      method: "POST",
      credentials: "same-origin",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        jsonrpc: "2.0",
        method: "call",
        params: {},
        id: Date.now(),
      }),
    })
      .then(function (response) {
        if (!response.ok) {
          return null;
        }
        return response.json();
      })
      .then(function (payload) {
        return payload && payload.result;
      })
      .catch(function () {
        return null;
      });
  }

  function kingdomRefreshFlyout(open) {
    if (open) {
      kingdomSetFlyoutOpen(true);
    }
    return kingdomFetchFlyoutData().then(function (data) {
      kingdomApplyFlyoutData(data, open);
    });
  }

  function kingdomGetFlyoutLineMeta(item) {
    if (!item) {
      return null;
    }
    var lineId = parseInt(item.getAttribute("data-line-id") || item.dataset.lineId, 10);
    if (!lineId) {
      return null;
    }
    var productId = parseInt(item.getAttribute("data-product-id") || item.dataset.productId, 10);
    return {
      lineId: lineId,
      productId: productId || null,
      qtyInput: item.querySelector(".js_kingdom_flyout_qty"),
    };
  }

  function kingdomUpdateFlyoutLine(lineId, quantity, productId) {
    var params = { line_id: lineId, quantity: quantity };
    if (productId) {
      params.product_id = productId;
    }
    return fetch("/shop/cart/update", {
      method: "POST",
      credentials: "same-origin",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        jsonrpc: "2.0",
        method: "call",
        params: params,
        id: Date.now(),
      }),
    })
      .then(function (response) {
        if (!response.ok) {
          return null;
        }
        return response.json();
      })
      .then(function (payload) {
        if (!payload || payload.error) {
          return null;
        }
        return payload.result;
      })
      .catch(function () {
        return null;
      })
      .then(function () {
        if (window.__kingdomFlyoutInteractionActive) {
          document.dispatchEvent(
            new CustomEvent("kingdom-flyout-cart-refresh", { detail: { open: true } })
          );
          return;
        }
        return kingdomRefreshFlyout(true);
      });
  }

  document.addEventListener(
    "click",
    function (ev) {
      var flyout = kingdomGetFlyout();
      if (!flyout) {
        return;
      }

      if (!flyout.contains(ev.target)) {
        if (
          kingdomIsFlyoutOpen()
          && !ev.target.closest("#topcartlink")
          && !ev.target.closest(".js_kingdom_flyout_cart")
        ) {
          kingdomSetFlyoutOpen(false);
        }
        return;
      }

      if (ev.target.closest(".js_kingdom_flyout_close")) {
        ev.preventDefault();
        ev.stopPropagation();
        kingdomSetFlyoutOpen(false);
        return;
      }
      if (ev.target.closest(".js_kingdom_flyout_go_cart")) {
        ev.preventDefault();
        ev.stopPropagation();
        window.location.href = "/shop/cart";
        return;
      }
      if (ev.target.closest(".js_kingdom_flyout_checkout")) {
        ev.preventDefault();
        ev.stopPropagation();
        window.location.href = "/shop/checkout";
        return;
      }

      var item = ev.target.closest(".kingdom-flyout-item");
      if (!item) {
        return;
      }
      var meta = kingdomGetFlyoutLineMeta(item);
      if (!meta) {
        return;
      }

      if (ev.target.closest(".js_kingdom_flyout_remove")) {
        ev.preventDefault();
        ev.stopPropagation();
        kingdomUpdateFlyoutLine(meta.lineId, 0, meta.productId);
        return;
      }
      if (ev.target.closest(".js_kingdom_flyout_plus")) {
        ev.preventDefault();
        ev.stopPropagation();
        var nextQty = (parseInt(meta.qtyInput && meta.qtyInput.value, 10) || 1) + 1;
        kingdomUpdateFlyoutLine(meta.lineId, nextQty, meta.productId);
        return;
      }
      if (ev.target.closest(".js_kingdom_flyout_minus")) {
        ev.preventDefault();
        ev.stopPropagation();
        var prevQty = (parseInt(meta.qtyInput && meta.qtyInput.value, 10) || 1) - 1;
        kingdomUpdateFlyoutLine(meta.lineId, Math.max(0, prevQty), meta.productId);
      }
    },
    true
  );

  document.addEventListener("change", function (ev) {
    var input = ev.target.closest(".js_kingdom_flyout_qty");
    if (!input) {
      return;
    }
    var meta = kingdomGetFlyoutLineMeta(input.closest(".kingdom-flyout-item"));
    if (!meta) {
      return;
    }
    var qty = parseInt(input.value, 10);
    if (isNaN(qty) || qty < 0) {
      qty = 1;
    }
    input.value = String(qty);
    kingdomUpdateFlyoutLine(meta.lineId, qty, meta.productId);
  });

  var kingdomFooterAccordionMq = window.matchMedia("(max-width: 991px)");

  function kingdomGetFooterUpper(root) {
    var scope = root || document;
    return scope.querySelector(".js_kingdom_footer_upper")
      || scope.querySelector("footer.footer .footer-upper")
      || scope.querySelector("#footer .footer-upper");
  }

  function kingdomGetFooterBlockTitle(block) {
    if (!block) {
      return null;
    }
    for (var i = 0; i < block.children.length; i++) {
      var child = block.children[i];
      if (child.classList && child.classList.contains("title")) {
        return child;
      }
    }
    return null;
  }

  function kingdomGetFooterBlockPanel(block) {
    if (!block) {
      return null;
    }
    for (var i = 0; i < block.children.length; i++) {
      var child = block.children[i];
      if (child.classList && child.classList.contains("list")) {
        return child;
      }
    }
    return null;
  }

  function kingdomToggleFooterAccordionTitle(title) {
    var block = title && title.parentElement;
    var panel = kingdomGetFooterBlockPanel(block);
    if (!panel) {
      return;
    }
    var willOpen = !title.classList.contains("ui-state-active");
    title.classList.toggle("ui-state-active", willOpen);
    title.classList.toggle("kingdom-footer-open", willOpen);
    title.setAttribute("aria-expanded", willOpen ? "true" : "false");
    panel.classList.toggle("ui-accordion-content", willOpen);
    panel.classList.toggle("kingdom-footer-panel-open", willOpen);
    panel.style.display = willOpen ? "" : "none";
  }

  function kingdomSyncFooterAccordionBlock(title, panel, isMobile) {
    if (!title || !panel) {
      return;
    }
    if (!isMobile) {
      title.classList.remove("ui-state-active", "kingdom-footer-open");
      title.setAttribute("aria-expanded", "true");
      panel.classList.add("ui-accordion-content", "kingdom-footer-panel-open");
      panel.style.removeProperty("display");
      return;
    }
    var isOpen = title.classList.contains("ui-state-active");
    title.setAttribute("aria-expanded", isOpen ? "true" : "false");
    panel.classList.toggle("ui-accordion-content", isOpen);
    panel.classList.toggle("kingdom-footer-panel-open", isOpen);
    panel.style.display = isOpen ? "" : "none";
  }

  function initKingdomFooterAccordion(root) {
    var footerUpper = kingdomGetFooterUpper(root);
    if (!footerUpper) {
      return;
    }
    var isMobile = kingdomFooterAccordionMq.matches;
    footerUpper.querySelectorAll(".footer-block").forEach(function (block) {
      var title = block.querySelector(".js_kingdom_footer_toggle")
        || kingdomGetFooterBlockTitle(block);
      var panel = kingdomGetFooterBlockPanel(block);
      if (!title || !panel) {
        return;
      }
      if (!title.dataset.kingdomFooterAccordionBound) {
        title.dataset.kingdomFooterAccordionBound = "1";
        title.setAttribute("role", "button");
        title.setAttribute("tabindex", "0");
        title.addEventListener("keydown", function (ev) {
          if (!kingdomFooterAccordionMq.matches) {
            return;
          }
          if (ev.key === "Enter" || ev.key === " ") {
            ev.preventDefault();
            kingdomToggleFooterAccordionTitle(title);
          }
        });
      }
      kingdomSyncFooterAccordionBlock(title, panel, isMobile);
    });
  }

  document.addEventListener(
    "click",
    function (ev) {
      if (!kingdomFooterAccordionMq.matches) {
        return;
      }
      var title = ev.target.closest(".js_kingdom_footer_toggle");
      if (!title) {
        var candidate = ev.target.closest(".footer-upper .footer-block .title");
        if (!candidate) {
          return;
        }
        var parent = candidate.parentElement;
        if (!parent || !parent.classList.contains("footer-block")
          || parent.classList.contains("social")
          || parent.classList.contains("newsletter")) {
          return;
        }
        title = candidate;
      }
      ev.preventDefault();
      ev.stopPropagation();
      kingdomToggleFooterAccordionTitle(title);
    },
    true
  );

  if (typeof kingdomFooterAccordionMq.addEventListener === "function") {
    kingdomFooterAccordionMq.addEventListener("change", function () {
      initKingdomFooterAccordion();
    });
  } else if (typeof kingdomFooterAccordionMq.addListener === "function") {
    kingdomFooterAccordionMq.addListener(function () {
      initKingdomFooterAccordion();
    });
  }

  function scheduleKingdomFooterAccordionInit() {
    initKingdomFooterAccordion();
    window.setTimeout(function () {
      initKingdomFooterAccordion();
    }, 0);
  }

  scheduleKingdomFooterAccordionInit();
  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", scheduleKingdomFooterAccordionInit);
  }
  window.addEventListener("load", scheduleKingdomFooterAccordionInit);

  function kingdomOpenFlyoutCart() {
    kingdomRemoveLegacyFlyoutCarts();
    kingdomMoveFlyoutToBody();
    kingdomSetFlyoutOpen(true);
    if (window.__kingdomFlyoutInteractionActive) {
      document.dispatchEvent(
        new CustomEvent("kingdom-flyout-cart-refresh", { detail: { open: true } })
      );
      return Promise.resolve();
    }
    if (typeof window.KingdomTheme.openFlyoutCart === "function" && kingdomFlyoutInitialized) {
      return window.KingdomTheme.openFlyoutCart();
    }
    kingdomFlyoutPendingOpen = true;
    initKingdomFlyoutCart();
    if (typeof window.KingdomTheme.openFlyoutCart === "function" && kingdomFlyoutInitialized) {
      kingdomFlyoutPendingOpen = false;
      return window.KingdomTheme.openFlyoutCart();
    }
    return Promise.resolve();
  }

  document.addEventListener(
    "click",
    function (ev) {
      var topCart = ev.target.closest("#topcartlink");
      if (!topCart) {
        return;
      }
      var link = ev.target.closest('a[href*="/shop/cart"], a.js_kingdom_cart_toggle');
      if (!link || !topCart.contains(link)) {
        return;
      }
      if (ev.metaKey || ev.ctrlKey || ev.shiftKey || ev.altKey) {
        return;
      }
      ev.preventDefault();
      ev.stopImmediatePropagation();
      kingdomOpenFlyoutCart();
    },
    true
  );

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
        if (!Number.isNaN(parsed) && parsed > 0) {
          // BuilderDateTimePicker stores unix seconds; deals use epoch ms.
          return parsed < 1e12 ? parsed * 1000 : parsed;
        }
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

  function kingdomSyncWishlistCount() {
    var badge = document.querySelector(
      ".ico-wishlist .my_wish_quantity, .mobile-navigation-drawer .my_wish_quantity"
    );
    if (!badge) {
      return;
    }

    var serverCount = parseInt(badge.textContent, 10);
    if (Number.isNaN(serverCount)) {
      serverCount = 0;
    }

    var sessionIds = [];
    try {
      sessionIds = JSON.parse(sessionStorage.getItem("wishlist_product_ids") || "[]");
    } catch (e) {
      sessionIds = [];
    }

    if (sessionIds.length === serverCount) {
      return;
    }

    fetch("/shop/wishlist/get_product_ids", {
      method: "POST",
      credentials: "same-origin",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        jsonrpc: "2.0",
        method: "call",
        params: {},
        id: Date.now(),
      }),
    })
      .then(function (response) {
        return response.ok ? response.json() : null;
      })
      .then(function (payload) {
        if (!payload || payload.error || !Array.isArray(payload.result)) {
          return;
        }
        sessionStorage.setItem("wishlist_product_ids", JSON.stringify(payload.result));
        var count = payload.result.length;
        document.querySelectorAll(".my_wish_quantity").forEach(function (el) {
          el.textContent = String(count);
          el.classList.remove("d-none");
        });
      })
      .catch(function () {});
  }

  function runKingdomFrontend() {
    kingdomSyncWishlistCount();
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
      var categoryMenu = document.querySelector(".header-left-menu-dropdown");

      function openSublist(link) {
        var sublist = link && link.parentElement.querySelector(":scope > .sublist");
        if (sublist) sublist.classList.add("show");
      }

      if (categoryMenu) {
        var megaCloseTimer;

        function closeMegaPanels() {
          categoryMenu.querySelectorAll(".nav-menu > li.is-mega-open").forEach(function (item) {
            item.classList.remove("is-mega-open");
          });
        }

        function openMegaPanel(item) {
          clearTimeout(megaCloseTimer);
          closeMegaPanels();
          item.classList.add("is-mega-open");
        }

        function scheduleMegaClose(item) {
          clearTimeout(megaCloseTimer);
          megaCloseTimer = setTimeout(function () {
            item.classList.remove("is-mega-open");
          }, 220);
        }

        categoryMenu.querySelectorAll(".nav-menu > li.has-children").forEach(function (item) {
          var sublist = item.querySelector(":scope > .sublist");
          if (!sublist) return;

          item.addEventListener("mouseenter", function () {
            if (!window.matchMedia("(min-width: 992px)").matches) return;
            openMegaPanel(item);
          });

          item.addEventListener("mouseleave", function (e) {
            if (!window.matchMedia("(min-width: 992px)").matches) return;
            if (e.relatedTarget && item.contains(e.relatedTarget)) {
              return;
            }
            scheduleMegaClose(item);
          });

          sublist.addEventListener("mouseenter", function () {
            if (!window.matchMedia("(min-width: 992px)").matches) return;
            openMegaPanel(item);
          });

          sublist.addEventListener("mouseleave", function (e) {
            if (!window.matchMedia("(min-width: 992px)").matches) return;
            if (e.relatedTarget && item.contains(e.relatedTarget)) {
              return;
            }
            scheduleMegaClose(item);
          });
        });

        categoryMenu.querySelectorAll(".mm-nav-item.has-children > a").forEach(function (link) {
          link.addEventListener("click", function (e) {
            var sublist = link.parentElement.querySelector(":scope > .sublist");
            if (!sublist) return;
            if (window.matchMedia("(max-width: 991px)").matches) {
              e.preventDefault();
              openSublist(link);
              return;
            }
            if (link.getAttribute("href") === "#") {
              e.preventDefault();
            }
          });
        });

        categoryMenu.querySelectorAll(".mm-nav-item.has-children .right-arrow").forEach(function (arrow) {
          arrow.addEventListener("click", function (e) {
            e.preventDefault();
            e.stopPropagation();
            openSublist(arrow.closest("a"));
          });
        });

        categoryMenu.querySelectorAll(".sublist .mm-nav-item.has-children > a").forEach(function (link) {
          link.addEventListener("click", function (e) {
            var sublist = link.parentElement.querySelector(":scope > .sublist");
            if (!sublist) return;
            if (window.matchMedia("(max-width: 991px)").matches) {
              e.preventDefault();
              openSublist(link);
            } else if (link.getAttribute("href") === "#") {
              e.preventDefault();
            }
          });
        });
      }

      document.querySelectorAll(".header-menu .header-right-menu .mm-nav-item.has-children .right-arrow").forEach(function (arrow) {
        arrow.addEventListener("click", function (e) {
          e.preventDefault();
          e.stopPropagation();
          openSublist(arrow.closest("a"));
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

    function initHeaderSelectors() {
      document.querySelectorAll(".header-inline-selectors .js_change_lang").forEach(function (link) {
        link.addEventListener("click", function (ev) {
          if (document.body.classList.contains("editor_enable")) {
            return;
          }
          ev.preventDefault();
          var urlCode = link.getAttribute("data-url_code");
          if (!urlCode) {
            return;
          }
          var target = (link.getAttribute("href") || "/").replace(/[&?]edit_translations[^&?]+/, "");
          var hash = window.location.hash || "";
          window.location.href =
            "/website/lang/" +
            encodeURIComponent(urlCode) +
            "?r=" +
            encodeURIComponent(target) +
            (hash ? encodeURIComponent(hash) : "");
        });
      });
    }

    initMobileChrome();
    initHeaderSelectors();
    initHeaderMegaMenu();
    initMobileNavigationDrawer();
    initKingdomFooterAccordion();
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
    function initCategorySwiper(root) {
      var scope = root || document;
      scope.querySelectorAll(".k-cat-mobile .home-category-swiper").forEach(function (el) {
        if (!root && el.closest("[data-kingdom-live-snippet]")) return;
        if (typeof Swiper === "undefined" || !el.querySelector(".swiper-slide")) return;
        if (el.swiper && el.swiper.destroy) {
          el.swiper.destroy(true, true);
        }
        try {
          new Swiper(el, {
            slidesPerView: 3.5,
            spaceBetween: 10,
            speed: 450,
            watchOverflow: true,
            observer: true,
            observeParents: true,
            autoplay: { delay: 5000, disableOnInteraction: false },
            breakpoints: {
              576: { slidesPerView: 3, spaceBetween: 10 },
            },
          });
        } catch (e) {}
      });
    }

    initCategorySwiper();
    window.KingdomInitCategorySwiper = initCategorySwiper;

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
        // Allow cart / wishlist / compare clicks inside slides.
        preventClicks: false,
        preventClicksPropagation: false,
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

    document.querySelectorAll(".product-carousel-section").forEach(function (root) {
      if (root.closest("[data-kingdom-live-snippet]")) return;
      initProductCarouselBlock(root);
    });
    window.KingdomInitProductCarousel = initProductCarouselBlock;

    /** nopCommerce-style product tab blocks (Category Dual Carousels snippet). */
    function initProductTabBlock(container) {
      if (!container || typeof Swiper === "undefined") return;

      var headerEl = container.querySelector(".product-tab-item-header.swiper");
      if (headerEl && !headerEl.swiper) {
        try {
          new Swiper(headerEl, {
            slidesPerView: "auto",
            spaceBetween: 16,
            observer: true,
            observeParents: true,
          });
        } catch (e) {}
      }

      var tabItems = container.querySelectorAll(".nav-tab-item[data-product-tab]");
      if (!tabItems.length) return;

      var swipers = {};

      function initPanelSwiper(panelId) {
        if (swipers[panelId]) return swipers[panelId];
        var panel = container.querySelector('[data-product-tab-panel="' + panelId + '"]');
        if (!panel) return null;
        var swiperEl = panel.querySelector(".product-tab-item.swiper");
        if (!swiperEl || !swiperEl.querySelector(".swiper-slide")) return null;
        if (swiperEl.swiper && swiperEl.swiper.destroy) {
          swiperEl.swiper.destroy(true, true);
        }
        var slideCount = swiperEl.querySelectorAll(".swiper-slide").length;
        try {
          swipers[panelId] = new Swiper(swiperEl, {
            slidesPerView: "auto",
            observer: true,
            observeParents: true,
            lazy: true,
            loop: slideCount > 1,
            centeredSlides: false,
            autoplay: {
              delay: 5000,
              disableOnInteraction: false,
              pauseOnMouseEnter: true,
            },
            pagination: {
              el: swiperEl.querySelector(".swiper-pagination"),
              type: "fraction",
            },
            navigation: {
              nextEl: swiperEl.querySelector(".swiper-button-next"),
              prevEl: swiperEl.querySelector(".swiper-button-prev"),
            },
          });
        } catch (e) {}
        return swipers[panelId];
      }

      function showTab(id) {
        tabItems.forEach(function (li) {
          var active = li.getAttribute("data-product-tab") === id;
          li.classList.toggle("ui-tabs-active", active);
          li.classList.toggle("ui-state-active", active);
          li.setAttribute("aria-selected", active ? "true" : "false");
          li.tabIndex = active ? 0 : -1;
        });

        container.querySelectorAll("[data-product-tab-panel]").forEach(function (panel) {
          var active = panel.getAttribute("data-product-tab-panel") === id;
          panel.classList.toggle("d-none", !active);
          if (active) panel.removeAttribute("hidden");
          else panel.setAttribute("hidden", "");
          panel.setAttribute("aria-hidden", active ? "false" : "true");
        });

        var sw = initPanelSwiper(id);
        if (sw && typeof sw.update === "function") {
          requestAnimationFrame(function () {
            sw.update();
            if (sw.navigation && sw.navigation.update) sw.navigation.update();
          });
        }
      }

      tabItems.forEach(function (li) {
        var link = li.querySelector(".nav-tab-link");
        if (!link) return;
        link.addEventListener("click", function (e) {
          e.preventDefault();
          var id = li.getAttribute("data-product-tab");
          if (id) showTab(id);
        });
      });

      var initial = container.querySelector(
        ".nav-tab-item.ui-tabs-active, .nav-tab-item.ui-state-active"
      );
      showTab(
        (initial && initial.getAttribute("data-product-tab")) ||
          (tabItems[0] && tabItems[0].getAttribute("data-product-tab")) ||
          "new"
      );
    }

    document.querySelectorAll(".product-tab-container").forEach(function (root) {
      if (root.closest("[data-kingdom-live-snippet]")) return;
      initProductTabBlock(root);
    });
    window.KingdomInitProductTab = initProductTabBlock;

    var productRowOpts = {
      spaceBetween: 14,
      slidesPerView: 2,
      observer: true,
      observeParents: true,
      breakpoints: {
        576: { slidesPerView: 2 },
        768: { slidesPerView: 3 },
        992: { slidesPerView: 4 },
        1200: { slidesPerView: 5 },
        1400: { slidesPerView: 6 },
      },
    };

    function initProductRowSwiperInSection(section, swiperSelector, swiperOpts) {
      if (!section || typeof Swiper === "undefined") return null;
      var swiperEl = section.querySelector(swiperSelector || ".featured-swiper, .bestsale-swiper");
      if (!swiperEl || !swiperEl.querySelector(".swiper-slide")) return null;
      if (swiperEl.swiper && swiperEl.swiper.destroy) {
        swiperEl.swiper.destroy(true, true);
      }
      var nav = section.querySelector(".featured-products-nav");
      var opts = swiperOpts || productRowOpts;
      return new Swiper(swiperEl, Object.assign({}, opts, {
        watchOverflow: true,
        preventClicks: false,
        preventClicksPropagation: false,
        navigation: {
          prevEl: nav && nav.querySelector(".swiper-button-prev"),
          nextEl: nav && nav.querySelector(".swiper-button-next"),
        },
      }));
    }

    function initProductRowSwiper(sectionSelector, swiperSelector, swiperOpts) {
      document.querySelectorAll(sectionSelector).forEach(function (section) {
        initProductRowSwiperInSection(section, swiperSelector, swiperOpts);
      });
    }

    window.KingdomInitProductRowSwiper = function (root) {
      var scope = root || document;
      var sectionSel = ".featured-products-section, .bestsale-products-section";
      var sections = [];
      // Live snippet passes the section itself as root; querySelectorAll only
      // matches descendants, so include the root when it is the section.
      if (scope.nodeType === 1 && scope.matches && scope.matches(sectionSel)) {
        sections.push(scope);
      }
      if (scope.querySelectorAll) {
        scope.querySelectorAll(sectionSel).forEach(function (section) {
          if (sections.indexOf(section) === -1) {
            sections.push(section);
          }
        });
      }
      sections.forEach(function (section) {
        var swiperEl = section.querySelector(".featured-swiper, .bestsale-swiper");
        var selector = swiperEl && swiperEl.classList.contains("bestsale-swiper")
          ? ".bestsale-swiper"
          : ".featured-swiper";
        initProductRowSwiperInSection(section, selector, productRowOpts);
      });
    };

    initProductRowSwiper(".featured-products-section", ".featured-swiper");
    initProductRowSwiper(".bestsale-products-section", ".bestsale-swiper");

    if (document.body.classList.contains("editor_enable") && typeof MutationObserver !== "undefined") {
      var productRowObserver = new MutationObserver(function () {
        window.KingdomInitProductRowSwiper();
      });
      var observeRoot = document.getElementById("wrapwrap") || document.body;
      productRowObserver.observe(observeRoot, { childList: true, subtree: true });
    }

    initSwiper(".secondary-hero-swiper", {
      loop: true,
      speed: 600,
      autoplay: { delay: 6500, disableOnInteraction: false },
      pagination: { el: ".secondary-hero-swiper .swiper-pagination", clickable: true },
      navigation: false,
    });

    function initManufacturerCarousel() {
      var section = document.querySelector(".home-manufacturers-section");
      if (!section || section.classList.contains("d-none") || typeof Swiper === "undefined") return;
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

  function initKingdomFlyoutCart() {
    var flyout = kingdomGetFlyout();
    if (!flyout || kingdomFlyoutInitialized) {
      return;
    }

    kingdomMoveFlyoutToBody();

    document.addEventListener("kingdom-flyout-cart-refresh", function (ev) {
      if (window.__kingdomFlyoutInteractionActive) {
        return;
      }
      kingdomRefreshFlyout(Boolean(ev.detail && ev.detail.open));
    });

    document.addEventListener("keydown", function (ev) {
      if (ev.key === "Escape" && kingdomIsFlyoutOpen()) {
        kingdomSetFlyoutOpen(false);
      }
    });

    window.KingdomTheme.openFlyoutCart = function () {
      if (window.__kingdomFlyoutInteractionActive) {
        document.dispatchEvent(
          new CustomEvent("kingdom-flyout-cart-refresh", { detail: { open: true } })
        );
        return Promise.resolve();
      }
      return kingdomRefreshFlyout(true);
    };
    window.KingdomTheme.closeFlyoutCart = function () {
      kingdomSetFlyoutOpen(false);
    };

    kingdomFlyoutInitialized = true;

    if (kingdomFlyoutPendingOpen) {
      kingdomFlyoutPendingOpen = false;
      window.KingdomTheme.openFlyoutCart();
    }
  }

  function scheduleKingdomFlyoutInit() {
    kingdomRemoveLegacyFlyoutCarts();
    kingdomMoveFlyoutToBody();
    initKingdomFlyoutCart();
    if (!kingdomFlyoutInitialized) {
      window.setTimeout(initKingdomFlyoutCart, 0);
    }
  }

  scheduleKingdomFlyoutInit();

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", scheduleKingdomFlyoutInit);
  }
  window.addEventListener("load", scheduleKingdomFlyoutInit);

  if (typeof MutationObserver !== "undefined") {
    var flyoutObserver = new MutationObserver(function () {
      if (!kingdomFlyoutInitialized && kingdomGetFlyout()) {
        scheduleKingdomFlyoutInit();
      }
    });
    flyoutObserver.observe(document.documentElement, { childList: true, subtree: true });
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", runKingdomFrontend);
  } else {
    runKingdomFrontend();
  }
})();
