import os
import json
import requests
import uuid
from fastapi import FastAPI, Request
from pydantic import BaseModel
from openai import OpenAI

# ─────────────────────────────────────────────────
# App & OpenAI client setup
# ─────────────────────────────────────────────────
app = FastAPI()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# ─────────────────────────────────────────────────
# Webhook URL for Google Apps Script
# ─────────────────────────────────────────────────
WEBHOOK_URL = os.getenv("SHEETS_WEBHOOK_URL")
if not WEBHOOK_URL:
    raise RuntimeError("❌ SHEETS_WEBHOOK_URL environment variable is not set!")

# ─────────────────────────────────────────────────
#  Health‐check & debug endpoints
# ─────────────────────────────────────────────────
@app.get("/")
async def root(request: Request):
    print("🌱 Received request at / from", request.client.host)
    return {"status": "FastAPI is up ✅"}

@app.get("/debug_webhook_url")
def debug_webhook_url():
    print("🔗 SHEETS_WEBHOOK_URL =", WEBHOOK_URL)
    return {
        "sheets_webhook_url": WEBHOOK_URL,
        "length": len(WEBHOOK_URL)
    }

# ─────────────────────────────────────────────────
#  Request schemas
# ─────────────────────────────────────────────────
class ResumeRequest(BaseModel):
    resume: str
    job_description: str

class AuditRequest(BaseModel):
    resume: str
    job_description: str
    tailored_resume: str

# ─────────────────────────────────────────────────
#  1) Generate tailored resume
# ─────────────────────────────────────────────────
@app.post("/generate_resume")
def generate_resume(data: ResumeRequest):
    prompt = f"""You are a resume rewriter. Improve the following resume to match this job description:

Resume:
{data.resume}

Job Description:
{data.job_description}

Rewrite the resume accordingly."""
    response = client.chat.completions.create(
        model="gpt-4",
        messages=[{"role":"user", "content":prompt}],
        temperature=0.7
    )
    return {"resume": response.choices[0].message.content}

# ─────────────────────────────────────────────────
#  2) Basic audit of a tailored resume
# ─────────────────────────────────────────────────
@app.post("/audit_resume_output")
def audit_resume_output(data: AuditRequest):
    audit_prompt = f"""You are a resume compliance auditor.

Original resume:
{data.resume}

Job description:
{data.job_description}

Tailored resume:
{data.tailored_resume}

Evaluate:
1. Factual correctness
2. Structural integrity
3. Alignment to the job
4. Prompt rule compliance

Return a JSON object:
{{
  "final_score": "✅ Pass",
  "summary": "...",
  "factual_issues": [...],
  "alignment_issues": [...],
  "suggested_edits": [...]
}}"""
    response = client.chat.completions.create(
        model="gpt-4",
        messages=[{"role":"user", "content":audit_prompt}],
        temperature=0.3
    )
    return {"audit": response.choices[0].message.content}

# ─────────────────────────────────────────────────
#  3) Diagnostic evaluator + Apps‐Script webhook logging
# ─────────────────────────────────────────────────
@app.post("/diagnostic_evaluator")
def diagnostic_evaluator(data: AuditRequest):
    # 1) Generate a unique run_id
    run_id = uuid.uuid4().hex

    try:
        # 2) Build your diagnostic prompt (no static run_id)
        diagnostic_prompt = f"""You are a resume compliance auditor and AI behavior evaluator.

Resume:
{data.resume}

Job description:
{data.job_description}

Tailored resume:
{data.tailored_resume}

Return a strict JSON object with these fields:
- output_score (integer)
- persona_context (string)
- purpose (string)
- status (string)
- tone_score_per_section (object)
- bracketed_item_log (array)
- hallucination_score (integer)
- consistency_score (integer)
- flagged_issues (array)
- recommendations (array)

Do NOT include any extra fields."""
        # 3) Call OpenAI
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[{"role":"user", "content":diagnostic_prompt}],
            temperature=0.3
        )
        content = response.choices[0].message.content

        # 4) Parse the JSON
        result = json.loads(content)

        # 5) Inject our unique run_id
        result["run_id"] = run_id

        # 6) Fire the webhook (Apps‐Script)
        try:
            requests.post(
                WEBHOOK_URL,
                headers={"Content-Type":"application/json"},
                json=result
            )
        except Exception as webhook_err:
            print("⚠️ Webhook delivery failed:", webhook_err)

        # 7) Return the augmented result
        return result

    except Exception as e:
        return {"error": str(e)}

