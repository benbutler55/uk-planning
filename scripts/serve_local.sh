#!/usr/bin/env bash
set -euo pipefail

python3 scripts/build_site.py

choose_port() {
  python3 - "$@" <<'PY'
import socket
import sys

for p in [4173, 4174, 4175, 8000]:
    s = socket.socket()
    try:
        s.bind(("127.0.0.1", p))
        print(p)
        sys.exit(0)
    except OSError:
        pass
    finally:
        s.close()

print("No free port in candidate set", file=sys.stderr)
sys.exit(1)
PY
}

PORT="${PORT:-$(choose_port)}"
echo "Serving site at http://localhost:${PORT}"
python3 -m http.server "$PORT" --directory site
