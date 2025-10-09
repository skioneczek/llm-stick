# UI State Matrix (36pt headings)

| State | What user hears | What is on screen | Keyboard access |
| --- | --- | --- | --- |
| Launch (Voice Mode OFF) | Silent | High-contrast 6-digit PIN pad; large buttons; focus ring on first digit | Tab cycles digits; digits/Enter submit; Escape brings up Panic |
| Invalid PIN | Silent | PIN pad with 36pt error banner "PIN not recognized"; focus returns to first digit | Digits/Enter retry; Escape Panic |
| Security Self-Check | Silent | 36pt text "Running offline self-check…" then two-line audit result | Tab to Cancel (mapped to Panic); Enter confirms proceed |
| Home (Voice Mode OFF) | Silent | Large command menu (Stop, Repeat, Summarize, Sources, Panic, Set Data Folder) plus controls row (Presets, Font Size ±, Serif/Sans, Bold, Contrast); 36pt text ask box labelled "Type your question"; Voice toggle OFF with helper text "Voice Mode is off — type to ask" | Arrow/Tab navigate menu; Enter activates; Alt+V toggles Voice; Alt+Plus/Minus resize; Alt+S serif toggle; Alt+B bold toggle; Alt+C contrast; Enter submits ask |
| Reader Preset Applied | If Voice Mode ON: "High-contrast sans preset applied." / etc. | Toast appears with preset name and reminder "Use Alt+Plus/Minus to adjust size."; controls row highlights active preset | Alt+Plus/Minus resize; Alt+S serif toggle; Alt+B bold toggle; Alt+C contrast |
| Text Ask Submitted | Silent | Ask box clears; latest response card appears with Repeat button focused; Voice toggle remains OFF unless user changed it | Enter submits; Shift+Enter adds newline; R repeats |
| Set Data Folder (Picker Open) | If Voice Mode ON: "Pick the folder containing the client files." otherwise silent | Native folder picker with 36pt header and reminder "Scanning stays local and may take a few minutes." | Arrow keys navigate; Enter selects; Esc cancels |
| Set Data Folder (Confirm Panel) | Silent unless Voice Mode ON (then "Confirm data folder." ) | High-contrast panel showing chosen path; buttons Confirm / Cancel; helper "The app will scan this folder offline." | Tab cycles path → Confirm → Cancel; Enter activates; Esc cancels |
| Set Data Folder (Toast) | Silent unless Voice Mode ON ("Data folder set." ) | Toast "Data folder set to {path}. Scan may take time; all local." or "Data folder unchanged." | Dismisses after 3s; Esc dismisses immediately |
| Voice Mode Enabled | "Voice Mode enabled. Hold space to speak." | Toggle shows ON; Hold-to-Talk button with focus ring; menu remains | Spacebar = push-to-talk; Enter activates focused control |
| Voice Mode Disabled | "Voice Mode disabled. Use buttons or keyboard." | Toggle shows OFF with helper text "Voice Mode is off — type to ask"; Hold-to-Talk hidden; text ask box regains focus | Same as Home OFF state |
| Listening | `earcon_listening.wav` once | High-contrast waveform; 36pt caption "Listening… hold space"; Stop/Repeat/Summarize/Sources/Panic visible | Spacebar must stay held; releasing moves to Thinking; Esc Panic |
| Timeout Prompt (Listening) | Silent unless Voice Mode ON and follow-up requested | Caption "Still there?" with focus returning to Hold-to-Talk | Spacebar restarts capture; commands hotkeys active |
| Thinking | Looping `earcon_thinking.wav` | 36pt text "Thinking offline…"; animated focus outline; commands visible | Spacebar ignored until response ready; Stop cancels |
| Speaking | `earcon_speaking.wav` lead-in then response | High-contrast text of response; Scroll controls; Stop/Repeat/Summarize/Sources/Panic | Spacebar pauses speech; R repeats; S stops |
| Post-Response Prompt | If Voice Mode ON: "Hold space to ask more." otherwise silent | 36pt prompt "Hold space to ask more"; commands remain | Spacebar restarts Listening; menu hotkeys |
| Sources Requested | Voice Mode ON: spoken list only if user asked; otherwise silent | High-contrast source list; collapsible details hiding PII by default; banner "Filenames and dates shown." | Arrow keys expand/collapse; Enter select; Esc exits |
| Sources Toast | Silent unless Voice Mode ON ("Filenames and dates shown.") | Toast "Filenames and dates shown." appears at bottom while panel opens/closes | Auto-dismiss after 3s; Esc dismisses immediately |
| Sources Panel Close | Silent unless Voice Mode ON (then reads "Sources hidden.") | Panel slides closed; latest answer remains; helper text "Say or click Sources to open again" | Esc or Enter closes; S reopens |
| Panic Prompt | Silent until confirmed | Modal "Panic clears temporary data and exits" with note "Press Esc within 3 seconds to cancel."; buttons Cancel / Confirm; aria-describedby explains effect | Tab cycles buttons; Enter activates; Esc cancels |
| Panic Execution | Silent (no speech) | Screen fades to high-contrast banner "Panic in progress…"; progress indicator; app quits after data cleared | Keyboard locked except Esc to cancel within 3s grace |
| Security Slider Change (Standard→Hardened) | Silent | Confirmation banner "Security set to Hardened"; enforcement audit line | Tab/Enter acknowledge; Esc Panic |
| Security Slider Change (→ Paranoid) | "Paranoid mode on. Network must be off." | Banner requiring adapters off; refuse to continue until compliance | Tab cycles checklist; Enter re-run check; commands limited to Panic |
