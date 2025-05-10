import os, json, requests
from fastapi import FastAPI
from pydantic import BaseModel
from openai import OpenAI

app = FastAPI()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
WEBHOOK_URL = os.getenv("SHEETS_WEBHOOK_URL")

class ResumeRequest(BaseModel):
    resume: str
    job_description: str

class AuditRequest(BaseModel):
    resume: str
    job_description: str
    tailored_resume: str

@app.post("/generate_resume")
def generate_resume(data: ResumeRequest):
    prompt = f"""You are a resume rewriter. Improve the following resume...

Resume:
{data.resume}

Job Description:
{data.job_description}
"""
    r = client.chat.completions.create(
      model="gpt-4",
      messages=[{"role":"user","content":prompt}],
      temperature=0.7
    )
    return {"resume": r.choices[0].message.content}

@app.post("/audit_resume_output")
def audit_resume_output(data: AuditRequest):
    prompt = f"""You are an auditor...
Original resume:
{data.resume}
Job Description:
{data.job_description}
Tailored:
{data.tailored_resume}
Return JSON…"""
    r = client.chat.completions.create(
      model="gpt-4",
      messages=[{"role":"user","content":prompt}],
      temperature=0.3
    )
    return {"audit": r.choices[0].message.content}

@app.post("/diagnostic_evaluator")
def diagnostic_evaluator(data: AuditRequest):
    # 1) call OpenAI
    prompt = f"""You are an evaluator...
Resume:
{data.resume}
Job Description:
{data.job_description}
Tailored:
{data.tailored_resume}
Return strict JSON…"""
    r = client.chat.completions.create(
      model="gpt-4",
      messages=[{"role":"user","content":prompt}],
      temperature=0.3
    )
    result = json.loads(r.choices[0].message.content)
    # 2) fire to Apps Script
    try:
        requests.post(
          WEBHOOK_URL,
          headers={"Content-Type":"application/json"},
          json=result
        )
    except Exception as e:
        print("Webhook failed:", e)
    return result
