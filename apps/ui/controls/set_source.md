# Set Data Folder Control (32–48pt intent)

## Overview
- Label: "Set Data Folder" (48pt button text; aria-label="Set Data Folder — choose client files").
- Availability: Visible after PIN unlock on the home screen alongside core commands.
- Purpose: Lets the user point the stick at a read-only client folder (e.g., `C:\OCRC_READONLY\Client_A`).

## Interaction Flow
1. **Activate button**
   - Button copy: "Set Data Folder" with helper text below: "Use this to choose where the stick looks for files." (aria-describedby on button).
   - Keyboard: Space/Enter activates; button keeps 4px high-contrast focus ring.

2. **Folder picker dialog**
   - Opens native folder chooser; 36pt header "Pick the folder containing the client files." (voice prompt if Voice Mode currently ON: speak same sentence; otherwise silent).
   - Screen reader hint: aria-live "assertive" message "Folder picker open. Use arrow keys to choose a folder.".
   - Reminder text: "Indexing stays local and may take a few minutes." shown in 32pt under header.

3. **Selection summary sheet**
   - After user picks folder, show confirmation panel with:
     - Path display in 36pt monospace (aria-label="Chosen folder path").
     - Buttons: "Confirm" (primary) and "Cancel" (secondary). Both 44px min height with focus rings.
     - Helper copy: "The app will scan this folder offline." (aria-describedby for Confirm).
   - Keyboard: Tab cycles path → Confirm → Cancel; Enter activates highlighted button; Esc equals Cancel.

4. **Completion states**
   - On Confirm: show toast "Data folder set to {path}." (aria-live="polite"). Trigger background index update flow (separate service owns auditing/logging).
   - On Cancel: return to home screen; helper text "Data folder unchanged." displayed in 36pt for 3 seconds (aria-live polite).

## Accessibility Requirements
- Button contrast ratio ≥ 7:1; 48pt text ensures readability for low-vision users.
- All helper copy tied via aria-describedby to explain offline-only processing and potential wait.
- Voice Mode OFF by default: no speech until user enables Voice Mode. If ON, speak the header lines once.
- Provide screen reader role="status" for the toast so the path update is announced without repeating PII beyond folder name.
