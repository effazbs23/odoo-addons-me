/** Grid / list layout toggle for theme shop page (persists in localStorage). */
(function () {
    'use strict';

    const STORAGE_KEY = 'theme_natural_foods_shop_layout';
    const row = document.getElementById('nf-shop-products-row');
    if (!row) {
        return;
    }

    function applyView(view) {
        const isList = view === 'list';
        row.classList.toggle('nf-shop-view-grid', !isList);
        row.classList.toggle('nf-shop-view-list', isList);
        document.querySelectorAll('.nf-shop-view-btn').forEach((btn) => {
            const active = btn.getAttribute('data-nf-view') === view;
            btn.classList.toggle('active', active);
            btn.setAttribute('aria-pressed', active ? 'true' : 'false');
        });
        try {
            localStorage.setItem(STORAGE_KEY, view);
        } catch (e) {
            /* private mode */
        }
    }

    const params = new URLSearchParams(window.location.search);
    const urlView = params.get('view');
    let initial = 'grid';
    if (urlView === 'list' || urlView === 'grid') {
        initial = urlView;
    } else {
        try {
            const stored = localStorage.getItem(STORAGE_KEY);
            if (stored === 'list' || stored === 'grid') {
                initial = stored;
            }
        } catch (e) {
            /* ignore */
        }
    }

    applyView(initial);

    document.querySelectorAll('.nf-shop-view-btn').forEach((btn) => {
        btn.addEventListener('click', function (ev) {
            ev.preventDefault();
            const v = btn.getAttribute('data-nf-view');
            if (v === 'grid' || v === 'list') {
                applyView(v);
            }
        });
    });
})();
