/** @odoo-module **/

import { CountdownOption } from "@website/builder/plugins/options/countdown_option_plugin";

/**
 * Keep Odoo's countdown builder options off Kingdom countdown snippets that
 * still carry the legacy `s_countdown` class.
 */
CountdownOption.selector =
    ".s_countdown:not(:has(.k-countdown)):not([data-snippet='theme_kingdom.s_countdown'])";
