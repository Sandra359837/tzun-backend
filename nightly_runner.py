import os
import sys
import json
import requests
from pathlib import Path

# ──────────────────────────────────────────────
# 1) Startup debug
# ──────────────────────────────────────────────
print("🚀 nightly_runner starting…", file=sys.stderr)

# ──────────────────────────────────────────────
# 2) Determine the path to nightly_payloads.json
# ──────────────────────────────────────────────
base_dir = Path(__file__).parent
payload_path = base_dir / "tests" / "nightly_payloads.json"
print(f"📂 Looking for payload file at: {payload_path}", file=sys.stderr)

if not payload_path.exists():
    print(f"❌ Payload file not found at {payload_path}", file=sys.stderr)
    sys.exit(1)

# ──────────────────────────────────────────────
# 3) Read & preview the file contents
# ──────────────────────────────────────────────
try:
    raw = payload_path.read_text(encoding="utf-8")
    preview = raw.replace("\n", " ")[:200]
    print(f"📄 Payload preview: {preview}…", file=sys.stderr)
except Exception as e:
    print("❌ Error reading payload file:", e, file=sys.stderr)
    sys.exit(1)

# ──────────────────────────────────────────────
# 4) Parse JSON
# ──────────────────────────────────────────────
try:
    payloads = json.loads(raw)
    print(f"✅ Successfully loaded {len(payloads)} payload(s)", file=sys.stderr)
except json.JSONDecodeError as e:
    print("❌ JSONDecodeError:", e, file=sys.stderr)
    sys.exit(1)

# ──────────────────────────────────────────────
# 5) Validate BACKEND_URL
# ──────────────────────────────────────────────
BACKEND_URL = os.getenv("BACKEND_URL")
if not BACKEND_URL:
    print("❌ BACKEND_URL env var not set", file=sys.stderr)
    sys.exit(1)
print(f"↗️ BACKEND_URL = {BACKEND_URL}", file=sys.stderr)

# ──────────────────────────────────────────────
# 6) Execute each test
# ──────────────────────────────────────────────
for idx, payload in enumerate(payloads, start=1):
    try:
        resp = requests.post(
            BACKEND_URL,
            headers={"Content-Type": "application/json"},
            json=payload
        )
        print(f"[{idx}/{len(payloads)}] {resp.status_code}: {resp.text}", file=sys.stderr)
    except Exception as e:
        print(f"❌ Request failed for payload #{idx}:", e, file=sys.stderr)
