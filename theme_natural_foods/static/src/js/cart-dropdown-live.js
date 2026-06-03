// Live cart dropdown for Natural Foods header.
(function () {
    'use strict';

    let hideTimer = null;

    function getJsonHeaders() {
        return {
            'Content-Type': 'application/json',
            'X-Requested-With': 'XMLHttpRequest',
        };
    }

    async function callJsonRoute(route, params) {
        const payload = {
            params: params || {},
        };
        const response = await fetch(route, {
            method: 'POST',
            headers: getJsonHeaders(),
            body: JSON.stringify(payload),
            credentials: 'same-origin',
        });
        if (!response.ok) {
            throw new Error('HTTP ' + response.status + ' for ' + route);
        }
        const data = await response.json();
        if (data && data.error) {
            throw new Error(data.error.data && data.error.data.message ? data.error.data.message : 'RPC error');
        }
        return data && Object.prototype.hasOwnProperty.call(data, 'result') ? data.result : data;
    }

    function escapeHtml(value) {
        const div = document.createElement('div');
        div.textContent = value || '';
        return div.innerHTML;
    }

    function updateHeaderCartCount(itemCount) {
        document.querySelectorAll('.my_cart_quantity').forEach(function (el) {
            el.textContent = String(itemCount || 0);
            el.classList.toggle('d-none', !(itemCount > 0));
        });
    }

    function renderCartItems(itemsContainer, items) {
        if (!items.length) {
            itemsContainer.innerHTML = '';
            return;
        }

        itemsContainer.innerHTML = items.map(function (item) {
            return (
                '<div class="d-flex align-items-center gap-3 mb-3" data-line-id="' + item.line_id + '">' +
                    '<img src="' + escapeHtml(item.image_url) + '" alt="' + escapeHtml(item.name) + '" class="rounded" style="width:64px;height:64px;object-fit:cover;">' +
                    '<div class="flex-grow-1">' +
                        '<h6 class="mb-1 small">' + escapeHtml(item.name) + '</h6>' +
                        '<div class="d-flex align-items-center justify-content-between">' +
                            '<span class="text-muted small">' + item.quantity + ' x ' + escapeHtml(item.price_subtotal_display) + '</span>' +
                            '<button type="button" class="btn btn-sm text-danger border-0 p-1 js-cart-dropdown-remove" data-line-id="' + item.line_id + '" aria-label="Remove item">' +
                                '<svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 16 16" fill="currentColor" aria-hidden="true">' +
                                    '<path d="M5.5 5.5A.5.5 0 0 1 6 6v6a.5.5 0 0 1-1 0V6a.5.5 0 0 1 .5-.5zm2.5.5a.5.5 0 0 0-1 0v6a.5.5 0 0 0 1 0V6zm2 .5a.5.5 0 0 1 1 0v6a.5.5 0 0 1-1 0V6z"/>' +
                                    '<path d="M14.5 3a1 1 0 0 1-1 1H13v9a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V4h-.5a1 1 0 0 1 0-2H5a1 1 0 0 1 1-1h4a1 1 0 0 1 1 1h2.5a1 1 0 0 1 1 1zM6 2v1h4V2H6zM4 4v9a1 1 0 0 0 1 1h6a1 1 0 0 0 1-1V4H4z"/>' +
                                '</svg>' +
                            '</button>' +
                        '</div>' +
                    '</div>' +
                '</div>'
            );
        }).join('');
    }

    function renderDropdown(data) {
        const dropdown = document.getElementById('cart-dropdown');
        if (!dropdown) {
            return;
        }
        const itemsContainer = document.getElementById('cart-dropdown-items');
        const emptyEl = document.getElementById('cart-dropdown-empty');
        const countEl = document.getElementById('cart-dropdown-items-count');
        const totalEl = document.getElementById('cart-dropdown-total');

        const items = data && data.items ? data.items : [];
        const itemCount = data && typeof data.item_count !== 'undefined' ? data.item_count : 0;
        const totalDisplay = data && data.total_display ? data.total_display : '$0.00';

        renderCartItems(itemsContainer, items);
        if (countEl) {
            countEl.textContent = itemCount + (itemCount === 1 ? ' item' : ' items');
        }
        if (totalEl) {
            totalEl.textContent = totalDisplay;
        }
        if (emptyEl) {
            emptyEl.classList.toggle('d-none', items.length > 0);
        }
        updateHeaderCartCount(itemCount);
        bindRemoveButtons();
    }

    async function refreshDropdown() {
        try {
            const data = await callJsonRoute('/shop/cart/dropdown_data', {});
            renderDropdown(data);
        } catch (error) {
            console.error('Failed to refresh cart dropdown', error);
            // Keep header and dropdown visually in sync when request fails.
            renderDropdown({
                items: [],
                item_count: 0,
                total_display: '$0.00',
            });
        }
    }

    async function removeLine(lineId) {
        const parsedLineId = Number(lineId);
        if (!Number.isFinite(parsedLineId) || parsedLineId <= 0) {
            console.error('Invalid line id for removal', lineId);
            return;
        }
        try {
            const data = await callJsonRoute('/shop/cart/remove_line', { line_id: parsedLineId });
            renderDropdown(data);
        } catch (error) {
            console.error('Failed to remove cart line', error);
        }
    }

    function bindRemoveButtons() {
        document.querySelectorAll('.js-cart-dropdown-remove').forEach(function (btn) {
            if (btn.dataset.boundRemove === '1') {
                return;
            }
            btn.dataset.boundRemove = '1';
            btn.addEventListener('click', function (ev) {
                ev.preventDefault();
                ev.stopPropagation();
                removeLine(btn.dataset.lineId);
            });
        });
    }

    function showDropdown() {
        clearTimeout(hideTimer);
        const dropdown = document.getElementById('cart-dropdown');
        if (!dropdown) {
            return;
        }
        dropdown.classList.remove('d-none');
        refreshDropdown();
    }

    function hideDropdown() {
        const dropdown = document.getElementById('cart-dropdown');
        if (!dropdown) {
            return;
        }
        hideTimer = window.setTimeout(function () {
            dropdown.classList.add('d-none');
        }, 180);
    }

    function keepDropdown() {
        clearTimeout(hideTimer);
    }

    function bindEvents() {
        const container = document.querySelector('.cart-dropdown-container');
        if (!container) {
            return;
        }
        const trigger = container.querySelector('.o_wsale_my_cart');
        const dropdown = document.getElementById('cart-dropdown');
        if (!trigger || !dropdown) {
            return;
        }

        container.addEventListener('mouseenter', showDropdown);
        container.addEventListener('mouseleave', hideDropdown);
        dropdown.addEventListener('mouseenter', keepDropdown);
        dropdown.addEventListener('mouseleave', hideDropdown);

        container.addEventListener('click', function (ev) {
            const removeBtn = ev.target.closest('.js-cart-dropdown-remove');
            if (!removeBtn) {
                return;
            }
            ev.preventDefault();
            ev.stopPropagation();
            removeLine(removeBtn.dataset.lineId);
        });

        trigger.addEventListener('click', function (ev) {
            if (window.matchMedia('(max-width: 991px)').matches) {
                return;
            }
            ev.preventDefault();
            showDropdown();
        });
    }

    function init() {
        bindEvents();
        refreshDropdown();
    }

    window.showCartDropdown = showDropdown;
    window.hideCartDropdown = hideDropdown;
    window.keepCartDropdown = keepDropdown;

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }
})();
