/** @odoo-module **/

/**
 * Picks black or white text so labels stay readable on top of an
 * arbitrary user-chosen background color (perceived-brightness/YIQ
 * formula). Falls back to white on a malformed hex value.
 */
export function getContrastingTextColor(hex) {
    const cleanHex = (hex || "").replace("#", "");
    const fullHex =
        cleanHex.length === 3
            ? cleanHex
                  .split("")
                  .map((char) => char + char)
                  .join("")
            : cleanHex;
    if (!/^[0-9A-Fa-f]{6}$/.test(fullHex)) {
        return "#FFFFFF";
    }
    const red = parseInt(fullHex.substring(0, 2), 16);
    const green = parseInt(fullHex.substring(2, 4), 16);
    const blue = parseInt(fullHex.substring(4, 6), 16);
    const brightness = (red * 299 + green * 587 + blue * 114) / 1000;
    return brightness > 150 ? "#000000" : "#FFFFFF";
}
