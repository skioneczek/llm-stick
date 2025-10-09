# Ingest Flow (Large-Text First)

## Entry Point — Ingest Button
- Location: Controls row (same level as Presets / Set Data Folder). 60pt label "Ingest" with helper copy "Bring new files in" (aria-describedby).
- Keyboard: `Alt+I` opens flow; retains 4px high-contrast focus ring.
- Voice: OFF by default; if Voice Mode ON, announce "Ingest opens. Follow on-screen steps." once.
- Threads list (chat) shortcut: After ingest completes, focus returns to threads pane with `aria-live="polite"` message "New documents available. Create a thread to review.".

## Step 1 — Select Folder
- Screen: Native folder picker with 48pt header "Choose the folder to ingest." Helper text 36pt: "Scan locally; may take a while; safe to minimize."
- Aria: `aria-describedby="ingest-helper"` describing offline processing and duration; `aria-live="polite"` for confirmation when selection made.
- Keyboard: Arrow keys browse; Enter confirms; Esc cancels (returns to home.

## Step 2 — Storage Choice Dialog
- Title: 48pt "Where should we store the indexed data?"
- Options: Two 60pt radio tiles (Computer vs USB) with one-line tradeoffs.
  - **Computer (faster)** — Stores index on the host computer; quickest access; stays read-only.
  - **USB (encrypted)** — Stores index on the stick; slower but encrypted at rest.
- Default selection: Computer (HOST_LOCAL) per current ingest plan; tooltip clarifies "You can switch later".
- Keyboard: Tab/Shift+Tab cycle options; Arrow keys move between radio tiles; Enter confirms.
- Aria: Each tile has `aria-label` covering storage type + tradeoff. If USB not available, announce "Encrypted storage currently unavailable".

## Step 3 — Hotswap Client List
- Screen: Full-width grid of large tiles (minimum 220px height). 60pt client name at top, 36pt subtext "Last indexed: {date}".
- Interaction: Clicking tile switches active client context before ingest; top tile is most recent client.
- Keyboard: Arrow keys navigate tiles; Enter selects; Esc cancels.
- Aria: `aria-live="polite"` announces "Selected {client name}. Last indexed {date}." for focus changes.
- Empty state (when no clients yet): 60pt banner "Choose a client, or ingest first." matches chat threads list copy.

## Step 4 — Confirmation Summary
- Display selected folder, storage choice, client context.
- Buttons: 60pt "Start ingest" (primary) and 60pt "Cancel" (secondary).
- Helper line: "Scan locally; may take a while; safe to minimize."
- Aria: `aria-describedby` linking helper text; if storage=USB, add line "Requires encryption provider; we will alert you if unavailable.".

## Background Progress View
- Screen: Plain text progress (48pt) with lines like "Scanning 12 of 200 files…"; no animations.
- Buttons: 48pt "Pause" and "Cancel"; Esc cancels with 3-second grace banner "Press Esc again to confirm cancel.".
- Aria: `role="status"` updates progress; `aria-live="polite"` for pause/resume; no auto speech unless Voice Mode ON (then read status once per change).
- Archive/search messaging: If ingest triggered from chat empty state, show toast "Thread list will update after ingest." (aria-live polite).

## Completion States
- Success banner: "Ingest complete. Files ready." plus "All processing stayed on this device." (aria-live polite).
- Warning (needs confirm): If source guard flagged confirm requirement, banner "Needs confirmation — run Set Data Folder or contact support.".
- Error: Show exact audit line from `validate_source`; keep data unchanged.
- Post-ingest actions: Offer buttons "Start new thread" (Alt+N) and "Run search" (Alt+F) with helper copy "Use Hotswap to switch clients.".

## Accessibility Notes
- Ensure font sizes 48–72pt across dialogs.
- Maintain high-contrast focus outlines and aria-describedby guidance on each step.
- Provide `Alt+H` shortcut from home screen to open Hotswap list directly (without ingest) for quick client switching.
- Voice Mode remains optional/offline; do not auto-play speech.
