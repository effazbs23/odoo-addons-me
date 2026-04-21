// Loading screen: fade out after full page load.
(function () {
    function hideLoader() {
        const el = document.getElementById('loading-screen');
        if (!el) {
            return;
        }
        el.classList.add('fade-out');
        window.setTimeout(() => {
            el.remove();
        }, 600);
    }

    if (document.readyState === 'complete') {
        hideLoader();
    } else {
        window.addEventListener('load', hideLoader, { once: true });
        // Safety: never block forever
        window.setTimeout(hideLoader, 8000);
    }
})();

