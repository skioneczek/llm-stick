# Enhanced Visual Window (Full-Screen Large Text)

## Overview
- Mode: Full-screen layout optimized for low-vision (John) with 60–72pt body text.
- Voice Mode: OFF by default; announcements only if user toggles Voice ON.
- Focus: All actionable elements keep 4px high-contrast focus ring and `aria-describedby` for shortcut hints.

## Regions
1. **Title Bar** (top 120px)
   - Left: App name + active security mode (Standard/Hardened/Paranoid) in 48pt text.
   - Center: Current time and offline status indicator (text-based, no color reliance).
   - Right: Help icon (48pt) and close button (60pt) with redundant text labels.

2. **Toolbar** (under title bar)
   - 60pt controls in order: System Preset | User Preset | Print (Large Text) | Export PDF | Sources | Set Data Folder | Ingest | Hotswap | Security slider | Voice | Panic | Enhanced Visual toggle.
   - Print button shows tooltip "Print in large text" and uses shortcut Alt+P; Export uses Alt+E with helper "Creates a standard-print PDF for sharing. All local.".
   - CLI button (`Open CLI`) visible only in Standard view; in Enhanced Visual mode it is hidden, `aria-hidden="true"`, and removed from tab order.
   - Enhanced Visual toggle announcement: `aria-live="polite"` message "Enhanced Visual mode on." for 3 seconds when enabled.

3. **Main Split**
   - Left pane (**Threads list**): 60pt titles, 36pt timestamps/badges, width ~480px; `aria-label="Conversations"`. Empty state copy "Choose a client, or ingest first" with helper line "Use Set Data Folder or Ingest to add documents." announced via `aria-live` when shown.
   - Right pane (**Conversation area**): 60pt system/user bubbles, timestamps 36pt; `aria-live="polite"` for new messages. Sources panel slides over this pane with heading "Sources" and list entries `filename — YYYY-MM-DD` only.

4. **Composer**
   - 72pt textarea with placeholder "Type your question" and helper `aria-describedby` "Press Enter to send. Shift+Enter for newline.".
   - Send button 72pt with high-contrast outline; Enter activates.

5. **Footer Audit Strip**
   - 48pt text area showing latest enforcement/audit line (e.g., "Scan may take time; all local.").
   - Uses `role="status"` for screen readers.

## Keyboard Shortcuts
- `Alt+Plus` / `Alt+Minus`: Increase/decrease font size (60↔72pt bounds).
- `Alt+S`: Toggle Serif/Sans.
- `Alt+B`: Toggle Bold weight.
- `Alt+C`: Cycle contrast themes (High-contrast black/white, Off-white/dark gray, Yellow/charcoal).
- `Alt+I`: Open Ingest flow.
- `Alt+H`: Open Hotswap client list.
- `Alt+V`: Toggle Voice Mode.
- `Alt+F`: Focus answer canvas (for screen reader review).
- `Alt+N`: Start new thread and focus composer (`aria-live` "New thread created.").
- `Alt+F` (threads view): Focus search field in threads list; announce "Search threads" via `aria-live`.
- `Alt+P`: Trigger Print (Large Text) button.
- `Alt+E`: Trigger Export PDF button.
- `Alt+1/2/3`: Apply preset slots with polite announcement (e.g., "System preset 1 applied.").
- `Delete`: Archive highlighted thread; shows 3-second undo toast.
- `Esc`: Cancel modals (3-second grace message "Press Esc again within 3 seconds to confirm.").

## Aria / Accessibility Notes
- Each control uses `aria-describedby` specifying its shortcut (e.g., "Alt+I opens ingest dialog.").
- Preset dropdown announces selection via `aria-live="polite"` ("High-contrast sans preset applied.").
- Ingest/Hotswap modals announce header text only once, no auto-speech beyond that.
- Panic button warns with `aria-describedby` pointing to "Press Esc within 3 seconds to cancel.".
- Ensure contrast ratio ≥ 7:1 for all text on backgrounds.
- Threads list updates `aria-live="polite"` when search/filter changes ("Showing {count} threads.").
- Archive/undo toast uses `role="alert"` with text "Thread archived. Press Undo within 3 seconds." and provides focusable Undo button.
- Sources panel emphasises "Filenames and dates shown." (aria-live polite) and suppresses PII.

## Interaction Notes
- When Ingest/Hotswap modals open, underlying answer canvas dims but remains readable.
- Progress indicators remain text-only (e.g., "Scanning 5 of 40 files…"), updated via status region.
- Voice Mode (if enabled) reads only explicit system prompts; no automatic reading of full answers without user request.
- Enhanced Visual mode enlarges spacing/padding; CLI button stays hidden until mode toggled off.
