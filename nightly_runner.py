import os, json, requests, sys

print("🚀 nightly_runner starting…", file=sys.stderr)

# URL of your Render-hosted FastAPI endpoint
BACKEND_URL = os.getenv("BACKEND_URL", "https://tzun-backend.onrender.com/diagnostic_evaluator")

# Path to your test cases file
PAYLOAD_FILE = "tests/nightly_payloads.json"

def load_payloads():
    with open(PAYLOAD_FILE, "r") as f:
        return json.load(f)

def run_all_tests():
    payloads = load_payloads()
    for i, payload in enumerate(payloads, start=1):
        resp = requests.post(
            BACKEND_URL,
            headers={"Content-Type": "application/json"},
            json=payload
        )
        print(f"[{i}/{len(payloads)}] {resp.status_code}: {resp.text}")

if __name__ == "__main__":
    run_all_tests()
