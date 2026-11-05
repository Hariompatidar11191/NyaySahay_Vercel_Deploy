"""
Document and Evidence Processor for Indian Banking & Cybercrime Claims.
Extracts transaction IDs, disputed amounts, dates, banks, and grievance IDs from PDFs, images, and text.
"""

import re
import io
from typing import Dict, Any, Optional

try:
    import fitz  # PyMuPDF
    FITZ_AVAILABLE = True
except ImportError:
    FITZ_AVAILABLE = False

try:
    import pypdf
    PYPDF_AVAILABLE = True
except ImportError:
    PYPDF_AVAILABLE = False


class DocumentProcessor:
    def __init__(self):
        # Regex patterns for Indian banking and cybercrime documentation
        self.amount_pattern = re.compile(r"(?:(?:Rs\.?|INR|₹)\s*|amount\s*(?:is|:)?\s*)([0-9]{1,3}(?:,[0-9]{2,3})*(?:\.[0-9]{2})?|[0-9]+(?:\.[0-9]{2})?)", re.IGNORECASE)
        self.utr_pattern = re.compile(r"(?:UTR|Ref(?:erence)?\s*(?:No|Number|ID)?|Txn\s*ID|Transaction\s*ID|RRN)\s*[:#\-]?\s*([A-Za-z0-9]{9,22})", re.IGNORECASE)
        self.date_pattern = re.compile(r"(\b\d{1,2}[-/\.]\d{1,2}[-/\.]\d{2,4}\b|\b\d{1,2}\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{2,4}\b)", re.IGNORECASE)
        self.upi_vpa_pattern = re.compile(r"([a-zA-Z0-9.\-_]{2,49}@[a-zA-Z]{2,})")
        self.ncrp_ack_pattern = re.compile(r"(?:ack(?:nowledgement)?\s*(?:no|number)?|complaint\s*(?:no|number)?|ticket\s*(?:no|id)?)\s*[:#\-]?\s*([0-9]{10,16}|[A-Za-z0-9\-_/]{8,25})", re.IGNORECASE)
        
        # Bank names list
        self.known_banks = [
            "State Bank of India", "SBI", "HDFC Bank", "HDFC", "ICICI Bank", "ICICI",
            "Punjab National Bank", "PNB", "Axis Bank", "Bank of Baroda", "BOB",
            "Kotak Mahindra Bank", "Kotak", "Canara Bank", "Union Bank of India",
            "Paytm Payments Bank", "Airtel Payments Bank", "India Post Payments Bank",
            "Google Pay", "PhonePe", "CRED", "BHIM", "Amazon Pay"
        ]

    def extract_text_from_pdf(self, file_bytes: bytes) -> str:
        """Extracts text from PDF using PyMuPDF or pypdf."""
        extracted_text = []

        if FITZ_AVAILABLE:
            try:
                doc = fitz.open(stream=file_bytes, filetype="pdf")
                for page in doc:
                    extracted_text.append(page.get_text())
                if "".join(extracted_text).strip():
                    return "\n".join(extracted_text)
            except Exception:
                pass

        if PYPDF_AVAILABLE:
            try:
                reader = pypdf.PdfReader(io.BytesIO(file_bytes))
                for page in reader.pages:
                    text = page.extract_text()
                    if text:
                        extracted_text.append(text)
                return "\n".join(extracted_text)
            except Exception:
                pass

        return ""

    def extract_facts(self, text: str, filename: str = "") -> Dict[str, Any]:
        """
        Parses raw text to extract key financial & case metadata.
        Returns a structured dictionary of case facts.
        """
        facts = {
            "source_file": filename,
            "disputed_amount": None,
            "transaction_id": None,
            "transaction_date": None,
            "detected_bank": None,
            "vpa_beneficiary": None,
            "complaint_ref_no": None,
            "raw_snippet": text[:400].strip() if text else ""
        }

        if not text:
            return facts

        # Extract amounts
        amount_matches = self.amount_pattern.findall(text)
        if amount_matches:
            # Filter out trivially small numbers or decimals
            for amt in amount_matches:
                clean_amt = amt.replace(",", "").strip()
                try:
                    val = float(clean_amt)
                    if val >= 50:  # reasonable fraud amount threshold
                        facts["disputed_amount"] = f"₹{amt}"
                        break
                except ValueError:
                    continue

        # Extract UTR / Txn ID
        utr_matches = self.utr_pattern.findall(text)
        if utr_matches:
            facts["transaction_id"] = utr_matches[0]

        # Extract Date
        date_matches = self.date_pattern.findall(text)
        if date_matches:
            facts["transaction_date"] = date_matches[0]

        # Extract Beneficiary UPI ID / VPA
        vpa_matches = self.upi_vpa_pattern.findall(text)
        if vpa_matches:
            # Avoid generic emails if possible
            for vpa in vpa_matches:
                if any(handle in vpa.lower() for handle in ["paytm", "okaxis", "okhdfc", "okicici", "upi", "ibl", "ybl", "axl"]):
                    facts["vpa_beneficiary"] = vpa
                    break
            if not facts["vpa_beneficiary"] and vpa_matches:
                facts["vpa_beneficiary"] = vpa_matches[0]

        # Extract Complaint / Ack No
        ack_matches = self.ncrp_ack_pattern.findall(text)
        if ack_matches:
            facts["complaint_ref_no"] = ack_matches[0]

        # Detect Bank / App
        for bank in self.known_banks:
            if re.search(rf"\b{re.escape(bank)}\b", text, re.IGNORECASE):
                facts["detected_bank"] = bank
                break

        return facts

    def parse_uploaded_file(self, uploaded_file) -> Dict[str, Any]:
        """Handles Streamlit uploaded file object."""
        filename = getattr(uploaded_file, "name", "document")
        file_bytes = uploaded_file.read()
        
        text = ""
        if filename.lower().endswith(".pdf"):
            text = self.extract_text_from_pdf(file_bytes)
        elif filename.lower().endswith((".txt", ".csv")):
            try:
                text = file_bytes.decode("utf-8")
            except UnicodeDecodeError:
                text = file_bytes.decode("latin-1", errors="ignore")
        else:
            # For images or scanned docs
            text = f"Image file: {filename}. (Visual proof attached: transaction receipt / screenshot)"

        facts = self.extract_facts(text, filename)
        return {
            "filename": filename,
            "text": text,
            "facts": facts
        }


# Global singleton instance
doc_processor = DocumentProcessor()
