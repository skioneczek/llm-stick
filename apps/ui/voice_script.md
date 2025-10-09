# Voice Interaction Script

## Launch (Voice Mode OFF)
- Screen: High-contrast 6-digit PIN pad; large keys, focus ring on first digit.
- Audio: Silent. Voice Mode toggle visibly set to OFF.
- Prompts: 32–48pt text instructing "Enter your 6-digit PIN" with helper copy "Voice Mode is optional and stays off until you turn it on." (aria-describedby for keypad instructions).

## PIN Entry
- User enters PIN via large on-screen buttons or keyboard digits.
- On submit, enforcement self-check runs and prints 1–2 line audit.
- If adapters are active and security slider is Paranoid, display refusal notice; no audio.

## Home Screen (Voice Mode OFF)
- Screen: Large-text command menu (Stop, Repeat, Summarize, Sources, Panic); prominent text ask box with 36pt label "Type your question" and placeholder "Press Enter to submit"; Voice Mode toggle OFF with helper text "Voice Mode is off — use the text box or commands.".
- Controls row: Presets, Font Size ±, Serif/Sans, Bold, Contrast, Voice toggle, Set Data Folder, Security slider, Sources, Panic. Each control 48pt label with aria-describedby for shortcut hints.
- Audio: Silent.
- User may enable Voice Mode via toggle (persisted setting) or submit text questions.
- Set Data Folder button appears alongside commands once unlocked.

## Voice Mode Availability Copy
- Banner copy (if user opens toggle info): "Voice Mode processes speech locally. Turn it on only when you want to talk."
- Screen reader note: aria-live "polite" message "Voice Mode is optional. All responses stay on this device." when toggle receives focus.

## Set Data Folder Flow
- Button label: "Set Data Folder" (48pt) with helper copy "Choose where the stick looks for files." (aria-describedby linked to note).
- On activation: Open folder picker dialog showing 36pt header "Pick the folder containing the client files." If Voice Mode ON, speak "Pick the folder containing the client files." once; otherwise remain silent.
- Reminder text in dialog: "Scanning stays local and may take a few minutes." (32pt; aria-describedby on Confirm).
- Confirmation sheet: show chosen path in high-contrast text with buttons "Confirm" and "Cancel"; helper line "The app will scan this folder offline.".
- Toast messaging: On Confirm, display "Data folder set to {path}. Scan may take time; all local." (aria-live polite). On Cancel, display "Data folder unchanged." for 3 seconds.

## Text Ask Box (Always Available)
- Location: Center column below command menu; 36pt label, 48pt input text, 60px high submit button labelled "Ask"; supports keyboard Enter and Shift+Enter for new line.
- Accessibility: ARIA label "Type your question"; focus ring 4px high contrast; screen reader hint "Voice Mode off by default. Type and press Enter to ask.".
- Feedback: After submit, field clears; last response summary appears below with "Repeat" command highlighted.

## Sources Control
- Button label: "Sources" (48pt) with aria-label "Show file names and dates".
- On activation: Show panel with 48pt heading "Sources" and collapsible entries; toast "Filenames and dates shown." appears at bottom (aria-live polite).
- When panel closes, prompt text "Say or click Sources to open again." remains visible. No PII unless user requests.

## Enabling Voice Mode
- Action: User toggles Voice Mode ON.
- Audio: "Voice Mode enabled. Hold space to speak." (one short confirmation line).
- Screen: Toggle text changes to "Voice Mode ON — hold space to talk"; Hold-to-Talk button appears with focus ring; commands and text ask box remain visible.
- Keys: Spacebar acts as push-to-talk while held.

## Listening State (Voice Mode ON)
- Trigger: User holds spacebar or presses on-screen Hold-to-Talk.
- Audio: Play `earcon_listening.wav` once at start, then stay silent until speech detected.
- Screen: High-contrast waveform indicator; caption "Listening… hold space" in 36pt.
- Timeout: If silence >5s, prompt "Still there?" in text only; no PII.

## Thinking State
- Trigger: User releases spacebar; system processes input offline.
- Audio: Loop `earcon_thinking.wav` softly until response ready.
- Screen: Large text "Thinking offline…" with animated focus outline.

## Speaking State
- Trigger: Response ready and Voice Mode ON.
- Audio: `earcon_speaking.wav` (brief lead-in) then synthesized speech.
- Screen: High-contrast text of response; provide Scroll + Stop button.
- Sensitive content: Only speak/show PII when user explicitly requested Sources.

## Follow-Up Prompting
- After speaking, display 36pt text "Hold space to ask more".
- Audio: If Voice Mode ON, say "Hold space to ask more." otherwise remain silent.
- Commands Stop/Repeat/Summarize/Sources/Panic remain on screen and keyboard accessible.

## Disabling Voice Mode
- Action: User toggles Voice Mode OFF.
- Audio: "Voice Mode disabled. Use buttons or keyboard." (short confirmation).
- Screen: Hold-to-Talk control hides; toggle shows OFF with helper text "Voice Mode is off — type to ask"; text ask box regains focus.

## Voice Mode Error Lines (no PII)
- "We didn’t hear anything. Try again with the spacebar held." (listening timeout)
- "Microphone not found. Use the text box or check your device." (hardware missing)
- "Voice Mode paused while security check runs. Type your question instead." (guards reapplying)
- All error lines surface as 36pt banners with aria-live "assertive" and no spoken output unless Voice Mode remains ON.

## Panic Flow Copy
- Panic button prompt: "Panic clears temporary data and exits." with note "Press Esc within 3 seconds to cancel." (both 36pt, aria-describedby link).
- During execution: Banner "Panic in progress… clearing local data." (no auto speech unless Voice Mode ON). After completion, app shuts down.

## Layout Wire (Text Description)
- Title bar: Left shows app name + security mode; right shows clock and network status icons (no color reliance, high-contrast text).
- Main content: Large answer area centered with 60pt body text adjusted by preset controls; scrollable with 4px focus outline.
- Controls row (below answer): Presets | Font Size ± | Serif/Sans | Bold | Contrast | Voice toggle | Set Data Folder | Security slider | Sources | Panic. Buttons 48pt labels, spaced for large targets.
- Footer: Audit strip showing latest enforcement message in 36pt text.

## Earcon Specifications
- Listening: `earcon_listening.wav` – 400 Hz sine chirp rising 200 ms, played once; <60 dB.
- Thinking: `earcon_thinking.wav` – soft 200 Hz pulsing bed, 500 ms loop, unobtrusive.
- Speaking: `earcon_speaking.wav` – single 600 Hz chime 150 ms preceding speech output.

## Enforcement Phrases
- Voice toggle ON: "Voice Mode enabled. Hold space to speak."
- Voice toggle OFF: "Voice Mode disabled. Use buttons or keyboard."
- Security slider Paranoid: "Paranoid mode on. Network must be off."
