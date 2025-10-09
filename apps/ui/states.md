# UI State Matrix (36pt headings)

| State | What user hears | What is on screen | Keyboard access |
| --- | --- | --- | --- |
| Launch (Voice Mode OFF) | Silent | High-contrast 6-digit PIN pad; large buttons; focus ring on first digit | Tab cycles digits; digits/Enter submit; Escape brings up Panic |
| Invalid PIN | Silent | PIN pad with 36pt error banner "PIN not recognized"; focus returns to first digit | Digits/Enter retry; Escape Panic |
| Security Self-Check | Silent | 36pt text "Running offline self-check…" then two-line audit result | Tab to Cancel (mapped to Panic); Enter confirms proceed |
| Home (Voice Mode OFF) | Silent | Large command menu (Stop, Repeat, Summarize, Sources, Panic); Voice toggle OFF | Arrow/Tab navigate menu; Enter activates; Alt+V toggles Voice |
| Voice Mode Enabled | "Voice Mode enabled. Hold space to speak." | Toggle shows ON; Hold-to-Talk button with focus ring; menu remains | Spacebar = push-to-talk; Enter activates focused control |
| Voice Mode Disabled | "Voice Mode disabled. Use buttons or keyboard." | Toggle shows OFF; Hold-to-Talk hidden; menu visible | Same as Home OFF state |
| Listening | `earcon_listening.wav` once | High-contrast waveform; 36pt caption "Listening… hold space"; Stop/Repeat/Summarize/Sources/Panic visible | Spacebar must stay held; releasing moves to Thinking; Esc Panic |
| Timeout Prompt (Listening) | Silent unless Voice Mode ON and follow-up requested | Caption "Still there?" with focus returning to Hold-to-Talk | Spacebar restarts capture; commands hotkeys active |
| Thinking | Looping `earcon_thinking.wav` | 36pt text "Thinking offline…"; animated focus outline; commands visible | Spacebar ignored until response ready; Stop cancels |
| Speaking | `earcon_speaking.wav` lead-in then response | High-contrast text of response; Scroll controls; Stop/Repeat/Summarize/Sources/Panic | Spacebar pauses speech; R repeats; S stops |
| Post-Response Prompt | If Voice Mode ON: "Hold space to ask more." otherwise silent | 36pt prompt "Hold space to ask more"; commands remain | Spacebar restarts Listening; menu hotkeys |
| Sources Requested | Voice Mode ON: spoken list only if user asked; otherwise silent | High-contrast source list; collapsible details hiding PII by default | Arrow keys expand/collapse; Enter select; Esc exits |
| Security Slider Change (Standard→Hardened) | Silent | Confirmation banner "Security set to Hardened"; enforcement audit line | Tab/Enter acknowledge; Esc Panic |
| Security Slider Change (→ Paranoid) | "Paranoid mode on. Network must be off." | Banner requiring adapters off; refuse to continue until compliance | Tab cycles checklist; Enter re-run check; commands limited to Panic |
