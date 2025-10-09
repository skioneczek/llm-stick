# PIN Lifecycle Copy (Large Text)

## Change PIN (Settings → Security) — 36pt headings, 48pt buttons
- Screen text: "Change your 6-digit PIN" with helper line "Type current PIN, then enter a new one." (screen-reader: aria-label="Change PIN form"; aria-describedby points to helper line).
- Fields: Current PIN, New PIN, Confirm PIN (each 48pt masked input with high-contrast focus ring; aria-labels match field names; aria-live "polite" for validation hints).
- Buttons: "Cancel" (30% gray background) and "Save new PIN" (high-contrast primary). Keyboard: Tab order top to bottom; Enter submits.
- Validation copy: "PINs must be 6 digits." / "New PINs must match." / "Current PIN incorrect." (aria-live updates; no digits spoken aloud).
- Success toast: "PIN updated." (aria-live="assertive"; no voice unless user enabled Voice Mode manually).

## Reset PIN via Recovery Phrase — 36pt headings, offline only
- Gate: "Forgot PIN?" link under keypad, 32pt text. aria-label="Forgot PIN — open recovery flow".
- Step 1 text: "Enter your recovery phrase to reset your PIN." Input is large multiline field with aria-describedby "Recover offline. Nothing leaves this device.".
- Step 2 text: "Choose a new 6-digit PIN." (same validation copy as Change PIN). Helper line: "Voice Mode stays off until you finish.".
- Confirmation: "PIN reset. Use your new PIN to sign in." (aria-live assertive). No automatic speech.

## Lockout Messaging — high contrast banners
- After 3 failed attempts: Banner "PIN not recognized. 2 tries left." (aria-live assertive). Keep keypad active.
- After 5 failed attempts: Banner "Too many attempts. Try again in 5 minutes." Disable keypad buttons; aria-live assertive announces cooldown.
- While locked out: screen shows countdown label "Locked. Try again in {mm}:{ss}" (aria-labelledby for timer). Provide "Panic" button and "Forgot PIN" recovery link only.
- Post-cooldown: banner "You can try again now." keypad re-enabled; voice remains off unless user toggled it before lockout.
