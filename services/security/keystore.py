# services/security/keystore.py
from __future__ import annotations
import os, json, time, base64, secrets, hashlib
from pathlib import Path
from dataclasses import dataclass

DATA_DIR = Path("Data")
KEYS_PATH = DATA_DIR / "keys.json"
AUTH_STATE_PATH = DATA_DIR / "auth_state.json"

@dataclass
class LockoutState:
    hard_lock: bool
    lockout_until: int  # epoch seconds; 0 if not in timed lock
    failed: int

def _b64(x: bytes) -> str: return base64.b64encode(x).decode("ascii")
def _b64d(x: str) -> bytes: return base64.b64decode(x.encode("ascii"))

def _scrypt_hash(secret: str, salt: bytes) -> bytes:
    # modest params for dev; can tune higher for production
    return hashlib.scrypt(secret.encode("utf-8"), salt=salt, n=2**14, r=8, p=1, dklen=32)

def _new_salt() -> bytes: return secrets.token_bytes(16)

def _load_json(p: Path, default):
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return default

def _save_json(p: Path, obj):
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(obj, indent=2), encoding="utf-8")

def _now() -> int: return int(time.time())

# ---------- Recovery phrase (dev-grade 12-word generator) ----------
_WORDS = ["able","about","above","access","account","act","adapt","add","adjust","advance","agent","agree","ahead",
"aim","align","alpha","amount","anchor","answer","apart","apple","apply","area","arrive","asset","audio","august",
"balance","basic","batch","begin","benefit","better","beyond","binary","bird","blue","board","bonus","book","boost",
"border","bound","brain","brand","brave","brief","bring","build","cable","calm","camera","capital","card","care",
"carry","case","cash","cause","center","chain","chair","chance","change","chart","check","choice","choose","civic",
"claim","clear","client","close","cloth","cloud","coach","code","coin","cold","color","come","common","craft","create",
"credit","crew","crisp","cross","crowd","cycle","daily","data","date","deal","dear","debt","decide","deep","deliver",
"demand","detail","develop","device","direct","document","dollar","duty","early","earth","easy","edge","edit","effect",
"eight","electric","elegant","element","elite","email","embed","emerge","emotion","empower","empty","enable","end",
"energy","engage","engine","enjoy","ensure","enter","entire","entry","equal","equip","escape","essay","estate","ethic",
"even","event","every","exact","example","excel","except","exchange","execute","exist","exit","expand","expect","expire",
"explain","explore","export","extend","extra","eye","face","fact","fair","faith","fall","fame","family","famous","far",
"farm","fast","fault","favor","feature","feed","feel","field","file","fill","film","final","find","fine","finish","first"]

def generate_recovery_phrase(n: int = 12) -> str:
    return " ".join(secrets.choice(_WORDS) for _ in range(n))

# ---------- Key/phrase storage ----------
def _new_key_record(pin: str):
    salt = _new_salt()
    phash = _scrypt_hash(pin, salt)
    r_salt = _new_salt()
    # first-boot phrase (printed to user)
    phrase = generate_recovery_phrase()
    r_hash = _scrypt_hash(phrase, r_salt)
    return {
        "version": 1,
        "pin": {"salt": _b64(salt), "hash": _b64(phash)},
        "recovery": {"salt": _b64(r_salt), "hash": _b64(r_hash)},
        "created_at": _now()
    }, phrase

def init_if_missing(default_pin: str = "123456") -> str | None:
    """Create keys on first run. Returns recovery phrase if newly created, else None."""
    if KEYS_PATH.exists():
        return None
    rec, phrase = _new_key_record(default_pin)
    _save_json(KEYS_PATH, rec)
    if not AUTH_STATE_PATH.exists():
        _save_json(AUTH_STATE_PATH, {"failed": 0, "lockout_until": 0, "hard_lock": False})
    return phrase

def _get_keys():
    return _load_json(KEYS_PATH, None)

def _get_state() -> LockoutState:
    st = _load_json(AUTH_STATE_PATH, {"failed": 0, "lockout_until": 0, "hard_lock": False})
    return LockoutState(bool(st.get("hard_lock", False)), int(st.get("lockout_until", 0)), int(st.get("failed", 0)))

def _put_state(s: LockoutState):
    _save_json(AUTH_STATE_PATH, {"failed": s.failed, "lockout_until": s.lockout_until, "hard_lock": s.hard_lock})

def check_lockout() -> LockoutState:
    s = _get_state()
    if s.hard_lock:
        return s
    if s.lockout_until and _now() < s.lockout_until:
        return s
    # clear timed lock if expired
    if s.lockout_until and _now() >= s.lockout_until:
        s.lockout_until = 0
        _put_state(s)
    return s

def record_failed_attempt():
    s = _get_state()
    s.failed += 1
    if s.failed >= 10:
        s.hard_lock = True
    elif s.failed >= 5 and s.lockout_until == 0:
        s.lockout_until = _now() + 15 * 60  # 15 min
    _put_state(s)

def clear_failures():
    s = _get_state()
    s.failed = 0
    s.lockout_until = 0
    s.hard_lock = False
    _put_state(s)

def verify_pin(pin: str) -> bool:
    rec = _get_keys()
    if not rec: return False
    salt = _b64d(rec["pin"]["salt"])
    h = _scrypt_hash(pin, salt)
    return _b64(h) == rec["pin"]["hash"]

def set_pin(new_pin: str) -> bool:
    if not (len(new_pin) == 6 and new_pin.isdigit()):
        return False
    rec = _get_keys()
    if not rec: return False
    salt = _new_salt()
    rec["pin"]["salt"] = _b64(salt)
    rec["pin"]["hash"] = _b64(_scrypt_hash(new_pin, salt))
    _save_json(KEYS_PATH, rec)
    clear_failures()
    return True

def verify_phrase(phrase: str) -> bool:
    rec = _get_keys()
    if not rec: return False
    r_salt = _b64d(rec["recovery"]["salt"])
    h = _scrypt_hash(phrase.strip().lower(), r_salt)
    return _b64(h) == rec["recovery"]["hash"]

def set_phrase(phrase: str) -> None:
    rec = _get_keys()
    if not rec: return
    r_salt = _new_salt()
    rec["recovery"]["salt"] = _b64(r_salt)
    rec["recovery"]["hash"] = _b64(_scrypt_hash(phrase.strip().lower(), r_salt))
    _save_json(KEYS_PATH, rec)
