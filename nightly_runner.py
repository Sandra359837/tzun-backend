#!/usr/bin/env python3
import os, json, requests, sys

print("🚀 nightly_runner starting…", file=sys.stderr)

BACKEND_URL = os.getenv(
    "BACKEND_URL",
    "https://tzun-backend-1.onrender.com/diagnostic_evaluator"
)
print(f"↗️ BACKEND_URL = {BACKEND_URL}", file=sys.stderr)

PAYLOAD_FILE = "tests/nightly_payloads.json"
print(f"📂 Loading payloads from {PAYLOAD_FILE}", file=sys.stderr)

def load_payloads():
    with open(PAYLOAD_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def run_all_tests():
    payloads = load_payloads()
    print(f"✅ Loaded {len(payloads)} payload(s)", file=sys.stderr)
    for i, payload in enumerate(payloads, start=1):
        resp = requests.post(
            BACKEND_URL,
            headers={"Content-Type": "application/json"},
            json=payload
        )
        print(f"[{i}/{len(payloads)}] {resp.status_code}: {resp.text}", file=sys.stderr)

if __name__ == "__main__":
    run_all_tests()
