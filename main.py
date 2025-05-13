import os
import json
import uuid
import requests

from fastapi import FastAPI
from pydantic import BaseModel
from openai import OpenAI

app = FastAPI()

# ——— OpenAI client ———
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# ——— Apps-Script webhook URL ———
WEBHOOK_URL = os.getenv("SHEETS_WEBHOOK_URL", "").strip()

# ——— Pydantic Request Schemas ———
class ResumeRequest(BaseModel):
    resume: str
    job_description: str

class AuditRequest(BaseModel):
    resume: str
    job_description: str
    tailored_resume: str

# ——— 1) Root health-check ———
@app.get("/")
def root():
    return {"status": "FastAPI is up ✅"}

# ——— 2) Generate tailored resume ———
@app.post("/generate_resume")
def generate_resume(data: ResumeRequest):
    prompt = f"""You are a resume rewriter. Improve the following resume to match this job description:

Resume:
{data.resume}

Job Description:
{data.job_description}

Rewrite the resume accordingly."""
    resp = client.chat.completions.create(
        model="gpt-4",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.7
    )
    return {"resume": resp.choices[0].message.content}

# ——— 3) Basic audit of a tailored resume ———
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

Return a JSON object with fields:
final_score, summary, factual_issues, alignment_issues, suggested_edits
"""
    resp = client.chat.completions.create(
        model="gpt-4",
        messages=[{"role": "user", "content": audit_prompt}],
        temperature=0.3
    )
    return {"audit": resp.choices[0].message.content}

# ——— 4) Diagnostic evaluator + Sheets logging ———
@app.post("/diagnostic_evaluator")
def diagnostic_evaluator(data: AuditRequest):
    # 1) Unique run_id
    run_id = str(uuid.uuid4())

    # 2) Build the diagnostic LLM prompt
    diagnostic_prompt = f"""
You are a resume compliance auditor and AI behavior evaluator.

Resume:
{data.resume}

Job description:
{data.job_description}

Tailored resume:
{data.tailored_resume}

Return *only* a JSON object in this exact schema:
{{
  "run_id": "{run_id}",
  "output_score": <int 1–10>,
  "persona_context": <string>,
  "purpose": <string>,
  "status": <"✅ Passed"|"⚠️ Minor Edits"|"❌ Rework">,
  "tone_score_per_section": {{
    "summary":<int>,
    "experience":<int>,
    "consistency_rating":<int>
  }},
  "bracketed_item_log": [<string>,…],
  "hallucination_score": <int>,
  "consistency_score": <int>,
  "flagged_issues": [<string>,…],
  "recommendations": [<string>,…]
}}
"""

    # 3) Call OpenAI
    resp = client.chat.completions.create(
        model="gpt-4",
        messages=[{"role": "user", "content": diagnostic_prompt}],
        temperature=0.3
    )
    content = resp.choices[0].message.content

    # 4) Parse JSON
    result = json.loads(content)
    result["run_id"] = run_id  # ensure it

    # 5) Fire to Google Sheets via Apps-Script
    try:
        requests.post(
            WEBHOOK_URL,
            headers={"Content-Type": "application/json"},
            json=result
        )
    except Exception as e:
        print("⚠️ Webhook delivery failed:", e)

    # 6) Return the audit JSON
    return result
