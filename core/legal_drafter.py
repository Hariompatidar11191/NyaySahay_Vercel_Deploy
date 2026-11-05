"""
Automated Legal Drafter for Indian Banking Fraud & Cybercrime Victims.
Generates formally structured notices, police/cyber complaints, and RBI Ombudsman petitions.
"""

from datetime import datetime
from typing import Dict, Any, Optional


class LegalDrafter:
    def __init__(self):
        pass

    def generate_bank_grievance_notice(
        self,
        customer_name: str,
        account_number: str,
        bank_name: str,
        disputed_amount: str,
        transaction_id: str,
        transaction_date: str,
        incident_narrative: str,
        notified_within_3_days: bool = True
    ) -> str:
        """
        Drafts a formal dispute notice invoking RBI Zero-Liability Circular RBI/2017-18/15.
        """
        today = datetime.now().strftime("%d-%m-%Y")
        notice = f"""DATE: {today}

TO:
The Branch Manager / Principal Nodal Grievance Officer,
{bank_name or '[Insert Bank Name]'},
[Insert Branch Name / City]

SUBJECT: FORMAL DISPUTE NOTICE AND CLAIM FOR ZERO CUSTOMER LIABILITY UNDER RBI CIRCULAR RBI/2017-18/15 FOR UNAUTHORIZED TRANSACTION OF {disputed_amount or '[Amount]'}

Respected Sir / Madam,

I am writing this formal dispute letter regarding my Account Number: {account_number or '[Insert Account Number]'} held with your esteemed bank.

1. DETAILS OF DISPUTED TRANSACTION:
   - Disputed Amount: {disputed_amount or '[Insert Amount]'}
   - Transaction ID / UTR / Reference: {transaction_id or '[Insert Transaction/UTR ID]'}
   - Date & Time of Transaction: {transaction_date or '[Insert Date]'}
   - Nature of Debit: Unauthorized Electronic Transaction (UPI / Netbanking / Card)

2. FACTUAL BACKGROUND:
   {incident_narrative.strip() or 'An unauthorized electronic debit occurred from my bank account without my informed consent or authorization. I did not voluntarily share credentials with any unauthorized party.'}

3. STATUTORY AND REGULATORY CITATIONS:
   A. RBI Master Circular RBI/2017-18/15 (Customer Protection - Limiting Liability of Customers in Unauthorised Electronic Banking Transactions):
      - Paragraph 6(a) & 6(b): 'Zero Liability of a Customer' is mandated where the unauthorized transaction is a result of third-party breach and the customer notifies the bank within three working days of receiving communication.
      - Paragraph 12: 'The burden of proving customer liability in case of unauthorised electronic banking transactions SHALL LIE ON THE BANK.'
   
   B. Judicial Precedents:
      - The Hon'ble High Court of Kerala in 'State Bank of India vs. P.V. George (RSA No. 892 of 2018)' held that a bank has a strict fiduciary duty of care to ensure the security of electronic banking systems and cannot summarily disown liability without concrete technical proof of customer culpability.
      - The National Consumer Disputes Redressal Commission (NCDRC) in 'PNB vs. Leader Valves Ltd.' ruled that failure to promptly reverse unauthorized debits amounts to gross deficiency in banking service.

4. DEMAND FOR RELIEF:
   In strict accordance with Paragraph 9 of RBI Circular RBI/2017-18/15, you are legally mandated to:
   i. Credit the disputed amount of {disputed_amount or '[Disputed Amount]'} back to my account within TEN (10) WORKING DAYS as a shadow reversal.
   ii. Provide the complete IP logs, MAC address, beneficiary account details, and transaction trail of the fraudulent debit.
   iii. Refrain from summarily rejecting my dispute under boilerplate clauses.

5. NOTICE OF ESCALATION:
   Please note that if this dispute is rejected or not resolved within 30 days, I shall immediately escalate this grievance to the Reserve Bank - Integrated Ombudsman Scheme, 2021 (cms.rbi.org.in), seeking not only full restitution but also compensation of up to ₹1,00,000/- for mental agony and deficiency in service.

Yours sincerely,

(Signature)
Name: {customer_name or '[Your Name]'}
Contact Phone: [Your Mobile Number]
Registered Email: [Your Email]
Copy to: Banking Ombudsman & Cyber Crime Cell
"""
        return notice

    def generate_cybercrime_complaint(
        self,
        victim_name: str,
        victim_phone: str,
        disputed_amount: str,
        transaction_id: str,
        transaction_date: str,
        suspect_details: str,
        incident_narrative: str
    ) -> str:
        """
        Drafts a complaint for submission on the National Cyber Crime Reporting Portal (cybercrime.gov.in / 1930).
        """
        today = datetime.now().strftime("%d-%m-%Y")
        complaint = f"""COMPLAINT FOR NATIONAL CYBER CRIME REPORTING PORTAL (cybercrime.gov.in / HELPLINE 1930)

COMPLAINANT DETAILS:
Name: {victim_name or '[Your Name]'}
Contact Mobile: {victim_phone or '[Your Mobile Number]'}
Date of Filing: {today}

INCIDENT SUMMARY:
Category of Crime: Online Financial Fraud / UPI Fraud / Impersonation
Date & Time of Occurrence: {transaction_date or '[Insert Date and Time]'}
Total Amount Defrauded: {disputed_amount or '[Insert Disputed Amount]'}
Transaction Reference / UTR Number: {transaction_id or '[Insert UTR/Txn ID]'}
Suspect Details (UPI / Phone / Link): {suspect_details or '[Insert Suspect UPI ID / Mobile / WhatsApp Link]'}

STATEMENT OF FACTS:
{incident_narrative.strip() or 'The complainant was fraudulently targeted through deceptive online means resulting in an unauthorized financial siphoning from bank account.'}

APPLICABLE LEGAL PROVISIONS:
1. Section 66D, Information Technology Act, 2000 (Cheating by personation using computer resource - Punishable with imprisonment up to 3 years and fine).
2. Section 66C, Information Technology Act, 2000 (Identity theft and fraudulent use of unique electronic credentials).
3. Section 318, Bharatiya Nyaya Sanhita (BNS), 2023 (Cheating and dishonestly inducing delivery of property).
4. Section 319, Bharatiya Nyaya Sanhita (BNS), 2023 (Cheating by personation).
5. Section 173, Bharatiya Nagarik Suraksha Sanhita (BNSS), 2023 (Mandate for registration of cognizable offences under Zero FIR).

PRAYER / ACTION REQUESTED:
1. Immediate coordination with the nodal officers of the concerned intermediary banks/wallets via the Citizen Financial Cyber Fraud Reporting System (CFCFRMS) to freeze/lien the destination accounts before funds are withdrawn.
2. Registration of an FIR under relevant provisions of the IT Act, 2000 and Bharatiya Nyaya Sanhita, 2023.
3. Issue of necessary directions to telecommunication service providers to trace the SIM and IP logs used by the perpetrators.

VERIFICATION:
I hereby solemnly declare that the facts stated above are true and correct to the best of my knowledge and belief.

Complainant: {victim_name or '[Your Name]'}
"""
        return complaint

    def generate_ombudsman_petition(
        self,
        customer_name: str,
        bank_name: str,
        account_number: str,
        complaint_ticket_no: str,
        rejection_date: str,
        disputed_amount: str,
        summary_of_rejection: str
    ) -> str:
        """
        Drafts a petition for the Reserve Bank - Integrated Ombudsman Scheme, 2021 (cms.rbi.org.in).
        """
        today = datetime.now().strftime("%d-%m-%Y")
        petition = f"""PETITION BEFORE THE HON'BLE OMBUDSMAN (RESERVE BANK - INTEGRATED OMBUDSMAN SCHEME, 2021)
Filed via CMS Portal (https://cms.rbi.org.in)

IN THE MATTER OF:
Complainant: {customer_name or '[Complainant Name]'}
Account No.: {account_number or '[Account Number]'}
VERSUS
Regulated Entity (Bank): {bank_name or '[Bank Name]'}

SUBJECT: COMPLAINT UNDER CLAUSE 8 OF THE RESERVE BANK - INTEGRATED OMBUDSMAN SCHEME, 2021 FOR DEFICIENCY IN SERVICE AND ARBITRARY REJECTION OF UNAUTHORIZED TRANSACTION CLAIM

1. JURISDICTION & ELIGIBILITY:
   - Initial Bank Complaint Ref / Ticket ID: {complaint_ticket_no or '[Bank Ticket/Ref No]'}
   - Bank Rejection / Inaction Date: {rejection_date or '[Date of Rejection or 30 days completed]'}
   - This petition is filed within the limitation period prescribed under the Scheme.

2. GROUNDS OF COMPLAINT:
   i. Non-compliance with RBI Circular RBI/2017-18/15 on Customer Protection - Limiting Liability of Customers.
   ii. The Regulated Entity arbitrarily rejected the Complainant's claim without discharging its statutory 'Burden of Proof' mandated under Paragraph 12 of the said Circular.
   iii. The Bank failed to provide technical forensic evidence (device fingerprint, IP address, customer authentication logs) proving customer culpability.

3. STATEMENT OF REJECTION BY BANK:
   "{summary_of_rejection.strip() or 'The bank summarily stated that the transaction was authenticated through electronic credentials and closed the grievance without investigation.'}"

4. RELIEFS PRAYED FOR:
   i. Full reimbursement of the disputed amount of {disputed_amount or '[Disputed Amount]'} along with applicable bank interest.
   ii. Award of compensation of up to ₹1,00,000/- (Rupees One Lakh) under Clause 10 of the Scheme for harassment, mental distress, and deficiency in service caused by the bank.

Complainant: {customer_name or '[Complainant Name]'}
Date: {today}
"""
        return petition


# Global singleton instance
legal_drafter = LegalDrafter()
