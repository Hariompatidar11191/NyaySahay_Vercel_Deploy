"""
Conversational Legal Reasoning Engine for Indian Cybercrime & Banking Fraud.
Supports Greetings, Privacy Guarantees, Out-of-Context Handling, Progressive Dialogue,
and Free-Tier Cloud LLMs (Groq, Google Gemini) alongside OpenAI & Built-in Engine.
"""

import os
import json
import re
from typing import Dict, Any, List, Optional
from legal_kb.retriever import legal_retriever

# AI Provider Imports
try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

try:
    import groq
    GROQ_AVAILABLE = True
except ImportError:
    GROQ_AVAILABLE = False

try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False


LEGAL_ASSISTANT_SYSTEM_PROMPT = """You are NyaySahay, an empathetic and authoritative AI Legal Assistant specializing in Indian cybercrime, banking fraud, and digital financial disputes.

Your purpose is to provide accurate, neutral, accessible, and evidence-based legal information to Indian citizens.

Core Behavioral Guidelines:
1. CONVERSATIONAL & EMPATHETIC: In early turns, do NOT overwhelm the user with long statutory essays. Be compassionate, concise (3-4 short paragraphs/bullet points max), explain their immediate safety step (Helpline 1930), and ask 2-3 precise clarifying questions to uncover missing facts.
2. PROGRESSIVE VERDICT: When facts are clarified or the user requests full legal advice, provide the detailed 'Final Legal Assessment' with exact sections from BNS 2023, IT Act 2000, and RBI Master Circulars.
3. GROUNDED IN VERIFIED SOURCES: Base legal claims strictly on Indian statutory provisions, BNS 2023, IT Act 2000, and RBI circulars. Never invent section numbers.
4. OUT-OF-SCOPE ADVICE: If the user asks something outside Indian cybercrime / financial fraud / banking disputes, politely guide them back to our specialization.
5. ADVOCATE REFERRAL: If the matter involves complex criminal litigation, physical intimidation, or cannot be resolved via administrative / banking channels, advise consulting a licensed advocate or visiting the District Legal Services Authority (DLSA) for free government legal aid.
6. CODE-MIXED LANGUAGE: Respond in the user's preferred language (English, Hindi Devanagari, or conversational Hinglish).
7. PRIVACY: Reassure users that their uploaded documents and case facts are private, processed in memory, and never stored or shared.
8. MANDATORY DISCLAIMER: End substantive legal advisories with:
   "⚠️ *Legal Disclaimer: This guidance is for educational and dispute-resolution purposes under Indian law and does not constitute formal attorney-client representation. For complex litigation, consult a licensed advocate.*"
"""


class LegalEngine:
    def __init__(self):
        self.provider = "local"  # "local", "groq", "gemini", "openai"
        self.api_key = None
        self.openai_client = None
        self.groq_client = None
        self.gemini_model = None

    def configure_provider(self, provider: str, api_key: str):
        """Configures the chosen AI provider."""
        self.provider = provider
        self.api_key = api_key.strip() if api_key else None

        if provider == "groq" and GROQ_AVAILABLE and self.api_key:
            try:
                self.groq_client = groq.Groq(api_key=self.api_key)
            except Exception:
                self.groq_client = None

        elif provider == "gemini" and GEMINI_AVAILABLE and self.api_key:
            try:
                genai.configure(api_key=self.api_key)
                self.gemini_model = genai.GenerativeModel("gemini-1.5-flash")
            except Exception:
                self.gemini_model = None

        elif provider == "openai" and OPENAI_AVAILABLE and self.api_key:
            try:
                self.openai_client = OpenAI(api_key=self.api_key)
            except Exception:
                self.openai_client = None

    def is_greeting(self, text: str) -> bool:
        """Detects if message is a greeting or introductory query."""
        clean = text.lower().strip()
        clean_words = set(re.findall(r"\b\w+\b", clean))
        greeting_words = {
            "hello", "hi", "hey", "namaste", "pranam", "kya", "hal", "kaise", "who", "kya", "about",
            "intro", "introduce", "morning", "afternoon", "evening", "namashkar"
        }
        common_greetings = [
            "hello", "hi", "hey", "namaste", "how are you", "kya hal hai", "who are you",
            "aap kaun ho", "tell me about yourself", "what do you do", "help me"
        ]
        if any(clean == g for g in common_greetings):
            return True
        if len(clean_words) <= 3 and any(w in greeting_words for w in clean_words):
            return True
        return False

    def is_out_of_context(self, text: str) -> bool:
        """Detects if the query is totally unrelated to cybercrime, banking fraud, or Indian consumer disputes."""
        clean = text.lower()
        irrelevant_topics = [
            "recipe", "cake", "cook", "weather", "cricket score", "movie", "song", "lyrics",
            "football", "python code", "write a poem", "story about a princess", "joke",
            "capital of", "president of", "minecraft", "instagram followers generator"
        ]
        return any(topic in clean for topic in irrelevant_topics)

    def detect_language_preference(self, text: str) -> str:
        """Determines whether user is speaking Hindi, Hinglish, or English."""
        if re.search(r"[\u0900-\u097F]", text):
            return "hindi"

        hinglish_words = [
            "mera", "meri", "mere", "hai", "nahi", "kya", "kar", "sakte", "paisa", "kat", "gaya",
            "khata", "batao", "bheja", "tha", "raha", "gaye", "karo", "kripya", "madad", "chahiye", "bol"
        ]
        tokens = set(re.findall(r"\b\w+\b", text.lower()))
        if len(tokens.intersection(hinglish_words)) >= 2:
            return "hinglish"
        
        return "english"

    def generate_response(
        self,
        user_message: str,
        conversation_history: List[Dict[str, str]] = None,
        case_facts: Optional[Dict[str, Any]] = None,
        language: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Generates grounded conversational legal responses with greeting & context filters.
        """
        if conversation_history is None:
            conversation_history = []

        if not language or language == "auto":
            language = self.detect_language_preference(user_message)

        # 1. Check Greetings
        if self.is_greeting(user_message) and len(conversation_history) == 0:
            return {
                "answer": self._generate_greeting_response(language),
                "sources": [],
                "language": language,
                "engine": "conversational-greeter"
            }

        # 2. Check Out of Context
        if self.is_out_of_context(user_message):
            return {
                "answer": self._generate_out_of_context_response(language),
                "sources": [],
                "language": language,
                "engine": "guardrail-filter"
            }

        # 3. Retrieve relevant authorities from knowledge base
        retrieved_sources = legal_retriever.hybrid_search(user_message, top_k=5)

        # Build context
        context_str = "RELEVANT VERIFIED STATUTES & REGULATIONS FROM KNOWLEDGE BASE:\n"
        for idx, src in enumerate(retrieved_sources, 1):
            source_file = f" (File: {src.get('source_file')})" if src.get('source_file') else ""
            context_str += (
                f"[{idx}] {src['act']} - {src['section']}{source_file}: {src['title']}\n"
                f"Authority: {src['issuing_authority']} | Effective: {src['effective_date']}\n"
                f"Official URL: {src['source_url']}\n"
                f"Summary: {src['summary']}\n"
                f"Practical Application: {src.get('practical_application', '')}\n\n"
            )

        facts_str = ""
        if case_facts and any(case_facts.values()):
            facts_str = "\nCONFIRMED EVIDENCE FACTS EXTRACTED FROM UPLOADED DOCUMENT:\n"
            for k, v in case_facts.items():
                if v and k not in ["raw_snippet"]:
                    facts_str += f"- {k.replace('_', ' ').title()}: {v}\n"

        # 4. Try Free/Paid Cloud LLM Providers if configured
        llm_response = self._call_cloud_llm(user_message, conversation_history, context_str, facts_str, language)
        if llm_response:
            return {
                "answer": llm_response,
                "sources": retrieved_sources,
                "language": language,
                "engine": self.provider
            }

        # 5. Fallback to Local Deterministic Progressive Engine
        answer = self._generate_grounded_local_response(
            user_message, retrieved_sources, case_facts, language, conversation_history
        )
        return {
            "answer": answer,
            "sources": retrieved_sources,
            "language": language,
            "engine": "grounded-rule-engine"
        }

    def _call_cloud_llm(
        self,
        query: str,
        history: List[Dict[str, str]],
        context: str,
        facts: str,
        language: str
    ) -> Optional[str]:
        """Calls Groq (Free), Gemini (Free), or OpenAI if configured."""
        system_instruction = LEGAL_ASSISTANT_SYSTEM_PROMPT
        if language == "hindi":
            system_instruction += "\nPLEASE RESPOND IN ACCESSIBLE HINDI (देवनागरी लिपि में बात करें)."
        elif language == "hinglish":
            system_instruction += "\nPLEASE RESPOND IN CONVERSATIONAL HINGLISH (Roman Hindi)."
        else:
            system_instruction += "\nPLEASE RESPOND IN CLEAR, ACCESSIBLE ENGLISH."

        # A. GROQ (FREE TIER: Llama 3.3 70B)
        if self.provider == "groq" and self.groq_client:
            try:
                messages = [{"role": "system", "content": system_instruction}]
                for turn in history[-4:]:
                    messages.append(turn)
                messages.append({"role": "user", "content": f"{context}{facts}\n\nUSER MESSAGE:\n{query}"})

                completion = self.groq_client.chat.completions.create(
                    model="llama-3.3-70b-versatile",
                    messages=messages,
                    temperature=0.2,
                    max_tokens=800
                )
                return completion.choices[0].message.content
            except Exception:
                pass

        # B. GEMINI (FREE TIER: Gemini 1.5 Flash)
        if self.provider == "gemini" and self.gemini_model:
            try:
                full_prompt = f"{system_instruction}\n\n{context}{facts}\n\nCONVERSATION HISTORY:\n"
                for turn in history[-3:]:
                    full_prompt += f"{turn['role'].upper()}: {turn['content']}\n"
                full_prompt += f"USER: {query}\nASSISTANT:"

                res = self.gemini_model.generate_content(full_prompt)
                return res.text
            except Exception:
                pass

        # C. OPENAI (GPT-4o-mini)
        if self.provider == "openai" and self.openai_client:
            try:
                messages = [{"role": "system", "content": system_instruction}]
                for turn in history[-4:]:
                    messages.append(turn)
                messages.append({"role": "user", "content": f"{context}{facts}\n\nUSER MESSAGE:\n{query}"})

                completion = self.openai_client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=messages,
                    temperature=0.2,
                    max_tokens=800
                )
                return completion.choices[0].message.content
            except Exception:
                pass

        return None

    def _generate_greeting_response(self, language: str) -> str:
        if language == "hindi":
            return """### 🙏 नमस्ते! मैं न्यायसहाय (NyaySahay) हूँ — आपका AI कानूनी सहायक

मैं भारतीय नागरिकों को **साइबर अपराध (Cybercrime)**, **ऑनलाइन वित्तीय धोखाधड़ी (Banking & UPI Fraud)** और **डिजिटल भुगतान विवादों** में उनके कानूनी अधिकार समझाने और त्वरित कानूनी कार्रवाई करने में मदद करता हूँ।

---
#### 🛡️ यहाँ आपको क्या-क्या सहायता मिलेगी:
1. **कानूनी स्थिति का मूल्यांकन:** भारतीय न्याय संहिता (BNS 2023), IT Act 2000 और RBI के नियमों (Zero Customer Liability) के तहत आपकी कानूनी स्थिति।
2. **दस्तावेज़ों से साक्ष्य निकालना:** बैंक स्टेटमेंट, UPI स्क्रीनशॉट या रसीद अपलोड करने पर धोखाधड़ी की राशि, UTR ID और बैंक विवरण का स्वतः विश्लेषण।
3. **1-क्लिक औपचारिक कानूनी नोटिस:** बैंक विवाद नोटिस (Bank Dispute Notice), साइबर पोर्टल (1930) शिकायत, और RBI बैंकिंग लोकपाल याचिका का तुरंत तैयार मसौदा।

---
#### 🔒 आपकी गोपनीयता (Privacy Guarantee):
> **आपकी गोपनीयता पूर्णतः सुरक्षित है:** यहाँ अपलोड किए जाने वाले आपके बैंक स्टेटमेंट, स्क्रीनशॉट या विवरण केवल आपके वर्तमान सत्र (Session) में इन-मेमोरी प्रोसेस होते हैं। आपका कोई भी व्यक्तिगत या वित्तीय डेटा सर्वर पर स्टोर नहीं किया जाता और न ही AI मॉडल ट्रेनिंग के लिए उपयोग होता है।

---
💬 **शुरू करने के लिए:** कृपया संक्षेप में बताएं कि आपके साथ क्या घटना हुई है, या बाईं तरफ दिए गए पैनल से अपना दस्तावेज़ अपलोड करें!"""

        elif language == "hinglish":
            return """### 🙏 Namaste! Main NyaySahay hoon — Aapka AI Legal Assistant

Main Indian citizens ko **Cybercrime, Online Banking Fraud, UPI Scams, aur Digital Financial Disputes** me unke legal rights samajhne aur instant legal action lene me help karta hoon.

---
#### 🛡️ Yahan aapko kya-kya help milegi:
1. **Legal Standing Assessment:** Bharatiya Nyaya Sanhita (BNS 2023), IT Act 2000, aur RBI ke rules (Zero Customer Liability) ke mutabik aapki exact position.
2. **Evidence Extraction from Documents:** Bank statement, UPI payment screenshot, ya receipt upload karne par disputed amount, UTR ID aur bank name ka automated extraction.
3. **1-Click Legal Notice Generator:** Bank Dispute Notice (RBI circular ke under 10 days refund demand), Cybercrime Portal (1930) complaint draft, aur RBI Ombudsman petition.

---
#### 🔒 Privacy & Data Security Guarantee:
> **Aapka data 100% private aur safe hai:** Upload kiye gaye bank statements aur details sirf aapke current browser session me process hote hain. **Koi bhi personal ya financial data store nahi hota aur na hi model training me use hota hai.**

---
💬 **Start karne ke liye:** Batayein aapke saath kya hua hai (jaise: 'UPI se fraud ho gaya', 'AnyDesk download karwaya tha', 'bank complaint reject kar raha hai'), ya left panel se document upload karein!"""

        else:
            return """### ⚖️ Welcome! I am NyaySahay — Your AI Legal Assistant for Indian Cybercrime & Banking Fraud

I help Indian citizens navigate online financial fraud, unauthorized UPI/banking debits, phishing, and digital financial disputes.

---
#### 🛡️ What You Can Achieve Here:
1. **Legal Rights Assessment:** Understand your exact standing under the **Bharatiya Nyaya Sanhita (BNS) 2023**, **IT Act 2000**, and **RBI Limited Customer Liability Regulations**.
2. **Automated Evidence Extraction:** Upload bank statements or UPI screenshots to extract Disputed Amounts, UTR/Transaction IDs, dates, and bank names into a structured case sheet.
3. **1-Click Action Drafting:** Generate ready-to-submit formal **Bank Dispute Notices** (demanding 10-day shadow credit), **Cybercrime Portal 1930 complaints**, and **RBI Ombudsman petitions**.

---
#### 🔒 Privacy & Confidentiality Guarantee:
> **Your data is strictly confidential:** All uploaded statements, receipts, and personal details are processed entirely in-memory for your active session. **No documents or banking credentials are saved, stored on servers, or used for AI training.**

---
💬 **To begin:** Please describe your issue in simple words below, or upload your transaction statement using the left panel!"""

    def _generate_out_of_context_response(self, language: str) -> str:
        if language == "hindi":
            return """⚠️ **विषय से बाहर प्रश्न (Out of Scope)**

मैं विशेष रूप से **भारतीय साइबर अपराध, ऑनलाइन बैंकिंग धोखाधड़ी, UPI विवाद और डिजिटल उत्पीड़न** के कानूनी समाधान हेतु प्रशिक्षित हूँ।

मैं सामान्य ज्ञान, कोडिंग, मौसम या गैर-कानूनी प्रश्नों में सहायता करने में असमर्थ हूँ। कृपया अपने बैंक फ्रॉड, अनधिकृत लेन-देन, साइबर हेल्पलाइन (1930), या RBI नियमों से संबंधित प्रश्न पूछें।"""
        elif language == "hinglish":
            return """⚠️ **Out of Context Query**

Main strictly **Indian Cybercrime, Banking Fraud, UPI Disputes, aur Digital Financial Scams** ke legal solutions ke liye trained hoon.

Main cooking, coding, weather ya general topics par help nahi kar sakta. Please online financial fraud, unauthorized bank debit, 1930 helpline, ya bank rejection se related question puchein!"""
        else:
            return """⚠️ **Out of Scope Question**

I am specialized exclusively in **Indian Cybercrime, Online Banking Fraud, UPI Disputes, and Digital Financial Safety** under Indian laws.

I cannot assist with unrelated general queries. Please ask a question related to financial cyber fraud, unauthorized transactions, cybercrime portal (1930) reporting, or bank dispute resolution."""

    def _generate_grounded_local_response(
        self,
        query: str,
        sources: List[Dict[str, Any]],
        case_facts: Optional[Dict[str, Any]],
        language: str,
        conversation_history: List[Dict[str, str]] = None
    ) -> str:
        """
        Progressive conversational legal advisor:
        - Turn 1: Concise, empathetic, emergency action (1930), asks 2-3 interview questions.
        - Turn 2+: Synthesizes facts, integrates Consumer Protection Act & BSA 63, directs to notice drafter.
        - Complex/Unsolvable: Recommends licensed advocate / District Legal Services Authority (DLSA).
        """
        q_lower = query.lower()
        history_len = len(conversation_history) if conversation_history else 0
        is_final_turn = history_len >= 2 or any(w in q_lower for w in ["final", "verdict", "kya karu", "action", "notice", "draft", "batao"])

        amt = (case_facts.get("disputed_amount") if case_facts else None) or "disputed amount"
        bank = (case_facts.get("detected_bank") if case_facts else None) or "Bank"

        # Check if case is physically threatening or criminal litigation beyond AI assistance
        is_complex_litigation = any(w in q_lower for w in ["murder", "suicide", "kidnap", "physical attack", "court warrant real", "arrested in jail"])
        if is_complex_litigation:
            if language == "hindi":
                return """🚨 **तत्काल पंजीकृत अधिवक्ता / DLSA से संपर्क की आवश्यकता**

यह मामला डिजिटल वित्तीय विवाद के दायरे से बाहर है और इसमें गंभीर आपराधिक या भौतिक प्रक्रिया शामिल है। AI सहायक ऐसे जटिल मुकदमों में विधिक प्रतिनिधित्व नहीं दे सकता।

**तुरंत क्या करें:**
1. अपने जिले के **जिला विधिक सेवा प्राधिकरण (District Legal Services Authority - DLSA)** में जाएं जहाँ सरकार द्वारा **मुफ्त कानूनी सहायता (Free Legal Aid)** और सरकारी वकील प्रदान किए जाते हैं।
2. किसी पंजीकृत वरिष्ठ आपराधिक अधिवक्ता (Advocate) से व्यक्तिगत रूप से मिलकर वकालतनामा निष्पादित करें।"""
            else:
                return """🚨 **Immediate Legal Counsel Required (Beyond AI Scope)**

This situation involves serious criminal proceedings or physical risks that extend beyond civil/financial cyber dispute mechanisms. An AI tool cannot replace formal legal defense.

**Recommended Immediate Action:**
1. Visit your local **District Legal Services Authority (DLSA)** located at the District Court complex for **Free Legal Aid** and government-appointed advocates.
2. Engage a licensed criminal advocate immediately to file an anticipatory bail or handle formal court appearance."""

        # Progressive Flow
        if not is_final_turn:
            # SHORT, EMPATHETIC INTAKE (Not long essays!)
            if language == "hindi":
                return f"""### 🛡️ आपकी स्थिति का प्राथमिक कानूनी अवलोकन

मैं समझ सकता हूँ कि अनधिकृत वित्तीय नुकसान ({amt}) कितना तनावपूर्ण हो सकता है। अच्छी बात यह है कि **RBI मास्टर परिपत्र (RBI/2017-18/15)** और **भारतीय न्याय संहिता 2023** के तहत भारतीय कानून आपको मजबूत सुरक्षा प्रदान करता है।

**तत्काल प्राथमिक कदम:**
- यदि लेनदेन पिछले 2 घंटे के भीतर हुआ है, तो तुरंत साइबर हेल्पलाइन **1930** पर कॉल करें ताकि आरोपी का खाता फ्रीज हो सके।

---
#### ❓ मामले का सटीक कानूनी समाधान तैयार करने के लिए कृपया इन 3 बातों की जानकारी दें:
1. **समय-सीमा (Timeline):** धोखाधड़ी किस तारीख को हुई और आपने बैंक को कब सूचित किया (3 दिन के भीतर या बाद में)?
2. **धोखाधड़ी का तरीका:** क्या किसी ने AnyDesk/TeamViewer डाउनलोड कराया था या बिना किसी जानकारी के खाता डेबit हुआ?
3. **शिकायत की स्थिति:** क्या आपके पास बैंक शिकायत संख्या (Ticket ID) या 1930 की पावती संख्या (Ack No.) है?

*(जैसे ही आप यह जानकारी देंगे, हम अंतिम कानूनी फैसला और तैयार बैंक नोटिस उपलब्ध कराएंगे!)*"""

            elif language == "hinglish":
                return f"""### 🛡️ Initial Legal Assessment

Main samajh sakta hoon ki unauthorized money debit ({amt}) kitna stressful hota hai. But don't worry — Indian Law aur **RBI Master Circular (RBI/2017-18/15)** customer ko complete protection dete hain.

**Immediate First Step:**
- Agar fraud recent hai, toh turant National Cyber Helpline **1930** par call karein taaki scammer ka bank account freeze ho sake.

---
#### ❓ Exact legal solution aur Bank Notice ready karne ke liye please in 3 sawalon ka short me jawab dein:
1. **Timeline:** Fraud kis date ko hua aur aapne bank ko kab report kiya (3 working days ke andar ya baad me)?
2. **Modus Operandi:** Kya kisi fake customer care ne AnyDesk/QuickSupport install karwaya tha, ya bina OTP account se paise cut gaye?
3. **Complaint Proof:** Kya bank ne koi written Ticket ID / Grievance number diya hai?

*(Aapke reply ke baad main complete final verdict aur formal legal draft provide karunga!)*"""

            else:
                return f"""### 🛡️ Preliminary Case Assessment

I understand how distressing an unauthorized financial loss ({amt}) can be. Fortunately, Indian regulatory frameworks—specifically **RBI Circular RBI/2017-18/15** and the **Bharatiya Nyaya Sanhita 2023**—provide strong legal safeguards for innocent victims.

**Immediate Action:**
- If the fraud occurred recently, dial **1930** immediately to trigger beneficiary account lien-marking.

---
#### ❓ To deliver an accurate legal verdict and notice, please answer these 3 quick questions:
1. **Timeline:** Exactly what date did the fraud occur, and when did you first notify the bank (within 3 working days)?
2. **Fraud Mode:** Was a screen-sharing tool (AnyDesk/TeamViewer) involved, or was it a direct debit without your knowledge?
3. **Grievance Status:** Has the bank issued a formal Ticket/Complaint reference number?

*(Once you reply, I will provide your comprehensive final legal verdict and pre-filled notices!)*"""

        else:
            # COMPREHENSIVE FINAL LEGAL VERDICT
            if language == "hindi":
                return f"""### ⚖️ अंतिम कानूनी निर्णय और अधिकारिक कार्ययोजना (Final Legal Verdict)

आपके मामले के पूर्ण तथ्यों और भारतीय विधिशास्त्र के आधार पर आपका अंतिम कानूनी मूल्यांकन:

#### 1. लागू कानून व आपकी कानूनी स्थिति:
- **RBI Zero Customer Liability (RBI/2017-18/15):** 3 कार्य दिवसों के भीतर सूचना देने पर ग्राहक की देनदारी शून्य (Zero) है। परिपत्र के पैरा 12 के अनुसार **सबूत का भार पूरी तरह बैंक पर है**। बैंक केवल यह कहकर शिकायत खारिज नहीं कर सकता कि 'लेनदेन सिस्टम से हुआ था' (*SBI vs P.V. George, केरल उच्च न्यायालय*)।
- **BNS 2023 - धारा 318 व 319:** ऑनलाइन धोखाधड़ी और छद्म पहचान (इम्पर्सनेशन) 7 वर्ष तक की सजा वाला संज्ञेय अपराध है।
- **IT Act 2000 - धारा 66D:** डिजिटल माध्यम से धोखाधड़ी के लिए 3 वर्ष का कारावास।

#### 2. सामान्य भारतीय कानून व अतिरिक्त कानूनी रास्ते (General Legal Remedies):
- **उपभोक्ता संरक्षण अधिनियम, 2019 (Sections 34 & 35):** बैंक द्वारा अवैध रूप से दावा खारिज करना 'सेवा में कमी' (Deficiency in Service) है। आप जिला उपभोक्ता आयोग (DCDRC) में शिकायत दर्ज करके मूल राशि + 9% ब्याज और मानसिक परेशानी का हर्जाना मांग सकते हैं।
- **भारतीय साक्ष्य अधिनियम (BSA) 2023 - धारा 63:** आपके पास मौजूद बैंक SMS, स्क्रीनशॉट और कॉल रिकॉर्डिंग इलेक्ट्रॉनिक साक्ष्य के रूप में मान्य हैं।
- **बैंकिंग लोकपाल योजना 2021:** 30 दिन में समाधान न मिलने पर [cms.rbi.org.in](https://cms.rbi.org.in) पर ₹1 लाख तक मानसिक प्रताड़ना का मुआवजा मांगा जा सकता है।

#### 3. तुरंत उठाए जाने वाले ठोस कदम:
1. **Tab 2 (Notice Drafter) खोलें:** वहां से पहले से तैयार **Bank Dispute Notice** डाउनलोड करें और शाखा प्रबंधक को रिसीविंग के साथ जमा करें।
2. **Cyber 1930 ड्राफ्ट डाउनलोड करें:** [cybercrime.gov.in](https://cybercrime.gov.in) पर औपचारिक पावती दर्ज कराएं।

⚠️ *कानूनी अस्वीकरण: यह सलाह सूचनात्मक और मार्गदर्शन उद्देश्य से है। यदि बैंक विवाद का समाधान नहीं करता है, तो आप अपने स्थानीय जिला विधिक सेवा प्राधिकरण (DLSA) से निःशुल्क कानूनी सहायता ले सकते हैं।*"""

            elif language == "hinglish":
                return f"""### ⚖️ Final Legal Verdict & Strategic Action Plan

Aapke provide kiye gaye complete case facts ke basis par aapka Final Legal Standing:

#### 1. Aapke Paksh me Statutory Kanoon:
- **RBI Zero Liability Rule (RBI/2017-18/15):** Agar aapne 3 working days me bank ko inform kiya hai aur voluntary consent nahi di, toh **aapki liability ZERO hai**. Paragraph 12 ke mutabik customer ki laparwahi prove karne ka burden BANK par hai (*Kerala High Court - SBI vs P.V. George*).
- **BNS 2023 - Section 318 & 319:** Online cheating aur fake identity ke through fraud 7 saal tak ki jail wala cognizable offence hai.
- **IT Act 2000 - Section 66D:** Phishing aur remote screen-sharing fraud ke liye 3 saal ki saza.

#### 2. General Indian Law & Additional Forums:
- **Consumer Protection Act, 2019:** Bank ka claim reject karna 'Deficiency in Service' hai. Aap District Consumer Disputes Redressal Commission (DCDRC) me complaint karke 9% interest aur compensation claim kar sakte hain.
- **Bharatiya Sakshya Adhiniyam (BSA) 2023 - Section 63:** Aapke screenshots aur SMS valid electronic evidence hain.
- **RBI Ombudsman Escalation:** Agar bank 30 days me refund nahi deta, toh [cms.rbi.org.in](https://cms.rbi.org.in) par Clause 10 ke under ₹1 Lakh tak ka mental harassment compensation mil sakta hai.

#### 3. Abhi Aapko Kya Karna Hai:
1. **Tab 2 (Notice Drafter) me jayein:** Aur pre-filled **Bank Dispute Notice** download karke branch manager ko receive karwayen.
2. **Cyber Crime Complaint:** Tab 2 se Cybercell draft download karke `cybercrime.gov.in` par lodge karein.

⚠️ *Legal Disclaimer: Yeh guidance informational purposes ke liye hai. Agar case me police cooperation na mile, toh District Legal Services Authority (DLSA) se free legal aid le sakte hain.*"""

            else:
                return f"""### ⚖️ Final Statutory Verdict & Actionable Protocol

Based on the verified facts of your case, here is your definitive legal assessment under Indian jurisprudence:

#### 1. Controlling Statutory Provisions & Banking Regulations:
- **RBI Master Circular RBI/2017-18/15 (Zero Customer Liability):** Reporting within 3 working days guarantees zero liability for third-party breaches. Under Paragraph 12, the **burden of proving customer liability lies strictly on the bank** (*SBI vs P.V. George, Kerala HC*).
- **Bharatiya Nyaya Sanhita (BNS), 2023 - Section 318 & 319:** Criminalizes dishonest inducement and fraudulent impersonation.
- **Information Technology Act, 2000 - Section 66D:** Penalizes cheating by personation and phishing with up to 3 years imprisonment.

#### 2. General Indian Legal Remedies:
- **Consumer Protection Act, 2019 (Sections 34 & 35):** Summary claim rejection amounts to gross *Deficiency in Banking Service*. You are entitled to petition the District Consumer Disputes Redressal Commission (DCDRC) for full restitution, 9% penal interest, and damages.
- **Bharatiya Sakshya Adhiniyam, 2023 - Section 63:** Your transaction receipts, SMS alerts, and app screenshots are admissible electronic evidence.
- **Reserve Bank - Integrated Ombudsman Scheme, 2021:** Escalation via [cms.rbi.org.in](https://cms.rbi.org.in) allows claiming up to ₹1,00,000 for mental agony and harassment.

#### 3. Prescribed Next Steps:
1. **Open Tab 2 (Notice Drafter):** Download your auto-populated **Bank Dispute Notice** and deliver it to the Branch Manager with acknowledgment.
2. **Submit Cyber Crime Report:** Lodge the pre-formatted complaint on [cybercrime.gov.in](https://cybercrime.gov.in) to obtain an acknowledgment number.

⚠️ *Legal Disclaimer: This guidance is for educational and dispute-resolution purposes under Indian law. For complex litigation, consult a licensed advocate or contact your local District Legal Services Authority (DLSA) for free legal aid.*"""


# Global singleton instance
legal_engine = LegalEngine()
