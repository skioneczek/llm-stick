# services/voice/stt_stub.py

def listen() -> str:
    """Listen using a stub (reads from stdin)"""
    try:
        return input("YOU> ").strip()
    except EOFError:
        return ""
