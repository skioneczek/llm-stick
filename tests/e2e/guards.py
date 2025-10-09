# tests/e2e/guards.py
import socket
def try_dns():
    try:
        socket.getaddrinfo("example.com", 80)
        return "DNS: PASS (unexpected — should be blocked)"
    except Exception as e:
        return "DNS: BLOCKED (ok)"

def try_socket():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(0.5)
        s.connect(("1.1.1.1", 80))
        s.close()
        return "SOCKET: PASS (unexpected — should be blocked)"
    except Exception:
        return "SOCKET: BLOCKED (ok)"

if __name__ == "__main__":
    print(try_dns())
    print(try_socket())
