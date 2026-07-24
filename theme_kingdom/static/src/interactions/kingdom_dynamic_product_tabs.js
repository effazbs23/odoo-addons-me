/** @odoo-module **/

import { Interaction } from '@web/public/interaction';
import { registry } from '@web/core/registry';
import { rpc } from '@web/core/network/rpc';

/**
 * Dynamic Product Tabs: switch tabs via AJAX, cache loaded panels.
 */
export class KingdomDynamicProductTabs extends Interaction {
    static selector = '.k-dyn-tabs';

    dynamicContent = {
        '.k-dyn-tabs__tab': {
            't-on-click.prevent': this.locked(this.onTabClick),
        },
    };

    setup() {
        this._cache = new Map();
        this._activeRequest = 0;
    }

    start() {
        // Cache the initially rendered panel.
        const activePanel = this.el.querySelector('.k-dyn-tabs__panel.is-active[data-tab-id]');
        if (activePanel?.dataset.tabId) {
            this._cache.set(activePanel.dataset.tabId, activePanel.innerHTML);
        }
        return super.start(...arguments);
    }

    async onTabClick(ev) {
        const button = ev.currentTarget;
        const tabId = button.dataset.tabId;
        if (!tabId || button.classList.contains('is-active')) {
            return;
        }

        this.el.querySelectorAll('.k-dyn-tabs__tab').forEach((tab) => {
            const active = tab === button;
            tab.classList.toggle('is-active', active);
            tab.setAttribute('aria-selected', active ? 'true' : 'false');
        });

        let panel = this.el.querySelector(`.k-dyn-tabs__panel[data-tab-id="${tabId}"]`);
        const panelsRoot = this.el.querySelector('.k-dyn-tabs__panels');
        if (!panelsRoot) {
            return;
        }

        this.el.querySelectorAll('.k-dyn-tabs__panel').forEach((el) => {
            el.classList.remove('is-active');
            el.hidden = true;
        });

        if (!panel) {
            panel = document.createElement('div');
            panel.className = 'k-dyn-tabs__panel';
            panel.setAttribute('role', 'tabpanel');
            panel.dataset.tabId = tabId;
            panel.id = `kDynPanel-${tabId}`;
            panel.setAttribute('aria-labelledby', `kDynTab-${tabId}`);
            panelsRoot.appendChild(panel);
        }

        panel.hidden = false;
        panel.classList.add('is-active');

        if (this._cache.has(tabId)) {
            panel.innerHTML = this._cache.get(tabId);
            await this._startPanelInteractions(panel);
            return;
        }

        panel.innerHTML = '<div class="k-dyn-tabs-loading">Loading…</div>';
        const requestId = ++this._activeRequest;
        try {
            const html = await this.waitFor(
                rpc('/theme_kingdom/product_tabs/render', { tab_id: parseInt(tabId, 10) })
            );
            if (requestId !== this._activeRequest) {
                return;
            }
            panel.innerHTML = typeof html === 'string' ? html : String(html ?? '');
            this._cache.set(tabId, panel.innerHTML);
            panel.dataset.loaded = '1';
            await this._startPanelInteractions(panel);
        } catch (_error) {
            if (requestId !== this._activeRequest) {
                return;
            }
            panel.innerHTML =
                '<p class="k-dyn-tabs-empty">Unable to load products for this tab.</p>';
        }
    }

    async _startPanelInteractions(panel) {
        if (!panel || !this.services['public.interactions']) {
            return;
        }
        await this.waitFor(this.services['public.interactions'].startInteractions(panel));
    }
}

registry
    .category('public.interactions')
    .add('theme_kingdom.dynamic_product_tabs', KingdomDynamicProductTabs);
