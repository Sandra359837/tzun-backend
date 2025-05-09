
from fastapi import FastAPI
from pydantic import BaseModel
from openai import OpenAI
import os

app = FastAPI()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

class ResumeRequest(BaseModel):
    resume: str
    job_description: str

class AuditRequest(BaseModel):
    resume: str
    job_description: str
    tailored_resume: str

@app.post("/generate_resume")
def generate_resume(data: ResumeRequest):
    prompt = f"""You are a resume rewriter. Improve the following resume to match this job description:

Resume:
{data.resume}

Job Description:
{data.job_description}

Rewrite the resume accordingly:
"""
    response = client.chat.completions.create(
        model="gpt-4",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.7
    )
    return {"resume": response.choices[0].message.content}

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
4. Prompt rule violations

Give a score (1–10) and return:
{{
  "final_score": "✅ Pass",
  "summary": "...",
  "factual_issues": [...],
  "alignment_issues": [...],
  "suggested_edits": [...]
}}
"""
    response = client.chat.completions.create(
        model="gpt-4",
        messages=[{"role": "user", "content": audit_prompt}],
        temperature=0.3
    )
    return {"audit": response.choices[0].message.content}

@app.post("/diagnostic_evaluator")
def diagnostic_evaluator(data: AuditRequest):
    try:
        diagnostic_prompt = f"""You are a resume compliance auditor and AI behavior evaluator.

You will now review the resume output that was generated based on the original resume and the job description provided.

Resume:
{data.resume}

Job description:
{data.job_description}

Tailored resume:
{data.tailored_resume}

Your task is to analyze the tailored resume and return this JSON block:

{{
  "run_id": "test_eval_001",
  "output_score": 4,
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
}}
"""
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "user", "content": diagnostic_prompt}],
            temperature=0.3
        )

        return {
            "audit_result": response.choices[0].message.content
        }

    except Exception as e:
        return {"error": str(e)}
