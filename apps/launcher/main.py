# apps/launcher/main.py
import sys, os, argparse
from pathlib import Path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from services.preflight.audit import audit_pin
from services.security.pin_gate import unlock_with_pin
from services.preflight.mode_state import set_mode, Mode, set_adapters_active, set_guards_ok
from services.preflight.host_alias import bind_host_path
from services.preflight.adapter_detect import adapters_active
from services.security import net_guard
from services.retriever.query import run as run_query

def boot(pin: str,
         target_mode: str,
         voice_enabled: bool,
         show_probe: bool,
         ask_query: str | None,
         index_path: str):

    # 1) PIN
    pin_ok = unlock_with_pin(pin)
    print(audit_pin(pin_ok).msg)
    if not pin_ok:
        return

    # 2) Detect adapters
    active = adapters_active()
    set_adapters_active(active)

    # 3) Apply guards by mode
    guards_ok = False
    mode = Mode(target_mode)
    if mode == Mode.STANDARD:
        guards_ok = net_guard.apply_standard_guards()
    elif mode == Mode.HARDENED:
        tmp_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "Data", "tmp"))
        guards_ok = net_guard.apply_hardened_guards(tmp_root)
    elif mode == Mode.PARANOID:
        guards_ok = True

    set_guards_ok(guards_ok)

    # 4) Mode audit
    print(set_mode(mode).msg)

    # 5) Host alias (policy: read-only)
    print(bind_host_path().msg)

    # 6) Voice audit
    from services.preflight.audit import audit_voice
    print(audit_voice(voice_enabled).msg)

    # 7) Optional inline probe
    if show_probe and mode in (Mode.STANDARD, Mode.HARDENED):
        dns_line, sock_line = net_guard.probe_text()
        print(dns_line)
        print(sock_line)

    # 8) Optional ask (post-audit Q&A against local index)
    if ask_query:
        idx = Path(index_path)  # <<< convert to Path
        try:
            run_query(ask_query, index_path=idx)
        except TypeError:
            # Back-compat if local function lacks index_path kw
            run_query(ask_query)

if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="LLM Stick launcher (offline, guarded)")
    ap.add_argument("--mode", default="standard", choices=["standard", "hardened", "paranoid"])
    ap.add_argument("--pin", default="123456")
    ap.add_argument("--voice", action="store_true", help="Enable Voice Mode")
    ap.add_argument("--probe", action="store_true", help="Inline DNS/socket probe after guards")
    ap.add_argument("--ask", default=None, help="Ask a question against the local index")
    ap.add_argument("--index", default="Data/index.json", help="Path to index.json (default: Data/index.json)")
    args = ap.parse_args()

    boot(
        pin=args.pin,
        target_mode=args.mode,
        voice_enabled=args.voice,
        show_probe=args.probe,
        ask_query=args.ask,
        index_path=args.index
    )
