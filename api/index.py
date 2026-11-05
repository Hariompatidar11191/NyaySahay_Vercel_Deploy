import io
import os
import sys
from pathlib import Path
from typing import Optional, List, Dict, Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from core.legal_engine import legal_engine
from core.doc_processor import doc_processor
from core.legal_drafter import legal_drafter
from legal_kb.retriever import legal_retriever

app = FastAPI(title="NyaySahay Legal Assistant API", version="1.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ChatRequest(BaseModel):
    message: str
    history: List[Dict[str, str]] = []
    case_facts: Dict[str, Any] = {}
    language: str = "auto"
    provider: str = "local"
    api_key: Optional[str] = None

class DraftRequest(BaseModel):
    kind: str
    customer_name: str = ""
    account_number: str = ""
    bank_name: str = ""
    disputed_amount: str = ""
    transaction_id: str = ""
    transaction_date: str = ""
    complaint_ticket_no: str = ""
    victim_phone: str = ""
    suspect_details: str = ""

@app.get("/api/health")
def health():
    return {"status": "ok", "knowledge_chunks": len(legal_retriever.get_all_statutes())}

@app.post("/api/chat")
def chat(req: ChatRequest):
    if not req.message.strip():
        raise HTTPException(status_code=400, detail="Message cannot be empty.")
    if req.provider not in {"local", "openai", "groq", "gemini"}:
        raise HTTPException(status_code=400, detail="Unsupported AI provider.")
    if req.provider != "local":
        if not req.api_key:
            raise HTTPException(status_code=400, detail="An API key is required for the selected provider.")
        legal_engine.configure_provider(req.provider, req.api_key)
    else:
        legal_engine.configure_provider("local", "")
    return legal_engine.generate_response(
        user_message=req.message,
        conversation_history=req.history[-8:],
        case_facts=req.case_facts,
        language=req.language,
    )

@app.post("/api/extract")
async def extract(file: UploadFile = File(...)):
    raw = await file.read()
    class Uploaded(io.BytesIO):
        def __init__(self, content, name):
            super().__init__(content)
            self.name = name
    parsed = doc_processor.parse_uploaded_file(Uploaded(raw, file.filename or "evidence"))
    return {"filename": parsed["filename"], "facts": parsed["facts"], "text_preview": parsed["text"][:1500]}

@app.post("/api/draft")
def draft(req: DraftRequest):
    if req.kind == "bank":
        text = legal_drafter.generate_bank_grievance_notice(
            customer_name=req.customer_name, account_number=req.account_number,
            bank_name=req.bank_name, disputed_amount=req.disputed_amount,
            transaction_id=req.transaction_id, transaction_date=req.transaction_date,
            incident_narrative="Unauthorized electronic transfer occurred from my account. Please investigate and apply applicable RBI customer-liability rules.",
            notified_within_3_days=True)
    elif req.kind == "cyber":
        text = legal_drafter.generate_cybercrime_complaint(
            victim_name=req.customer_name, victim_phone=req.victim_phone,
            disputed_amount=req.disputed_amount, transaction_id=req.transaction_id,
            transaction_date=req.transaction_date, suspect_details=req.suspect_details,
            incident_narrative="Online financial fraud / unauthorized electronic transaction.")
    elif req.kind == "ombudsman":
        text = legal_drafter.generate_ombudsman_petition(
            customer_name=req.customer_name, bank_name=req.bank_name,
            account_number=req.account_number, complaint_ticket_no=req.complaint_ticket_no,
            rejection_date="", disputed_amount=req.disputed_amount,
            summary_of_rejection="The bank has not resolved the disputed unauthorized transaction to my satisfaction.")
    else:
        raise HTTPException(status_code=400, detail="kind must be bank, cyber, or ombudsman")
    return {"draft": text}

@app.get("/api/statutes")
def statutes():
    return {"items": legal_retriever.get_all_statutes()}
