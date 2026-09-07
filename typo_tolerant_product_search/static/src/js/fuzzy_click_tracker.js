/** @odoo-module **/
// Best-effort, non-blocking click tracking for the search-miss log (spec 6).
// Fires once per page load, only when the "Showing results for..." note
// carries a fuzzy log id (i.e. a fuzzy correction actually fired). A failure
// here must never affect navigation - see fuzzy_search_log_click() in
// controllers/main.py, which is equally best-effort.
document.addEventListener('DOMContentLoaded', () => {
    const notice = document.querySelector('[data-fuzzy-log-id]');
    if (!notice) {
        return;
    }
    const logId = notice.getAttribute('data-fuzzy-log-id');
    if (!logId) {
        return;
    }
    const grid = document.querySelector('#products_grid');
    if (!grid) {
        return;
    }
    grid.addEventListener('click', (ev) => {
        if (!ev.target.closest('a')) {
            return;
        }
        try {
            const url = `/shop/fuzzy_search/click/${encodeURIComponent(logId)}`;
            if (navigator.sendBeacon) {
                navigator.sendBeacon(url);
            } else {
                fetch(url, {method: 'GET', keepalive: true}).catch(() => {});
            }
        } catch {
            // best-effort: never block the visitor's navigation
        }
    }, {once: true});
});
