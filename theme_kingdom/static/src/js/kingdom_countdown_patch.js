/** @odoo-module **/

import { Countdown } from "@website/snippets/s_countdown/countdown";

/**
 * Kingdom's countdown snippet previously used class `s_countdown`, which is the
 * selector for Odoo's canvas countdown interaction. That interaction expects
 * `data-display` (and a canvas wrapper) and crashes with:
 *   Cannot read properties of undefined (reading 'includes')
 * Exclude Kingdom timers (marked by `.k-countdown` / data-snippet) so Odoo
 * never attaches — covers pages saved before the class rename.
 */
Countdown.selector =
    ".s_countdown:not(:has(.k-countdown)):not([data-snippet='theme_kingdom.s_countdown'])";
