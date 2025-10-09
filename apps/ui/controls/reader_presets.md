# Reader Presets (Accessibility First)

## Preset A — High-Contrast Sans 60 (Default)
- Typeface: Humanist sans-serif, 60pt, extra bold weight.
- Colors: Black text (#000000) on pure white (#FFFFFF); line spacing 1.6.
- Aria label: `aria-label="High-contrast sans preset selected"`.
- Shortcut hints: `Alt+Plus` increase size, `Alt+Minus` decrease, `Alt+S` toggle serif/sans, `Alt+B` toggle bold, `Alt+C` cycle contrast.
- Screen reader note: announce "High-contrast sans preset applied." via `aria-live="polite"`.

## Preset B — Serif Comfort 48
- Typeface: Slab serif, 48pt, bold weight.
- Colors: Off-white text (#F5F2E8) on very dark gray (#121212) with 1.6 line spacing.
- Aria label: `aria-label="Serif comfort preset selected"`.
- Shortcut hints: same key bindings; on selection, announce "Serif comfort preset applied.".

## Preset C — Mega Sans 72
- Typeface: Geometric sans-serif, 72pt, bold weight.
- Colors: White text (#FFFFFF) on charcoal (#1A1A1A); 1.5 line spacing to maintain legibility at size.
- Aria label: `aria-label="Mega sans preset selected"`.
- Shortcut hints: same keys; announce "Mega sans preset applied." and remind user "Scroll for full answer" via `aria-live` when content overflows.

## Global Controls
- Display controls row with buttons: `Presets`, `Font size ±`, `Serif/Sans`, `Bold`, `Contrast`, each 48pt labels and 44px minimum height.
- Keyboard shortcuts: `Alt+Plus`/`Alt+Minus` adjust size; `Alt+S` toggles serif/sans; `Alt+B` toggles bold; `Alt+C` cycles contrast schemes.
- Screen reader instructions: Provide `aria-describedby` text "Use Alt plus/minus to adjust size. Alt+S toggles serif. Alt+B toggles bold. Alt+C switches contrast.".
- Voice Mode stays OFF unless toggled; if ON, read preset confirmation line once then remain silent.
