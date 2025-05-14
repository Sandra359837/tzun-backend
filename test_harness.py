import os
import json
import requests

# 1️⃣ Load your endpoint URL from env-vars (set in Render or locally)
BACKEND_URL = os.getenv("BACKEND_URL", "https://tzun-backend.onrender.com/diagnostic_evaluator")

# 2️⃣ Define or load your test cases (you can also point to tests/nightly_payloads.json)
TEST_PAYLOADS = [
    {
      "resume": "Sales Manager with 5 years of experience leading outbound sales teams in B2B SaaS. Managed a $2M pipeline, exceeded quota by 130%.",
      "job_description": "We’re seeking a Customer Success Manager in B2B SaaS with onboarding, Salesforce, and cross-functional experience.",
      "tailored_resume": "Sales Manager with 5 years of B2B SaaS experience, recognized for leading high-performing teams. Managed a $2M pipeline and exceeded quota by 130%. Skilled in Salesforce, onboarding, and collaboration."
    },
    {
      "resume": "Senior Software Engineer with 12 years in fintech. Led microservices teams, scaled APIs to 10M users, and reduced latency by 40%. Expert in Python, Go, and AWS.",
      "job_description": "Hiring a Principal Backend Engineer to architect resilient microservices, optimize performance at scale, and mentor junior engineers. Must have 10+ years in distributed systems and cloud.",
      "tailored_resume": "Principal Backend Engineer with 12 years of fintech experience, driving 40% latency reduction across microservices and mentoring cross-functional teams."
    },
    # ← Add as many payloads here as you like
]

def run_tests():
    print(f"🚀 Running {len(TEST_PAYLOADS)} tests against {BACKEND_URL}\n")
    for i, payload in enumerate(TEST_PAYLOADS, start=1):
        resp = requests.post(
            BACKEND_URL,
            headers={"Content-Type": "application/json"},
            json=payload
        )
        status = resp.status_code
        body   = resp.text
        print(f"[{i}/{len(TEST_PAYLOADS)}] {status}\n{body}\n{'-'*60}\n")

if __name__ == "__main__":
    run_tests()
