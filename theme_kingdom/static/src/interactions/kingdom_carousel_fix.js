/** @odoo-module **/

import { Interaction } from '@web/public/interaction';
import { registry } from '@web/core/registry';

/**
 * Bootstrap Carousel crashes when indicators exist but lack data-bs-slide-to:
 * after the first slide, no indicator has .active, so the next tick throws
 * "Cannot read properties of null (reading 'classList')".
 *
 * Repair indicators and harden Bootstrap's setter for all carousels.
 */
function repairCarouselIndicators(carouselEl) {
    const indicatorsEl = carouselEl.querySelector('.carousel-indicators');
    if (!indicatorsEl) {
        return;
    }
    const slides = carouselEl.querySelectorAll('.carousel-inner > .carousel-item');
    const indicators = [...indicatorsEl.querySelectorAll('button, li')];
    if (!slides.length) {
        return;
    }

    // Ensure one indicator per slide with a usable data-bs-slide-to index.
    const target = carouselEl.id ? `#${carouselEl.id}` : null;
    indicators.forEach((indicator, index) => {
        if (index >= slides.length) {
            indicator.remove();
            return;
        }
        if (!indicator.hasAttribute('data-bs-slide-to')) {
            indicator.setAttribute('data-bs-slide-to', String(index));
        }
        if (target && !indicator.getAttribute('data-bs-target')) {
            indicator.setAttribute('data-bs-target', target);
        }
        indicator.classList.toggle('active', slides[index].classList.contains('active'));
        if (slides[index].classList.contains('active')) {
            indicator.setAttribute('aria-current', 'true');
        } else {
            indicator.removeAttribute('aria-current');
        }
    });

    // Create missing indicators when slides were added in the editor.
    for (let index = indicators.length; index < slides.length; index++) {
        const button = document.createElement('button');
        button.type = 'button';
        button.setAttribute('data-bs-slide-to', String(index));
        if (target) {
            button.setAttribute('data-bs-target', target);
        }
        button.setAttribute('aria-label', 'Carousel indicator');
        if (slides[index].classList.contains('active')) {
            button.classList.add('active');
            button.setAttribute('aria-current', 'true');
        }
        indicatorsEl.appendChild(button);
    }

    // Guarantee exactly one active indicator.
    const activeIndicators = indicatorsEl.querySelectorAll('.active');
    if (!activeIndicators.length) {
        const activeSlideIndex = [...slides].findIndex((slide) =>
            slide.classList.contains('active')
        );
        const fallback = indicatorsEl.querySelector(
            `[data-bs-slide-to="${Math.max(activeSlideIndex, 0)}"]`
        ) || indicatorsEl.querySelector('button, li');
        fallback?.classList.add('active');
        fallback?.setAttribute('aria-current', 'true');
    } else if (activeIndicators.length > 1) {
        activeIndicators.forEach((el, i) => {
            if (i === 0) {
                return;
            }
            el.classList.remove('active');
            el.removeAttribute('aria-current');
        });
    }
}

function patchBootstrapCarouselIndicators() {
    const Carousel = window.Carousel;
    if (!Carousel?.prototype || Carousel.prototype._kingdomIndicatorGuard) {
        return;
    }
    const original = Carousel.prototype._setActiveIndicatorElement;
    if (typeof original !== 'function') {
        return;
    }
    Carousel.prototype._setActiveIndicatorElement = function (index) {
        if (!this._indicatorsElement) {
            return;
        }
        const activeIndicator = this._indicatorsElement.querySelector('.active');
        activeIndicator?.classList.remove('active');
        activeIndicator?.removeAttribute('aria-current');
        const newActiveIndicator = this._indicatorsElement.querySelector(
            `[data-bs-slide-to="${index}"]`
        );
        if (newActiveIndicator) {
            newActiveIndicator.classList.add('active');
            newActiveIndicator.setAttribute('aria-current', 'true');
        }
    };
    Carousel.prototype._kingdomIndicatorGuard = true;
}

export class KingdomCarouselFix extends Interaction {
    static selector = '.carousel.slide';

    setup() {
        patchBootstrapCarouselIndicators();
        repairCarouselIndicators(this.el);
    }

    async willStart() {
        repairCarouselIndicators(this.el);
        // Recreate BS instance after repair so ride/interval keep working.
        if (this.el.dataset.bsRide || this.el.dataset.bsInterval) {
            window.Carousel?.getInstance(this.el)?.dispose();
        }
    }

    start() {
        repairCarouselIndicators(this.el);
        if (this.el.dataset.bsRide || this.el.dataset.bsInterval) {
            const carousel = window.Carousel?.getOrCreateInstance(this.el);
            if (carousel) {
                this.registerCleanup(() => carousel.dispose());
            }
        }
    }
}

registry
    .category('public.interactions')
    .add('theme_kingdom.carousel_fix', KingdomCarouselFix);
