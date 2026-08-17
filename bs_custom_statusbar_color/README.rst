Custom Statusbar Color
=======================

Configurable, per-state coloring for statusbar widgets, defined rule by
rule - nothing is pre-populated.

Features
--------

- "Custom Statusbar Color" app: starts empty. Click "New", name your rule,
  and pick the model whose statusbar you want to color.
- As soon as a model is picked, its statusbar states are discovered
  automatically (only fields actually rendered with
  widget="statusbar" in a real view qualify) and shown as a live
  preview of the real statusbar. Click a state's button to select it;
  a panel appears with:

  - Default Color: used when that step is shown but the record is NOT
    currently in it (a past or upcoming step).
  - In State Color: used when the record IS currently in that state.
  - An Enabled toggle for that specific state.

  Selecting a button previews it with its In State color (as if it
  were active) while its siblings show their Default color. Each
  color picker supports presets, a typed hex code, or the native RGB
  picker.
- A rule-level Enabled toggle turns all of its states on/off at once.
- Colors are applied globally to the native statusbar widget everywhere
  it's used, with no changes required to existing views. Text color is
  auto-adjusted (black/white) for contrast against whatever color is
  picked.
- Findable from the global command palette (Ctrl+K).

Usage
-----

1. Open the "Custom Statusbar Color" app and click "New".
2. Name the rule and pick a model - its states appear automatically.
3. Click a state, pick a Default Color and/or In State Color, toggle it
   on. Toggle the rule itself on to apply it.
4. If the model's views change later (new state added, widget
   changed), use "Scan States" to re-sync.

This module supersedes ``web_statusbar_color_patch`` (the color patch
logic is now built in and driven by this configuration UI). That module
can be uninstalled once this one is verified.
