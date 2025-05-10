import os
import json
from fastapi import FastAPI
from pydantic import BaseModel
from openai import OpenAI
import gspread
from google.oauth2.service_account import Credentials

# ─────────────────────────────────────────────────
# App & OpenAI client
# ─────────────────────────────────────────────────
app = FastAPI()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# ─────────────────────────────────────────────────
# Google Sheets logging setup
# ─────────────────────────────────────────────────
SCOPES     = ["https://www.googleapis.com/auth/spreadsheets"]
CREDS_PATH = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")   # ex: "secrets/tzun_sheets_creds.json"
SHEET_URL  = os.getenv("QA_LOG_SHEET_URL")                # ex: your sheet URL

creds = Credentials.from_service_account_file(CREDS_PATH, scopes=SCOPES)
gc    = gspread.authorize(creds)
sheet = gc.open_by_url(SHEET_URL).worksheet("benchmark_test_cases")

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
    response = client.chat.completions.create(
        model="gpt-4",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.7
    )
    return {"resume": response.choices[0].message.content}

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
        messages=[{"role": "user", "content": audit_prompt}],
        temperature=0.3
    )
    return {"audit": response.choices[0].message.content}

# ─────────────────────────────────────────────────
# 3) Diagnostic evaluator + real-time Sheets logging
# ─────────────────────────────────────────────────
@app.post("/diagnostic_evaluator")
def diagnostic_evaluator(data: AuditRequest):
    try:
        # Build the diagnostic prompt
        diagnostic_prompt = f"""You are a resume compliance auditor and AI behavior evaluator.

Resume:
{data.resume}

Job description:
{data.job_description}

Tailored resume:
{data.tailored_resume}

Return a strict JSON object in this format:
{{
  "run_id": "test_eval_001",
  "output_score": 4,
  "persona_context": "mid-level B2B SaaS sales professional",
  "purpose": "Validate tone & hallucination controls",
  "status": "✅ Passed",
  "tone_score_per_section": {{
    "summary": "bold",
    "experience": "neutral",
    "consistency_rating": 82
  }},
  "bracketed_item_log": [],
  "hallucination_score": 1,
  "consistency_score": 82,
  "flagged_issues": [],
  "recommendations": []
}}"""
        # Call OpenAI
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "user", "content": diagnostic_prompt}],
            temperature=0.3
        )
        content = response.choices[0].message.content

        # Parse the JSON string
        result = json.loads(content)

        # Append a row to Google Sheets
        sheet.append_row([
            result.get("run_id", ""),
            result.get("output_score", ""),
            result.get("persona_context", ""),
            result.get("purpose", ""),
            result.get("status", ""),
            content.replace("\n", " ")[:500]  # first 500 chars of raw JSON
        ])

        # Return the parsed audit object
        return result

    except Exception as e:
        return {"error": str(e)}
