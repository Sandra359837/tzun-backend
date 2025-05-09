
from fastapi import FastAPI, Request
from pydantic import BaseModel
import openai
import os

app = FastAPI()

openai.api_key = os.getenv("OPENAI_API_KEY")

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
    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.7
    )
    return {"resume": response.choices[0].message["content"]}

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
    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[{"role": "user", "content": audit_prompt}],
        temperature=0.3
    )
    return {"audit": response.choices[0].message["content"]}

@app.post("/diagnostic_evaluator")
def diagnostic_evaluator(data: AuditRequest):
    diagnostic_prompt = f"""You are a resume compliance auditor and AI behavior evaluator.

You will now review the resume output that was generated based on the original resume and the job description provided.

Your task is to analyze the tailored resume and identify any of the following issues:

---

### 1. Factual Inconsistency
- Did the output fabricate any degrees, companies, roles, or dates?
- Were metrics (like % growth or quota attainment) invented without being flagged as placeholders?
- Were any original roles renamed, combined, or omitted?

→ If YES, list each occurrence.

---

### 2. Structural Integrity
- Did the revised resume preserve all jobs, dates, and employers in the original order?
- Were sections like “Summary,” “Experience,” and “Skills” kept logically organized?
- Was the resume reframed but not rewritten as a different version of the candidate’s life?

→ If NO, describe where structure drifted or became misleading.

---

### 3. Alignment with Job Description
- Does the output integrate specific keywords and themes from the job post?
- Was the tone appropriately matched (e.g., strategic, technical, collaborative)?
- Were the most relevant roles emphasized (through bullet ordering or phrasing)?

→ If NO, explain what the resume failed to reflect about the job.

---

### 4. Prompt Compliance
- Did the AI follow instructions like: “Do not fabricate,” “Insert placeholder if data is missing,” “Match tone,” and “Use only provided job description”?

→ If NO, identify which rule(s) were violated and how.

---

### 5. Final Scorecard
Summarize your evaluation using this scale:

- ✅ Pass – Ready for user delivery
- ⚠️ Minor Edits Needed – Factual or tone issues to fix
- ❌ Rework Required – Structure, accuracy, or alignment failures

Return your evaluation in this JSON format:

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
    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[{"role": "user", "content": diagnostic_prompt}],
        temperature=0.3
    )

    return {
        "audit_result": response.choices[0].message["content"]
    }
