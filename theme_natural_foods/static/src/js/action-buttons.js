// Global action handlers used in snippet buttons
// Keeps behavior self-contained within the natural_foods addon.

(function () {
    function safeParseInt(val) {
        const n = parseInt(val, 10);
        return Number.isFinite(n) ? n : null;
    }

    function getWishlist() {
        try {
            return JSON.parse(localStorage.getItem('wishlist') || '[]');
        } catch (e) {
            return [];
        }
    }

    function setWishlist(items) {
        try {
            localStorage.setItem('wishlist', JSON.stringify(items));
        } catch (e) {
            // ignore
        }
    }

    function toast(message, type) {
        if (typeof window.showNotification === 'function') {
            window.showNotification(message, type || 'info');
            return;
        }
        // Fallback
        console.log(message);
    }

    async function odooJsonRpc(route, params) {
        const res = await fetch(route, {
            method: 'POST',
            credentials: 'same-origin',
            headers: {
                'Content-Type': 'application/json',
                'X-Requested-With': 'XMLHttpRequest',
            },
            body: JSON.stringify({
                jsonrpc: '2.0',
                method: 'call',
                params: params || {},
            }),
        });
        const data = await res.json();
        if (data && Object.prototype.hasOwnProperty.call(data, 'error')) {
            throw new Error(data.error && data.error.message ? data.error.message : 'RPC error');
        }
        return data ? data.result : null;
    }

    async function updateWishlistBadge() {
        try {
            const count = await odooJsonRpc('/shop/wishlist/get_count', {});
            document.querySelectorAll('.my_wish_quantity').forEach((el) => {
                el.textContent = String(count || 0);
                if (count && count > 0) {
                    el.classList.remove('d-none');
                } else {
                    el.classList.add('d-none');
                }
            });
        } catch (e) {
            // ignore
        }
    }

    window.addToWishlist = function addToWishlist(productId) {
        const id = safeParseInt(productId);
        if (!id) {
            return;
        }
        // Prefer Odoo native wishlist (website_sale_wishlist). Falls back to localStorage.
        odooJsonRpc('/shop/wishlist/add', { product_id: id })
            .then(() => {
                toast('Added to wishlist', 'success');
                updateWishlistBadge();
            })
            .catch(() => {
                const wishlist = getWishlist();
                const idx = wishlist.findIndex((x) => x && x.id === id);
                if (idx >= 0) {
                    wishlist.splice(idx, 1);
                    setWishlist(wishlist);
                    toast('Removed from wishlist', 'info');
                } else {
                    wishlist.push({ id });
                    setWishlist(wishlist);
                    toast('Added to wishlist', 'success');
                }
            });
    };

    window.quickView = function quickView(productId) {
        const id = safeParseInt(productId);
        if (!id) {
            return;
        }
        // Minimal quick view: open product page. (Avoids depending on extra modal JS.)
        window.location.href = `/shop/product/${id}`;
    };
})();

