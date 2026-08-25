/** @odoo-module **/

import { patch } from '@web/core/utils/patch';
import { _t } from '@web/core/l10n/translation';
import { browser } from '@web/core/browser/browser';
import { session } from '@web/session';
import { WebsiteSwitcherSystrayItem } from '@website/client_actions/website_preview/website_switcher_systray_item';
import { isHTTPSorNakedDomainRedirection } from '@website/client_actions/website_preview/utils';

/**
 * Guard Website preview systray when currentWebsite is not resolved yet
 * (e.g. stale website_id in the action hash). Core getElements() crashes on
 * `this.websiteService.currentWebsite.id`.
 */
patch(WebsiteSwitcherSystrayItem.prototype, {
    getElements() {
        const currentId = this.websiteService.currentWebsite?.id;
        return (this.websiteService.websites || [])
            .filter((website) => website && website.id)
            .map((website) => ({
                name: website.name,
                id: website.id,
                domain: website.domain,
                dataset: Object.assign(
                    {
                        'data-website-id': website.id,
                    },
                    website.domain
                        ? {}
                        : {
                              'data-tooltip': _t('This website does not have a domain configured.'),
                              'data-tooltip-position': 'left',
                          }
                ),
                callback: () => {
                    if (
                        !session.website_bypass_domain_redirect &&
                        website.domain &&
                        !isHTTPSorNakedDomainRedirection(website.domain, window.location.origin)
                    ) {
                        const {
                            location: { pathname, search, hash },
                        } = this.websiteService.contentWindow;
                        const path = pathname + search + hash;
                        const url = new URL('/web', website.domain);
                        url.hash = new URLSearchParams({
                            action: 'website.website_preview',
                            path: path,
                            website_id: website.id,
                        });
                        window.location.href = url;
                    } else {
                        this.websiteService.goToWebsite({
                            websiteId: website.id,
                            path: '',
                            lang: 'default',
                        });
                        if (!website.domain) {
                            const closeFn = this.notificationService.add(
                                _t('Add a domain to your website.'),
                                {
                                    type: 'warning',
                                    sticky: true,
                                    buttons: [
                                        {
                                            onClick: () => {
                                                this.actionService.doAction(
                                                    'website.action_website_configuration'
                                                );
                                                closeFn();
                                            },
                                            primary: true,
                                            name: 'Settings',
                                        },
                                    ],
                                }
                            );
                            browser.setTimeout(closeFn, 7000);
                        }
                    }
                },
                class:
                    currentId && website.id === currentId
                        ? 'text-truncate active'
                        : 'text-truncate',
            }));
    },
});
