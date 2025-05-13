import os
import sys
import json
import requests

print("🚀 nightly_runner starting…", file=sys.stderr)

# 1) Endpoint under test
BACKEND_URL = os.getenv(
    "BACKEND_URL",
    "https://tzun-backend.onrender.com/diagnostic_evaluator"
)
print("↗️ BACKEND_URL =", BACKEND_URL, file=sys.stderr)

# 2) Load your test cases
PAYLOAD_FILE = os.path.join(os.path.dirname(__file__), "tests", "nightly_payloads.json")
print("📂 Loading payloads from", PAYLOAD_FILE, file=sys.stderr)

def load_payloads():
    with open(PAYLOAD_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def run_all_tests():
    payloads = load_payloads()
    total = len(payloads)
    print(f"✅ Loaded {total} payload(s)", file=sys.stderr)

    exit_code = 0
    for i, payload in enumerate(payloads, start=1):
        print(f"➡️ Test [{i}/{total}] …", file=sys.stderr)
        try:
            resp = requests.post(
                BACKEND_URL,
                headers={"Content-Type": "application/json"},
                json=payload,
                timeout=60
            )
        except Exception as e:
            print(f"❌ Request error: {e}", file=sys.stderr)
            exit_code = 1
            continue

        status = resp.status_code
        body   = resp.text
        print(f"[{i}/{total}] {status}: {body}", file=sys.stderr)

        # failing non-200 responses
        if status != 200:
            exit_code = 1

    if exit_code != 0:
        print("❗ Some tests failed", file=sys.stderr)
    else:
        print("🎉 All tests passed", file=sys.stderr)
    sys.exit(exit_code)

if __name__ == "__main__":
    run_all_tests()
