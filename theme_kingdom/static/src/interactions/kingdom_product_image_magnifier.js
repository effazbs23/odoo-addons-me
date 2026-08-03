/** @odoo-module **/

import { Interaction } from '@web/public/interaction';
import { registry } from '@web/core/registry';

const DEFAULT_LENS_SIZE = 200;
const MIN_LENS_SIZE = 150;
const MAX_LENS_SIZE = 250;
const DEFAULT_ZOOM = 2.5;
const MIN_ZOOM = 2;
const MAX_ZOOM = 4;

/**
 * ZoomPle-style circular hover magnifier for the product detail gallery.
 *
 * Prefers Odoo data-zoom-image (image_1920) when available, otherwise zooms
 * the displayed product image. Click-to-fullscreen ProductImageViewer is
 * left untouched.
 */
export class KingdomProductImageMagnifier extends Interaction {
    static selector = '.o_wsale_product_page';

    setup() {
        this.imagesCol = null;
        this.lens = null;
        this.lensView = null;
        this.activeImg = null;
        this.activeWrapper = null;
        this.pendingEvent = null;
        this.rafId = null;
        this.loadedZoomUrl = null;
        this.imageHandlers = [];
        this.galleryObserver = null;
        this.carouselEl = null;
        this.lensSize = DEFAULT_LENS_SIZE;
        this.zoomFactor = DEFAULT_ZOOM;
        this.onCarouselSlide = this.deactivate.bind(this);
        this.onWindowResize = this.throttled(this.onResize.bind(this));
        this.onDragStart = (ev) => ev.preventDefault();
        this.onFinePointerChange = () => {
            if (this._isDisabled()) {
                this.deactivate();
                this._unbindImages();
            } else {
                this._bindImages();
            }
        };
    }

    start() {
        this.imagesCol = this.el.querySelector(
            '.o_wsale_product_images, .kingdom-product-images-magnifier'
        );
        if (!this.imagesCol) {
            return;
        }

        this._createLens();
        this._readConfig();

        if (!this._isDisabled()) {
            this._bindImages();
        }

        this._observeGallery();
        this._bindCarousel();

        window.addEventListener('resize', this.onWindowResize);
        this.registerCleanup(() => window.removeEventListener('resize', this.onWindowResize));

        if (window.matchMedia) {
            this.finePointerMq = window.matchMedia('(hover: hover) and (pointer: fine)');
            if (this.finePointerMq.addEventListener) {
                this.finePointerMq.addEventListener('change', this.onFinePointerChange);
                this.registerCleanup(() =>
                    this.finePointerMq.removeEventListener('change', this.onFinePointerChange)
                );
            }
        }
    }

    destroy() {
        this.deactivate();
        this._unbindImages();
        this.galleryObserver?.disconnect();
        if (this.carouselEl) {
            this.carouselEl.removeEventListener('slide.bs.carousel', this.onCarouselSlide);
        }
        if (this.rafId) {
            cancelAnimationFrame(this.rafId);
            this.rafId = null;
        }
        this.lens?.remove();
        this.lens = null;
        this.lensView = null;
        return super.destroy(...arguments);
    }

    /**
     * Desktop fine-pointer only. Avoid hasTouch() — many laptops report
     * touch capability and would incorrectly disable the magnifier.
     */
    _isDisabled() {
        if (document.body.classList.contains('editor_enable')) {
            return true;
        }
        if (window.matchMedia) {
            return !window.matchMedia('(hover: hover) and (pointer: fine)').matches;
        }
        return false;
    }

    _createLens() {
        this.lens = document.createElement('div');
        this.lens.className = 'kingdom-zoomple-lens';
        this.lens.setAttribute('aria-hidden', 'true');
        this.lensView = document.createElement('div');
        this.lensView.className = 'kingdom-zoomple-lens__view';
        this.lens.appendChild(this.lensView);
    }

    _readConfig() {
        const styles = getComputedStyle(this.imagesCol);
        const size = parseFloat(styles.getPropertyValue('--kingdom-zoomple-size'));
        const zoom = parseFloat(styles.getPropertyValue('--kingdom-zoomple-zoom'));
        this.lensSize = Number.isFinite(size)
            ? Math.min(MAX_LENS_SIZE, Math.max(MIN_LENS_SIZE, size))
            : DEFAULT_LENS_SIZE;
        this.zoomFactor = Number.isFinite(zoom)
            ? Math.min(MAX_ZOOM, Math.max(MIN_ZOOM, zoom))
            : DEFAULT_ZOOM;
        this.lens.style.width = `${this.lensSize}px`;
        this.lens.style.height = `${this.lensSize}px`;
    }

    /**
     * Prefer high-res zoom URL from Odoo; fall back to displayed src, upgrading
     * image_1024 → image_1920 when the URL pattern allows it.
     */
    _getZoomUrl(img) {
        if (!img) {
            return '';
        }
        const zoomImage = img.dataset.zoomImage;
        if (zoomImage) {
            return zoomImage;
        }
        const src = img.currentSrc || img.getAttribute('src') || '';
        if (!src) {
            return '';
        }
        if (src.includes('/image_1024')) {
            return src.replace('/image_1024', '/image_1920');
        }
        if (src.includes('/image_512')) {
            return src.replace('/image_512', '/image_1920');
        }
        if (src.includes('/image_256')) {
            return src.replace('/image_256', '/image_1920');
        }
        return src;
    }

    _isProductImage(img) {
        return !!img?.classList.contains('product_detail_img');
    }

    _bindImages() {
        this._unbindImages();
        for (const img of this.el.querySelectorAll('.product_detail_img')) {
            if (!this._isProductImage(img)) {
                continue;
            }
            img.classList.add('kingdom-product-detail-img--magnifiable');
            img.draggable = false;

            const onEnter = (ev) => this.activate(img, ev);
            const onMove = (ev) => this.scheduleUpdate(ev);
            const onLeave = () => this.deactivate();

            img.addEventListener('mouseenter', onEnter);
            img.addEventListener('mousemove', onMove);
            img.addEventListener('mouseleave', onLeave);
            img.addEventListener('dragstart', this.onDragStart);

            this.imageHandlers.push({ img, onEnter, onMove, onLeave });
        }
    }

    _unbindImages() {
        for (const { img, onEnter, onMove, onLeave } of this.imageHandlers) {
            img.removeEventListener('mouseenter', onEnter);
            img.removeEventListener('mousemove', onMove);
            img.removeEventListener('mouseleave', onLeave);
            img.removeEventListener('dragstart', this.onDragStart);
            img.classList.remove('kingdom-product-detail-img--magnifiable');
        }
        this.imageHandlers = [];
    }

    _observeGallery() {
        this.galleryObserver?.disconnect();
        this.galleryObserver = new MutationObserver((mutations) => {
            const relevant = mutations.some((mutation) => {
                if (mutation.type === 'attributes') {
                    return (
                        mutation.target.classList?.contains('carousel-item') ||
                        mutation.target.id === 'o-carousel-product' ||
                        mutation.target.id === 'o-grid-product'
                    );
                }
                for (const node of [...mutation.addedNodes, ...mutation.removedNodes]) {
                    if (node.nodeType !== Node.ELEMENT_NODE) {
                        continue;
                    }
                    if (node.classList?.contains('kingdom-zoomple-lens')) {
                        continue;
                    }
                    return true;
                }
                return false;
            });
            if (!relevant) {
                return;
            }
            this.deactivate();
            this._readConfig();
            if (!this._isDisabled()) {
                this._bindImages();
            }
            this._bindCarousel();
        });
        this.galleryObserver.observe(this.imagesCol, {
            childList: true,
            subtree: true,
            attributes: true,
            attributeFilter: ['class'],
        });
        this.registerCleanup(() => this.galleryObserver?.disconnect());
    }

    _bindCarousel() {
        const carousel = this.el.querySelector('#o-carousel-product');
        if (this.carouselEl && this.carouselEl !== carousel) {
            this.carouselEl.removeEventListener('slide.bs.carousel', this.onCarouselSlide);
        }
        this.carouselEl = carousel;
        if (this.carouselEl) {
            this.carouselEl.addEventListener('slide.bs.carousel', this.onCarouselSlide);
        }
    }

    activate(img, ev) {
        if (this._isDisabled() || !this._isProductImage(img)) {
            return;
        }
        const zoomUrl = this._getZoomUrl(img);
        if (!zoomUrl) {
            return;
        }

        const rect = img.getBoundingClientRect();
        if (rect.width < 80 || rect.height < 80) {
            return;
        }

        this.activeImg = img;
        this.activeWrapper =
            img.closest('.o_product_detail_img_wrapper') ||
            img.closest('.carousel-item') ||
            img.parentElement;
        if (!this.activeWrapper) {
            return;
        }

        // Keep the lens inside a relatively-positioned, non-clipping host.
        this.activeWrapper.classList.add('kingdom-zoomple-host');
        if (this.lens.parentElement !== this.activeWrapper) {
            this.activeWrapper.appendChild(this.lens);
        }
        this.lens.classList.add('is-active');
        this.lens.setAttribute('aria-hidden', 'false');

        if (this.loadedZoomUrl !== zoomUrl) {
            this.loadedZoomUrl = zoomUrl;
            this.lensView.style.backgroundImage = `url("${zoomUrl}")`;
        }

        this.scheduleUpdate(ev);
    }

    deactivate() {
        this.activeImg = null;
        this.activeWrapper?.classList.remove('kingdom-zoomple-host');
        this.activeWrapper = null;
        this.pendingEvent = null;
        if (this.rafId) {
            cancelAnimationFrame(this.rafId);
            this.rafId = null;
        }
        this.lens?.classList.remove('is-active');
        this.lens?.setAttribute('aria-hidden', 'true');
        this.lens?.remove();
    }

    onResize() {
        this._readConfig();
        this.deactivate();
    }

    scheduleUpdate(ev) {
        this.pendingEvent = ev;
        if (!this.rafId) {
            this.rafId = requestAnimationFrame(() => this._renderLens());
        }
    }

    _renderLens() {
        this.rafId = null;
        const ev = this.pendingEvent;
        const img = this.activeImg;
        const wrapper = this.activeWrapper;
        if (!ev || !img || !wrapper) {
            return;
        }

        const rect = img.getBoundingClientRect();
        if (!rect.width || !rect.height) {
            return;
        }

        // Shrink lens if the image is smaller than the configured size.
        const lensSize = Math.min(this.lensSize, rect.width, rect.height);
        const radius = lensSize / 2;
        this.lens.style.width = `${lensSize}px`;
        this.lens.style.height = `${lensSize}px`;

        const x = clamp(ev.clientX - rect.left, 0, rect.width);
        const y = clamp(ev.clientY - rect.top, 0, rect.height);
        const lensX = clamp(x - radius, 0, rect.width - lensSize);
        const lensY = clamp(y - radius, 0, rect.height - lensSize);

        const wrapperRect = wrapper.getBoundingClientRect();
        const offsetLeft = rect.left - wrapperRect.left;
        const offsetTop = rect.top - wrapperRect.top;

        this.lens.style.transform = `translate3d(${offsetLeft + lensX}px, ${offsetTop + lensY}px, 0)`;

        const bgWidth = rect.width * this.zoomFactor;
        const bgHeight = rect.height * this.zoomFactor;
        // Keep the point under the cursor centered in the lens.
        const bgX = -(x * this.zoomFactor - radius);
        const bgY = -(y * this.zoomFactor - radius);

        this.lensView.style.backgroundSize = `${bgWidth}px ${bgHeight}px`;
        this.lensView.style.backgroundPosition = `${bgX}px ${bgY}px`;
    }
}

function clamp(value, min, max) {
    return Math.max(min, Math.min(value, max));
}

registry
    .category('public.interactions')
    .add('theme_kingdom.product_image_magnifier', KingdomProductImageMagnifier);
