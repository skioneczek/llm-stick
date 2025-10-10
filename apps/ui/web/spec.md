# Chat UI Specification (Accessibility First)

## Layout Overview
- **Toolbar (top strip)**: 60pt buttons in order — System Preset dropdown, User Preset dropdown, Print (Large Text), Export PDF, Sources, Set Data Folder, Ingest, Hotswap, Security slider, Voice toggle, Panic. CLI button appears only in Standard View; hidden in Enhanced Visual mode.
- **Main area**: Split left/right with adjustable divider.
  - **Threads list (left)**: Large cards stacked vertically, 48pt titles and 36pt subtext. Default width 360px in Standard, 480px in Enhanced Visual.
  - **Conversation pane (right)**: 48pt–60pt messages, high-contrast bubbles, time stamps in 32pt.
- **Composer (bottom of conversation)**: 48pt text area that expands to 72pt in Enhanced Visual; Send button 60pt, high-contrast outline, `aria-label="Send message"`.

## Threads List Details
- Thread card layout:
  - Title = first user line (trimmed) in 48pt bold.
  - Last activity timestamp 32pt; format "Today 14:05" / "Oct 9 2025".
  - Badges row with 32pt pill tags showing client slug and source slug; `aria-label` announces "Client {slug}; source {slug}.".
  - Archive dot (outer ring) toggled with Delete key; high-contrast focus ring.
- Empty state: 48pt centered text "Choose a client, or ingest first." with helper copy "Use Set Data Folder or Ingest to add documents." and `aria-live="polite"` on reveal.
- Keyboard focus order: Up/Down navigate threads; Enter opens; Delete archives (with 3s grace confirmation toast "Thread archived. Press Undo to restore".).

## Conversation Pane
- Message bubbles use 48pt text (Standard) or 60pt (Enhanced Visual). User messages right-aligned, system responses left.
- Sources panel toggle surfaces on toolbar. When open, side sheet slides in from right with 48pt heading "Sources" and list items `filename — YYYY-MM-DD` only; `aria-live="polite"` announces "Filenames and dates shown.".
- Empty conversation message: 48pt italic copy "Start by typing a question." displayed until first send.
- Archive and delete actions confirm via inline banner `role="alert"` "Thread archived. Press Undo within 3 seconds.".

- **System Presets dropdown**: 48pt trigger labeled "System Preset"; options show one-line summary (e.g., "Standard: 48pt sans"). `aria-label="Choose system preset"` and `aria-live` announcement when changed.
- **User Presets dropdown**: Same size; lists personal saved presets; includes "Reset to default".
- **Print (Large Text)**: 48pt button (Alt+P) invoking large-print flow; tooltip "Print in large text"; `aria-label="Print large-text view"`; hidden from tab order when `@media print` active.
- **Export PDF**: 48pt button (Alt+E) launching offline export routine; tooltip "Creates a local PDF; may fall back to browser Print to PDF."; `aria-label="Creates a local PDF; may fall back to browser Print to PDF."`; if PDF engine unavailable, disable with helper text and surface fallback toast.
- **Sources**: 48pt label; toggles side sheet; shows tooltip "Filenames and dates only.".
- **Set Data Folder / Ingest / Hotswap**: Mirror flows from large-text app; `Alt+I` and `Alt+H` shortcuts active.
- **Security slider**: 48pt segmented control; `aria-describedby` describing modes; blocks slider in Paranoid if adapters detected.
- **Voice toggle**: OFF by default; 48pt pill button; if ON, announces "Voice Mode enabled. Hold space to speak." once.
- **Panic**: 48pt red outline; `aria-describedby` "Press Esc within 3 seconds to cancel.".
- **CLI button**: 48pt icon+label "Open CLI"; visible only in Standard View; hidden and removed from tab order in Enhanced Visual.
- **Enhanced Visual toggle**: 48pt switch in toolbar (adjacent to presets); when ON, app fills screen, thread width increases, font sizes jump to 60/72pt, CLI button hidden.

## Composer
- Large textarea with placeholder "Type your question" (48pt / 60pt). `aria-describedby` reminding "Press Enter to send. Shift+Enter for newline.".
- Send button 60pt; also triggered by Enter.
- Attachment area intentionally omitted for security.

## Keyboard Shortcuts
- `Alt+N`: New thread (focus composer, create untitled entry; announces "New thread created." via `aria-live`).
- `Alt+F`: Focus search box in threads list.
- `Alt+P`: Trigger large-text print flow.
- `Alt+E`: Launch Export PDF dialog.
- `Delete`: Archive selected thread (shows 3-second undo toast).
- `Alt+1`: Apply System preset slot 1; `Alt+2` slot 2; `Alt+3` slot 3 (announced via `aria-live`).
- `Esc`: Cancels modals or destructive confirmations; 3-second grace message.
- Existing shortcuts (`Alt+Plus/Minus`, `Alt+S`, `Alt+B`, `Alt+C`, `Alt+I`, `Alt+H`, `Alt+V`) remain active.

## Search & Archive Feedback
- Search field sits atop threads list, 48pt input with `aria-label="Search threads"` and `Alt+F` shortcut.
- Results update `aria-live="polite"` message "Showing {count} threads.".
- Archive action shows toast "Thread archived. Press Undo within 3 seconds." with Undo button (48pt) focusable.

## Enhanced Visual Mode Behavior
- Toggle sets full-screen overlay with 60pt threads list titles, 72pt composer text area, and expanded spacing.
- CLI button hidden; `aria-hidden="true"` and removed from tab order.
- Print and Export buttons remain visible; labels remind "Large text applies to print preview" while export keeps 48pt control size.
- Toolbar shows banner "Enhanced Visual mode on." for 3 seconds (`aria-live`).
- Voice remains OFF by default; Voice toggle still available.

- **Print (Large Text)**: Uses `@media print` styles in `apps/webui/static/style.css` to output 60–72pt equivalents, hide toolbars/sidebars, and surface `.print-header` plus `.print-meta` badges (client, source, time). Invokes browser print dialog via `window.print()`.
- **Export PDF**: Generates a standard-print layout with local HTML template (no external assets). Document structure:
  - Header row: Thread title (bold), current timestamp, client/source badges.
  - Messages: Block per turn showing role, timestamp, and message text (48pt Standard, 60pt Enhanced). Code/text uses monospace fallback bundled locally.
  - Sources appendix: List of filenames + dates only.
- All icons delivered as bundled SVGs under `apps/webui/static/icons/` (48px minimum), referenced via relative paths to satisfy CSP requirements.

## Print & PDF Flows
- **Print (Large Text)**:
  - Button opens `/_print/{thread_id}` in a same-window modal view containing large-text HTML (no external assets, local fonts only).
  - Browser immediately receives `window.print()` call to launch the native print dialog; `aria-live` announces "Print preview opened."
  - When `@media print` is active, toolbars and nonessential chrome hide automatically; focus returns to Print button after dialog closes.
- **Export PDF**:
  - Button requests `/export/pdf/{thread_id}`; if local PDF engine is available, downloads PDF directly.
  - If the engine is unavailable, UI shows toast `role="alert"` "PDF engine missing. Use Print to PDF instead." and button remains enabled for retry after engine installation.
  - Completion toast `role="status"` announces "PDF saved locally." with focus moving to the downloads affordance.

## Accessibility Notes
- All interactive elements maintain ≥7:1 contrast.
- Use `role="status"` for ingest, hotswap, archive notifications; ensure they do not repeat PII.
- Sources panel shows filenames/dates only; no preview text.
- Ensure focus returns predictably after closing dialogs (e.g., to the button that opened them).
