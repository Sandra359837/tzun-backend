# main.py

import os
import json
import uuid
import requests
import random
import pathlib

from fastapi import FastAPI, Request
from pydantic import BaseModel
from openai import OpenAI

from title_bucketer import classify_title

app = FastAPI()

MATRIX = json.loads(pathlib.Path("stem_matrix.json").read_text())

# ——— OpenAI client ———
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# ——— Apps-Script webhook URL ———
WEBHOOK_URL = os.getenv("SHEETS_WEBHOOK_URL", "").strip()

# ─────────────────────────────────────────────────
# Request Schemas
# ─────────────────────────────────────────────────
class ResumeRequest(BaseModel):
    resume: str
    job_description: str

class AuditRequest(BaseModel):
    resume: str
    job_description: str
    tailored_resume: str

# ─────────────────────────────────────────────────
# 0) Health-check
# ─────────────────────────────────────────────────
@app.get("/")
async def root(request: Request):
    return {"status": "FastAPI is up ✅"}

# ─────────────────────────────────────────────────
# 1) Generate tailored resume
# ─────────────────────────────────────────────────
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

# ─────────────────────────────────────────────────
# 2) Basic audit of a tailored resume
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

Return a JSON object with these fields:
final_score, summary, factual_issues, alignment_issues, suggested_edits
"""
    resp = client.chat.completions.create(
        model="gpt-4",
        messages=[{"role": "user", "content": audit_prompt}],
        temperature=0.3
    )
    return {"audit": resp.choices[0].message.content}

# ─────────────────────────────────────────────────
# 3) Diagnostic evaluator + bucket classification + Sheets logging
# ─────────────────────────────────────────────────
@app.post("/diagnostic_evaluator")
def diagnostic_evaluator(data: AuditRequest):
    # 3.1 Generate a unique run_id
    run_id = str(uuid.uuid4())

    # 3.2 Build the diagnostic LLM prompt
    diagnostic_prompt = f"""
You are a resume compliance auditor and AI behavior evaluator.

Resume:
{data.resume}

Job description:
{data.job_description}

Tailored resume:
{data.tailored_resume}

Return *only* a JSON object **exactly** in this format:
{{
  "run_id": "{run_id}",
  "output_score": <integer 1–10>,
  "persona_context": <string>,
  "purpose": <string>,
  "status": <"✅ Passed" | "⚠️ Minor Edits" | "❌ Rework">,
  "tone_score_per_section": {{ "summary":<int>,"experience":<int>,"consistency_rating":<int> }},
  "bracketed_item_log": [<string>,…],
  "hallucination_score": <int>,
  "consistency_score": <int>,
  "flagged_issues": [<string>,…],
  "recommendations": [<string>,…]
}}
"""

    # 3.3 Call OpenAI
    resp = client.chat.completions.create(
        model="gpt-4",
        messages=[{"role": "user", "content": diagnostic_prompt}],
        temperature=0.3
    )
    content = resp.choices[0].message.content

    # 3.4 Parse the JSON the model returned
    result = json.loads(content)
    result["run_id"] = run_id  # ensure consistency

    # 3.5 Inject a memory-aware summary stem
    archetype = result.get("summary_archetype", "")
    stems     = MATRIX.get(archetype, [])
    if stems:
        result["summary_stem"] = random.choice(stems)

    # 3.6 Dynamically bucket the persona_context
    bucket, confidence = classify_title(result.get("persona_context", ""))
    result["bucket"]            = bucket
    result["bucket_confidence"] = confidence

    # 3.7 Fire off the row to Google Sheets via your Apps-Script webhook
    try:
        requests.post(
            WEBHOOK_URL,
            headers={"Content-Type": "application/json"},
            json=result
        )
    except Exception as webhook_err:
        print("⚠️ Webhook delivery failed:", webhook_err)

    # 3.8 Return the structured audit + bucket info
    return result
