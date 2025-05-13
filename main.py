import os
import json
import requests
from fastapi import FastAPI, Request
from pydantic import BaseModel
from openai import OpenAI

app = FastAPI()

# ─── Environment / Secrets ────────────────────────────────────────────────────
OPENAI_API_KEY   = os.getenv("OPENAI_API_KEY")
SHEETS_WEBHOOK_URL = os.getenv("SHEETS_WEBHOOK_URL")

client = OpenAI(api_key=OPENAI_API_KEY)

# ─── Request Schemas ──────────────────────────────────────────────────────────
class ResumeRequest(BaseModel):
    resume: str
    job_description: str

class AuditRequest(BaseModel):
    resume: str
    job_description: str
    tailored_resume: str

# ─── Health & Debug ────────────────────────────────────────────────────────────
@app.get("/")
async def root(request: Request):
    return {"status": "FastAPI is up ✅"}

@app.get("/debug_webhook_url")
def debug_webhook_url():
    return {
        "sheets_webhook_url": SHEETS_WEBHOOK_URL or "⚠️ Not set",
        "length": len(SHEETS_WEBHOOK_URL or "")
    }

# ─── 1) Generate Tailored Resume ──────────────────────────────────────────────
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
        messages=[{"role": "user", "content": prompt}],
        temperature=0.7
    )
    return {"resume": response.choices[0].message.content}

# ─── 2) Basic Audit Endpoint ───────────────────────────────────────────────────
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

Return a JSON object with keys:
final_score, summary, factual_issues, alignment_issues, suggested_edits
"""
    response = client.chat.completions.create(
        model="gpt-4",
        messages=[{"role": "user", "content": audit_prompt}],
        temperature=0.3
    )
    return {"audit": response.choices[0].message.content}

# ─── 3) Diagnostic Evaluator + Webhook Logging ─────────────────────────────────
@app.post("/diagnostic_evaluator")
def diagnostic_evaluator(data: AuditRequest):
    # 1) Build the diagnostic prompt
    diagnostic_prompt = f"""You are a resume compliance auditor and AI behavior evaluator.

Resume:
{data.resume}

Job description:
{data.job_description}

Tailored resume:
{data.tailored_resume}

Return a strict JSON object in this format:
{{
  "run_id": "GENERATE_A_UUID_OR_TIMESTAMP",
  "output_score": 0–10,
  "persona_context": "...",
  "purpose": "...",
  "status": "✅ Passed / ⚠️ Minor Edits / ❌ Rework",
  "tone_score_per_section": {{ /* summary, experience, consistency_rating */ }},
  "bracketed_item_log": [...],
  "hallucination_score": 0–10,
  "consistency_score": 0–100,
  "flagged_issues": [...],
  "recommendations": [...]
}}"""
    # 2) Ask GPT
    response = client.chat.completions.create(
        model="gpt-4",
        messages=[{"role": "user", "content": diagnostic_prompt}],
        temperature=0.3
    )
    content = response.choices[0].message.content

    # 3) Parse it
    result = json.loads(content)

    # 4) Fire the Apps Script webhook (if set)
    if SHEETS_WEBHOOK_URL:
        try:
            requests.post(
                SHEETS_WEBHOOK_URL,
                headers={"Content-Type": "application/json"},
                json=result
            )
        except Exception as webhook_err:
            print("⚠️ Webhook delivery failed:", webhook_err)

    # 5) Return the structured JSON to the caller
    return result
