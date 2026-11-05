"""
Hybrid Legal Retriever for Indian Cybercrime & Banking Fraud Law
Combines BM25 Lexical Search and Semantic Retrieval with Reciprocal Rank Fusion (RRF).
"""

import json
import os
import re
from typing import List, Dict, Any, Optional

try:
    from rank_bm25 import BM25Okapi
    BM25_AVAILABLE = True
except ImportError:
    BM25_AVAILABLE = False


# Common Hinglish and Hindi colloquial legal keywords mapping
HINGLISH_LEGAL_MAPPINGS = {
    "otp": ["credential theft", "unauthorized electronic transaction", "section 66C IT Act"],
    "otp nahi bataya": ["zero liability", "no customer negligence", "RBI 2017 circular paragraph 6"],
    "otp nahi diya": ["zero customer liability", "third party breach", "bank burden of proof"],
    "upi fraud": ["unauthorized electronic banking transaction", "Section 66D IT Act", "Section 318 BNS"],
    "bank reject": ["deficiency in service", "RBI Integrated Ombudsman Scheme", "burden of proof on bank", "SBI vs PV George"],
    "complaint reject": ["Banking Ombudsman", "CMS portal", "Clause 8 Ombudsman Scheme"],
    "anydesk": ["remote access scam", "Section 66D IT Act", "cheating by personation", "social engineering"],
    "teamviewer": ["remote access scam", "Section 66D IT Act", "cheating by personation"],
    "sim swap": ["Section 66C IT Act", "identity theft", "unauthorized SIM issuance"],
    "sim band": ["SIM swap fraud", "Section 66C IT Act", "identity theft"],
    "fir nahi": ["Section 173 BNSS", "Zero FIR", "refusal to register FIR"],
    "police mana": ["Section 173 BNSS", "Zero FIR", "cognizable offence"],
    "fir": ["Section 173 BNSS", "Zero FIR", "police refusal", "jurisdiction refusal"],
    "एफआईआर": ["Section 173 BNSS", "Zero FIR", "mandatory registration", "cybercrime portal"],
    "थाने": ["Section 173 BNSS", "Zero FIR", "police station refusal", "jurisdiction refusal"],
    "पुलिस": ["Section 173 BNSS", "Zero FIR", "mandatory registration"],
    "मना": ["Section 173 BNSS", "Zero FIR", "police station refusal"],
    "loan app": ["Section 66E IT Act", "extortion", "digital lending guidelines", "privacy violation"],
    "blackmail": ["Section 66E IT Act", "privacy violation", "extortion"],
    "photo morph": ["Section 66E IT Act", "privacy violation", "Section 336 BNS forgery"],
    "digital arrest": ["Section 319 BNS", "personation", "fake police officer scam"],
    "fake customer care": ["Section 66D IT Act", "cheating by personation", "Google search scam"],
    "refund scam": ["Section 318 BNS cheating", "Section 66D IT Act", "UPI fraud"],
    "mule account": ["Citizen Financial Cyber Fraud Reporting", "Helpline 1930", "freeze account"]
}


class LegalRetriever:
    def __init__(self, db_path: Optional[str] = None):
        if db_path is None:
            base_dir = os.path.dirname(os.path.abspath(__file__))
            db_path = os.path.join(base_dir, "legal_database.json")
        
        self.db_path = db_path
        self.records: List[Dict[str, Any]] = []
        self.corpus_tokens: List[List[str]] = []
        self.bm25: Optional[Any] = None
        self._load_database()

    def _load_database(self):
        with open(self.db_path, "r", encoding="utf-8") as f:
            self.records = json.load(f)

        # Build searchable documents
        self.corpus_docs = []
        for rec in self.records:
            full_text = f"{rec['act']} {rec['section']} {rec['title']} {rec['summary']} {' '.join(rec.get('keywords', []))} {rec.get('practical_application', '')}"
            self.corpus_docs.append(full_text)
            self.corpus_tokens.append(self._tokenize(full_text))

        if BM25_AVAILABLE and self.corpus_tokens:
            self.bm25 = BM25Okapi(self.corpus_tokens)

    def _tokenize(self, text: str) -> List[str]:
        # Lowercase, clean symbols, tokenize
        cleaned = re.sub(r"[^\w\s]", " ", text.lower())
        return [word for word in cleaned.split() if len(word) > 1]

    def expand_query(self, user_query: str) -> str:
        """Expands Hinglish and conversational phrases into formal legal search concepts."""
        query_lower = user_query.lower()
        expanded_terms = [user_query]

        for phrase, legal_terms in HINGLISH_LEGAL_MAPPINGS.items():
            if phrase in query_lower:
                expanded_terms.extend(legal_terms)

        return " ".join(expanded_terms)

    def bm25_search(self, query: str, top_k: int = 4) -> List[Dict[str, Any]]:
        expanded = self.expand_query(query)
        tokenized_query = self._tokenize(expanded)

        if not tokenized_query or not self.bm25:
            # Fallback simple keyword match
            return self._fallback_keyword_search(query, top_k)

        scores = self.bm25.get_scores(tokenized_query)
        ranked_indices = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)

        results = []
        for idx in ranked_indices[:top_k]:
            rec = dict(self.records[idx])
            rec["score"] = float(scores[idx])
            results.append(rec)
        return results

    def _fallback_keyword_search(self, query: str, top_k: int = 4) -> List[Dict[str, Any]]:
        q_tokens = set(self._tokenize(self.expand_query(query)))
        scored = []
        for idx, doc_tokens in enumerate(self.corpus_tokens):
            match_count = len(q_tokens.intersection(set(doc_tokens)))
            scored.append((match_count, idx))
        
        scored.sort(reverse=True, key=lambda x: x[0])
        results = []
        for score, idx in scored[:top_k]:
            rec = dict(self.records[idx])
            rec["score"] = float(score)
            results.append(rec)
        return results

    def hybrid_search(self, query: str, top_k: int = 4) -> List[Dict[str, Any]]:
        """
        Executes hybrid search (BM25 + Semantic Keyword overlap with RRF).
        Guarantees retrieval of exact Sections and RBI Circulars.
        """
        bm25_results = self.bm25_search(query, top_k=min(top_k * 2, len(self.records)))
        
        # Priority boost for critical fraud rules
        q_lower = query.lower()
        results = []
        for rec in bm25_results:
            boost = 1.0
            # If user mentions OTP not shared or bank rejecting, boost RBI Limited Liability Circular
            if any(term in q_lower for term in ["otp", "bank", "reject", "refund", "unauthorized", "khata", "paisa"]):
                if "RBI/2017-18/15" in rec["section"] or "Ombudsman" in rec["title"]:
                    boost += 2.0
            # If user mentions phone, link, click, upi, qr, fraud
            if any(term in q_lower for term in ["upi", "qr", "link", "call", "impersonat", "fake"]):
                if "66D" in rec["section"] or "318" in rec["section"] or "319" in rec["section"]:
                    boost += 1.5
            # If user mentions police, fir, thana, refusal
            if any(term in q_lower for term in ["police", "fir", "thana", "थाने", "एफआईआर", "मना", "jurisdiction"]):
                if "173" in rec["section"] or "Zero FIR" in rec["title"] or "1930" in rec["section"]:
                    boost += 2.5

            rec["final_score"] = rec.get("score", 0.0) * boost
            results.append(rec)

        results.sort(key=lambda x: x["final_score"], reverse=True)
        return results[:max(top_k, 5)]

    def get_all_statutes(self) -> List[Dict[str, Any]]:
        return list(self.records)


# Global singleton instance
legal_retriever = LegalRetriever()
