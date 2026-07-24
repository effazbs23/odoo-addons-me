/** @odoo-module **/

import { Interaction } from '@web/public/interaction';
import { registry } from '@web/core/registry';
import { rpc } from '@web/core/network/rpc';

/**
 * Coming Soon subscription form — AJAX submit with inline status.
 */
export class KingdomComingSoonSubscribe extends Interaction {
    static selector = '.k-coming-soon__form';

    dynamicContent = {
        _root: {
            't-on-submit.prevent': this.locked(this.onSubmit),
        },
    };

    setup() {
        this._messageEl = this.el.querySelector('.k-coming-soon__message');
        this._input = this.el.querySelector('input[name="email"]');
        this._button = this.el.querySelector('button[type="submit"]');
    }

    _setMessage(text, type) {
        if (!this._messageEl) {
            return;
        }
        this._messageEl.hidden = !text;
        this._messageEl.textContent = text || '';
        this._messageEl.classList.toggle('is-success', type === 'success');
        this._messageEl.classList.toggle('is-error', type === 'error');
    }

    async onSubmit() {
        const email = (this._input?.value || '').trim();
        if (!email) {
            this._setMessage('Please enter your email address.', 'error');
            this._input?.focus();
            return;
        }

        if (this._button) {
            this._button.disabled = true;
        }
        this._setMessage('Submitting…', 'success');

        try {
            const result = await this.waitFor(
                rpc('/theme_kingdom/coming_soon/subscribe', { email })
            );
            if (result?.error) {
                this._setMessage(result.error, 'error');
            } else {
                this._setMessage(result?.message || 'Thanks! We will notify you.', 'success');
                if (this._input) {
                    this._input.value = '';
                }
            }
        } catch (_error) {
            this._setMessage('Unable to subscribe right now. Please try again.', 'error');
        } finally {
            if (this._button) {
                this._button.disabled = false;
            }
        }
    }
}

registry
    .category('public.interactions')
    .add('theme_kingdom.coming_soon_subscribe', KingdomComingSoonSubscribe);
