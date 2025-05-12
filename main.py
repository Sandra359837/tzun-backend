import os, json, requests
from fastapi import FastAPI, Request
from pydantic import BaseModel
from openai import OpenAI

app = FastAPI()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
WEBHOOK_URL = os.getenv('https://script.google.com/macros/s/AKfycbx9B2TDWlrK_r1gf0XEHq6NHmAnO9VxZ72eV9o7ehSD-tJla9cgknLAd5Omn7Ps8dCi/exec')

# Root health-check (logs each hit)
@app.get("/")
async def root(request: Request):
    print("🌱 Received request at / from", request.client.host)
    return {"status": "FastAPI is up ✅"}

# Debug webhook URL (logs the value)
@app.get("/debug_webhook_url")
def debug_webhook_url():
    url = os.getenv("SHEETS_WEBHOOK_URL", "")
    print("🔗 SHEETS_WEBHOOK_URL =", url)
    return {"sheets_webhook_url": url or "⚠️ Not set", "length": len(url)}

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
# 3) Diagnostic evaluator + Apps-Script Webhook logging
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

        # Send to your Apps-Script webhook
        try:
            requests.post(
                WEBHOOK_URL,
                headers={"Content-Type": "application/json"},
                json=result
            )
        except Exception as webhook_err:
            print("⚠️ Webhook delivery failed:", webhook_err)

        # Return the structured audit object
        return result

    except Exception as e:
        return {"error": str(e)}

