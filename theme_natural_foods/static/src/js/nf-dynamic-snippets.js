import { Interaction } from "@web/public/interaction";
import { registry } from "@web/core/registry";

/*
 * Keeps the config-driven snippets (Featured Products, Best Seller, New Arrival,
 * Deals of the Day, Our Products, Featured Recipes, Shop by Category) in sync
 * with their backend configuration.
 *
 * Odoo freezes the rendered HTML of a snippet into the page when it is saved, so
 * these sections would otherwise keep showing whatever products/categories
 * existed at the moment the snippet was dropped. On every (published) page load
 * we re-fetch a freshly rendered fragment from the server and swap it in, then
 * re-initialise the carousels.
 *
 * This is implemented as a public Interaction (instead of a raw <script>) on
 * purpose: the website framework never starts public interactions while the page
 * is being edited, so this code cannot interfere with the website builder's
 * drag & drop / history tracking.
 */

const CONFIG = {
    featured_products_snippet: { key: "featured_products", container: ".swiper-wrapper", reinit: "swiper" },
    best_seller_snippet: { key: "best_seller", container: ".swiper-wrapper", reinit: "swiper" },
    naturalfood_new_arrival: { key: "new_arrival", container: ".swiper-wrapper", reinit: "swiper" },
    naturalfood_deals_of_the_day: { key: "deals_of_day", container: ".swiper-wrapper", reinit: "swiper" },
    naturalfood_our_products: { key: "our_products", container: "#product-slider", reinit: "ourproducts" },
    featured_recipes_snippet: { key: "featured_recipes", container: ".row.g-4", reinit: "none" },
    naturalfood_shop_by_category: { key: "shop_by_category", container: ".swiper-wrapper", reinit: "swiper" },
};

export class NfDynamicSnippet extends Interaction {
    static selector = [
        '[data-snippet="featured_products_snippet"]',
        '[data-snippet="best_seller_snippet"]',
        '[data-snippet="naturalfood_new_arrival"]',
        '[data-snippet="naturalfood_deals_of_the_day"]',
        '[data-snippet="naturalfood_our_products"]',
        '[data-snippet="featured_recipes_snippet"]',
        '[data-snippet="naturalfood_shop_by_category"]',
    ].join(", ");

    start() {
        const cfg = CONFIG[this.el.dataset.snippet];
        if (!cfg) {
            return;
        }
        const container = this.el.querySelector(cfg.container);
        if (!container) {
            return;
        }
        const url =
            "/theme_natural_foods/snippet_reload?key=" +
            encodeURIComponent(cfg.key) +
            "&_=" +
            Date.now();

        this.waitFor(
            fetch(url, {
                headers: { "X-Requested-With": "XMLHttpRequest" },
                credentials: "same-origin",
            }).then((resp) => (resp.ok ? resp.text() : ""))
        ).then((html) => {
            // Empty response means "keep whatever is there" (avoid blanking on error).
            if (!html || !html.trim()) {
                return;
            }
            container.innerHTML = html;
            this._reinit(cfg, container);
        });
    }

    _reinit(cfg, container) {
        if (cfg.reinit === "swiper") {
            const swiperEl = container.closest(".swiper");
            if (swiperEl && swiperEl.swiper) {
                try {
                    swiperEl.swiper.destroy(true, true);
                } catch (e) {
                    /* ignore */
                }
            }
            if (typeof window.initAllSwipers === "function") {
                window.initAllSwipers();
            }
        } else if (cfg.reinit === "ourproducts") {
            this._initCategorySwipers(container);
            if (typeof window.nfRefreshProductTabs === "function") {
                window.nfRefreshProductTabs();
            }
        }
    }

    _initCategorySwipers(root) {
        if (typeof window.Swiper === "undefined") {
            return;
        }
        root.querySelectorAll(".category-products").forEach((el) => {
            if (el.swiper) {
                try {
                    el.swiper.destroy(true, true);
                } catch (e) {
                    /* ignore */
                }
            }
            new window.Swiper(el, {
                slidesPerView: 4,
                spaceBetween: 30,
                loop: false,
                observer: true,
                observeParents: true,
                breakpoints: {
                    320: { slidesPerView: 2 },
                    768: { slidesPerView: 3 },
                    1200: { slidesPerView: 4 },
                },
            });
        });
    }
}

registry.category("public.interactions").add("theme_natural_foods.dynamic_snippets", NfDynamicSnippet);
