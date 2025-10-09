# apps/launcher/main.py
import sys, os, argparse
from pathlib import Path

# Make package imports work when launched as a module
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from services.preflight.mode_state import set_mode, Mode, set_adapters_active, set_guards_ok
from services.preflight.host_alias import bind_host_path
from services.preflight.adapter_detect import adapters_active
from services.security import net_guard
from services.retriever.query import run as run_query
from services.security.pin_gate import (
    unlock_with_pin, change_pin, reset_with_recovery, first_boot_phrase_if_any
)
from services.preflight.audit import audit_voice  # reuse the existing voice audit line


def boot(args):
    # 1) PIN unlock (uses persisted keystore + lockouts)
    pin_res = unlock_with_pin(args.pin)
    print(pin_res.message)
    if not pin_res.ok:
        return

    # 2) Detect adapters and apply guards for the selected mode
    active = adapters_active()
    set_adapters_active(active)

    guards_ok = False
    mode = Mode(args.mode)
    if mode == Mode.STANDARD:
        guards_ok = net_guard.apply_standard_guards()
    elif mode == Mode.HARDENED:
        tmp_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "Data", "tmp"))
        guards_ok = net_guard.apply_hardened_guards(tmp_root)
    elif mode == Mode.PARANOID:
        # In Paranoid we rely on adapters being OFF; we don't patch sockets here.
        guards_ok = True
    set_guards_ok(guards_ok)

    # 3) Mode audit (prints the 1–2 line message and commits mode if ok)
    print(set_mode(mode).msg)

    # 4) Host alias (policy: read-only)
    print(bind_host_path().msg)

    # 5) Voice audit line (toggle state only; actual TTS/STT is stubbed elsewhere)
    print(audit_voice(args.voice).msg)

    # 6) Optional inline probe (only meaningful in Standard/Hardened)
    if args.probe and mode in (Mode.STANDARD, Mode.HARDENED):
        dns_line, sock_line = net_guard.probe_text()
        print(dns_line)
        print(sock_line)

    # 7) Optional Q&A against the local index (post-audit, inside guarded process)
    if args.ask:
        idx = Path(args.index)
        run_query(args.ask, index_path=idx)

def main():
    ap = argparse.ArgumentParser(description="LLM Stick launcher (offline, guarded)")
    ap.add_argument("--mode", default="standard", choices=["standard", "hardened", "paranoid"])
    ap.add_argument("--pin", default="123456", help="6-digit PIN")
    ap.add_argument("--voice", action="store_true", help="Enable Voice Mode")
    ap.add_argument("--probe", action="store_true", help="Inline DNS/socket probe after guards")
    ap.add_argument("--ask", default=None, help="Ask a question against the local index")
    ap.add_argument("--index", default="Data/index.json", help="Path to index.json (default: Data/index.json)")

    # PIN lifecycle ops
    ap.add_argument("--change-pin", nargs=2, metavar=("CURRENT","NEW"), help="Change PIN (6 digits)")
    ap.add_argument("--reset-pin", nargs=2, metavar=("PHRASE","NEW"), help="Reset PIN using recovery phrase")
    ap.add_argument("--show-first-boot-phrase", action="store_true",
                    help="Print the generated recovery phrase if keys were just created")

    args = ap.parse_args()

    # First-boot key init (prints phrase only if keys were just created AND flag is set)
    phrase = first_boot_phrase_if_any()
    if args.show_first_boot_phrase:
        if phrase:
            print("\n*** WRITE THIS DOWN (store offline) ***")
            print(phrase)
            print("*** DO NOT LOSE THIS PHRASE ***\n")
        else:
            print("Recovery phrase already set (not shown). Keep your printed copy secure.")

    # Handle PIN change/reset commands and exit
    if args.change_pin:
        cur, new = args.change_pin
        res = change_pin(cur, new)
        print(res.message)
        return
    if args.reset_pin:
        phr, new = args.reset_pin
        res = reset_with_recovery(phr, new)
        print(res.message)
        return

    # Normal guarded boot
    boot(args)

if __name__ == "__main__":
    main()
