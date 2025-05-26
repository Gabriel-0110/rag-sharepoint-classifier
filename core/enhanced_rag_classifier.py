#!/usr/bin/env python3
"""
Enhanced RAG Classification with Category Definitions
Implements the advanced RAG features mentioned in the PDF document.
"""

import json
import numpy as np
from sentence_transformers import SentenceTransformer
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
import requests
from typing import List, Dict, Tuple

class EnhancedRAGClassifier:
    def __init__(self):
        self.client = QdrantClient(url="http://localhost:6333")
        # Force CPU usage for embedding model to avoid CUDA memory conflicts
        self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2', device='cpu')
        self.mistral_url = "http://localhost:8001/classify"
        
        # SharePoint-Compatible Category Definitions for Immigration & Criminal Law
        self.category_definitions = {
            # Immigration Categories
            "Asylum & Refugee": "Immigration cases of individuals seeking protection due to past persecution or fear of persecution (e.g. asylum applications, refugee status claims).",
            "Family-Sponsored Immigration": "Immigration cases based on family relationships (e.g. visa petitions for spouses, children, parents of U.S. citizens or residents).",
            "Employment-Based Immigration": "Immigration cases based on employment, skills, or investment (e.g. work visas, employer-sponsored green cards).",
            "Non-Immigrant Visas": "Cases involving temporary visas for tourism, study, work, etc. (non-permanent stays in the U.S.).",
            "Naturalization & Citizenship": "Cases about obtaining U.S. citizenship or proof of citizenship (e.g. naturalization applications, citizenship certificates).",
            "Removal & Deportation Defense": "Cases of individuals in deportation/removal proceedings, fighting to remain in the U.S. (immigration court defense).",
            "Immigration Detention & Bonds": "Matters involving ICE detention and bond hearings to secure release from immigration custody.",
            "Waivers of Inadmissibility": "Cases focused on waivers/exceptions that forgive immigration violations or criminal grounds to allow relief.",
            "Immigration Appeals & Motions": "Appeals or motions to reopen/reconsider in immigration matters (BIA appeals, motions to reopen cases, etc.).",
            "Humanitarian Relief & Special Programs": "Immigration cases under humanitarian programs (e.g. VAWA, U visas, T visas, TPS, DACA, humanitarian parole, SIJS).",
            "ICE Enforcement & Compliance": "Issues related to ICE check-ins, orders of supervision, compliance with enforcement for individuals not detained.",
            
            # Criminal Law Categories
            "Criminal Defense (Pretrial & Trial)": "Criminal cases defending individuals charged with crimes, from investigation through trial and verdict.",
            "Criminal Appeals": "Cases appealing criminal convictions or sentences to higher courts.",
            "Criminal Post-Conviction Relief": "Motions or petitions attacking a finalized criminal conviction/sentence (e.g. habeas corpus, motions to vacate).",
            "Parole & Probation Proceedings": "Matters involving parole board hearings for release from prison, or court hearings on probation violations.",
            "Investigations & Pre-Charge": "Legal assistance during investigations or before formal charges (fact-finding, interacting with law enforcement pre-indictment)."
        }

        # SharePoint-Compatible Document Types for Immigration & Criminal Law
        self.document_types = {
            # USCIS & Immigration Agency Documents
            "USCIS Receipt Notice": "USCIS notice confirming receipt of an application or petition (Form I-797C Notice of Action).",
            "USCIS Approval Notice": "USCIS notice indicating an application or petition was approved (often Form I-797 notice of action).",
            "USCIS Appointment Notice": "USCIS notice scheduling biometrics or an interview (contains date/time for fingerprinting or interview).",
            "USCIS Request for Evidence (RFE)": "USCIS letter requesting additional evidence for a pending application.",
            "USCIS Intent to Deny/Revoke": "USCIS notice of intent to deny an application or revoke a prior approval (often abbreviated NOID or NOIR).",
            "USCIS Denial Notice": "USCIS decision letter denying an application or petition.",
            
            # Immigration Court Documents
            "Notice to Appear (NTA)": "Charging document initiating immigration court removal proceedings (lists allegations and hearing info).",
            "Immigration Court Hearing Notice": "Notice of scheduled immigration court hearing (Master or Individual hearing date).",
            "Immigration Judge Decision/Order": "Written decision or order from an Immigration Judge (granting or denying relief, removal order, etc.).",
            "BIA/AAO Appeal Decision": "Decision from the Board of Immigration Appeals or USCIS Administrative Appeals Office on an appeal.",
            
            # ICE & Enforcement Documents
            "ICE Supervision Report Notice": "ICE Order of Supervision or notice to report for ICE check-ins (conditions for release from detention).",
            
            # Criminal Court Documents
            "Parole Board Notice/Decision": "Correspondence scheduling a parole hearing or announcing a parole board's decision in a criminal case.",
            "Criminal Complaint/Indictment": "Formal criminal charging document (complaint filed by prosecutor or indictment from a grand jury).",
            "Plea Agreement": "Written agreement in a criminal case where defendant pleads guilty under agreed terms.",
            "Court Order/Judgment": "Official court order or judgment (e.g. sentencing order, final judgment, court's written order on a motion).",
            "Sentencing Memo": "Memorandum to the court arguing for a particular sentence (usually by defense, before sentencing in a criminal case).",
            
            # Legal Filings & Proceedings
            "Motion (Court Filing)": "A legal motion filed in court (requesting a court order on a specific issue).",
            "Legal Brief/Memorandum": "A document outlining legal arguments, filed in support of a motion or on appeal.",
            "Notice of Appeal": "Filing that initiates an appeal of a court or agency decision.",
            "Subpoena": "Legal document ordering someone to appear in court or produce evidence.",
            "Notice of Appearance": "Form or letter entering an attorney's appearance in a case (e.g. Form G-28 for immigration, attorney notice in court).",
            
            # Forms & Applications
            "Official Form/Application": "Completed official form for an application or petition (e.g. visa application form, immigration petition form).",
            
            # Evidence Documents
            "ID or Civil Document": "Personal identification or civil documents (passport, birth/marriage certificate, ID card) submitted as evidence.",
            "Financial Document": "Financial records (tax returns, pay stubs, bank statements, affidavits of support) submitted as evidence.",
            "Medical Record": "Medical reports or records submitted as evidence (doctor letters, hospital records, lab results).",
            "Psychological Evaluation": "Mental health evaluation or report by a psychologist/psychiatrist submitted in the case.",
            "Country Conditions Info": "Reports or articles about conditions in a country (human rights reports, news articles) used as evidence.",
            "Police/Incident Report": "Law enforcement report documenting an incident or crime (used as evidence for criminal or immigration cases).",
            "Court Record (Disposition)": "Official court record of a case's outcome (e.g. conviction certificate, docket sheet, sentencing record).",
            "Background Check/Rap Sheet": "Criminal history report (FBI or state rap sheet listing arrests/convictions).",
            "Photographs/Media": "Photographs or audio/video media files submitted as evidence.",
            "Communications Evidence": "Printouts of texts, emails, social media posts or similar communications used as evidence.",
            
            # Statements & Testimony
            "Support/Reference Letter": "Letter of support or character reference from a third party (not notarized, typically informal).",
            "Witness Affidavit/Declaration": "Sworn statement by a witness or third party (notarized affidavit or signed declaration under penalty of perjury).",
            "Expert Report/Affidavit": "Report or affidavit by an expert (forensic analysis, medical expert, country expert) providing professional evidence.",
            
            # Case Preparation Documents
            "Bond Packet": "Compiled set of documents submitted for an immigration bond hearing (cover letter, exhibits like support letters, etc.).",
            "FOIA Request": "Letter or form requesting records under the Freedom of Information Act.",
            "FOIA Records Response": "Documents received from a FOIA request (agency's response and released records).",
            "Legal Research Memo": "Internal memo analyzing legal issues or case law (attorney work product).",
            "Case Strategy Memo": "Internal document outlining legal strategy or case plan (attorney work product).",
            "Client Timeline": "Chronology of events prepared for the case (attorney or client prepared timeline of facts).",
            "Interview/Meeting Notes": "Attorney's notes from client interviews, witness interviews, or meetings.",
            "Evidence Index": "List or index of exhibits/evidence prepared for the case.",
            
            # Draft & Working Documents
            "Draft (Unfiled) Document": "Draft version of a legal document (e.g. draft affidavit, draft motion) not yet signed or filed.",
            "Unsigned Declaration (Draft)": "An unsigned sworn statement prepared for someone to sign (e.g. draft client declaration awaiting signature).",
            
            # Communications
            "Attorney-Client Correspondence": "Letters or emails between the lawyer and client regarding the case.",
            "General Correspondence": "Other case-related correspondence (letters to/from agencies, opposing counsel, cover letters, etc.).",
            
            # Reference Materials
            "Misc. Reference Material": "Any other documents in the file for reference (e.g. copies of laws, practice advisories, articles in the file)."
        }

        self._setup_category_collection()
    
    def _setup_category_collection(self):
        """Setup the category definitions collection in Qdrant as per PDF requirements."""
        try:
            # Create categories collection if it doesn't exist
            collections = self.client.get_collections().collections
            category_exists = any(c.name == "categories" for c in collections)
            
            if not category_exists:
                self.client.create_collection(
                    collection_name="categories",
                    vectors_config=VectorParams(size=384, distance=Distance.COSINE)
                )
                print("📁 Created categories collection")
            
            # Check if categories are already stored
            try:
                result = self.client.scroll("categories", limit=1)
                if len(result[0]) > 0:
                    print("📋 Category definitions already loaded")
                    return
            except:
                pass
            
            # Store category definitions as embeddings
            points = []
            point_id = 1
            
            # Store document type definitions
            for doc_type, definition in self.document_types.items():
                embedding = self.embedding_model.encode(definition)
                points.append(PointStruct(
                    id=point_id,
                    vector=embedding.tolist(),
                    payload={
                        "type": "document_type",
                        "name": doc_type,
                        "definition": definition
                    }
                ))
                point_id += 1
            
            # Store category definitions
            for category, definition in self.category_definitions.items():
                embedding = self.embedding_model.encode(definition)
                points.append(PointStruct(
                    id=point_id,
                    vector=embedding.tolist(),
                    payload={
                        "type": "category",
                        "name": category,
                        "definition": definition
                    }
                ))
                point_id += 1
            
            # Upload to Qdrant
            self.client.upsert("categories", points)
            print(f"✅ Stored {len(points)} category/type definitions in Qdrant")
            
        except Exception as e:
            print(f"❌ Error setting up categories: {e}")
    
    def get_rag_context(self, document_text: str, top_k: int = 3) -> Tuple[List[Dict], List[Dict]]:
        """
        Get RAG context using vector similarity as specified in PDF.
        Returns similar documents and relevant category definitions.
        """
        try:
            # Generate embedding for the document
            doc_embedding = self.embedding_model.encode(document_text)
            
            # Search for similar documents
            similar_docs = self.client.search(
                collection_name="documents",
                query_vector=doc_embedding.tolist(),
                limit=top_k,
                with_payload=True
            )
            
            # Search for relevant category definitions
            relevant_categories = self.client.search(
                collection_name="categories",
                query_vector=doc_embedding.tolist(),
                limit=top_k,
                with_payload=True
            )
            
            return similar_docs, relevant_categories
            
        except Exception as e:
            print(f"❌ Error getting RAG context: {e}")
            return [], []
    
    def classify_with_rag(self, document_text: str, filename: str) -> Dict:
        """
        Enhanced classification using RAG context as specified in PDF document.
        """
        try:
            # Get RAG context
            similar_docs, relevant_categories = self.get_rag_context(document_text)
            
            # Build enhanced prompt with RAG context
            prompt = self._build_rag_prompt(document_text, similar_docs, relevant_categories)
            
            # Call Mistral API with enhanced prompt
            response = requests.post(
                self.mistral_url,
                json={"text": prompt},
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                
                # Add RAG context info to result
                result["rag_context"] = {
                    "similar_documents": len(similar_docs),
                    "relevant_categories": len(relevant_categories),
                    "context_used": True
                }
                
                return result
            else:
                # Fallback to basic classification
                return self._fallback_classification(document_text)
                
        except Exception as e:
            print(f"❌ Error in RAG classification: {e}")
            return self._fallback_classification(document_text)
    
    def _build_rag_prompt(self, document_text: str, similar_docs: List, relevant_categories: List) -> str:
        """Build enhanced prompt with RAG context, using SharePoint-compatible format."""
        prompt = f"""You are an AI legal document classifier for a law firm specializing in U.S. immigration and criminal law. Your task is to analyze an input document (its text content and context) and assign **one appropriate Document Category and one Document Type** from the lists provided below.

DOCUMENT TO CLASSIFY:
{document_text[:3000]}

**Document Categories (choose one from this list):**
"""
        # Add all categories from our definitions
        for category in sorted(self.category_definitions.keys()):
            prompt += f"- **{category}:** {self.category_definitions[category]}\n"

        prompt += "\n**Document Types (choose one from this list):**\n"
        
        # Add all document types from our definitions
        for doc_type in sorted(self.document_types.keys()):
            prompt += f"- **{doc_type}:** {self.document_types[doc_type]}\n"

        # Add contextual information if available
        if similar_docs or relevant_categories:
            prompt += "\n**CONTEXTUAL INFORMATION (Consider if helpful):**\n"
            
            if similar_docs:
                prompt += "Similar documents from database:\n"
                for i, doc in enumerate(similar_docs[:2]):
                    if doc.payload and 'doc_type' in doc.payload:
                        prompt += f"- Example {i+1}: Type '{doc.payload.get('doc_type', 'N/A')}', Category '{doc.payload.get('doc_category', 'N/A')}'\n"
            
            if relevant_categories:
                prompt += "Relevant context from similar cases:\n"
                for cat in relevant_categories[:2]:
                    if cat.payload and cat.payload.get('type') == 'category':
                        prompt += f"- {cat.payload['name']}: {cat.payload['definition'][:100]}...\n"

        prompt += """
**Classification Task:** Read the content of the provided document and determine:
1. **Category:** Which one **Document Category** best fits the subject matter or context of the document?
2. **Type:** Which one **Document Type** best describes the format or purpose of the document itself?

**Output Format:** Provide your answer in a concise text format as follows – `Category: [Chosen Category]; Type: [Chosen Document Type]`. Do not deviate from the given lists. If the document does not clearly match any category/type, choose the closest reasonable option (but **do not** invent new labels).

**Guidance:**
- Use cues from the document's text (titles, keywords, phrases) to infer its nature.
- Ensure the category reflects the case context (immigration vs criminal, and the specific area within those), and the type reflects the document's form (notice, motion, evidence, etc.).
- If multiple categories or types seem to apply, pick the one that is most specific or central to the document's main purpose.
- **Only output one category and one type.** No additional commentary is needed.

Now proceed to classify the given document with the format **"Category: ...; Type: ..."** only.
"""
        return prompt

    def _fallback_classification(self, document_text: str) -> Dict:
        """Improved fallback using SharePoint-compatible categories and document types."""
        # Simplified fallback, primary classification should happen via LLM.
        # This is a basic keyword spotter if LLM fails completely.
        text_lower = document_text.lower()
        doc_type = "Misc. Reference Material"  # Default fallback using SharePoint-compatible type
        doc_category = "Immigration Appeals & Motions"  # Default fallback category
        confidence = "Low"

        # Immigration Keywords
        immigration_keywords = [
            'uscis', 'immigration', 'visa', 'i-130', 'i-485', 'n-400', 'asylum', 'deportation', 
            'removal proceeding', 'green card', 'naturalization', 'eoir', 'ice', 'cbp',
            'petition for alien relative', 'adjustment of status', 'notice to appear',
            'refugee', 'family petition', 'employment visa', 'tourist visa', 'citizenship',
            'detention', 'bond hearing', 'waiver', 'inadmissibility', 'humanitarian'
        ]
        # Criminal Keywords
        criminal_keywords = [
            'criminal', 'felony', 'misdemeanor', 'arrest', 'police report', 'court order', 
            'plea agreement', 'sentencing', 'indictment', 'complaint', 'defendant', 
            'prosecutor', 'dui', 'dwi', 'assault', 'burglary', 'fraud', 'appeal',
            'conviction', 'parole', 'probation', 'investigation', 'habeas corpus'
        ]

        is_immigration = any(keyword in text_lower for keyword in immigration_keywords)
        is_criminal = any(keyword in text_lower for keyword in criminal_keywords)

        # Document type detection based on keywords
        if "receipt notice" in text_lower:
            doc_type = "USCIS Receipt Notice"
        elif "approval notice" in text_lower:
            doc_type = "USCIS Approval Notice"
        elif "rfe" in text_lower or "request for evidence" in text_lower:
            doc_type = "USCIS Request for Evidence (RFE)"
        elif "notice to appear" in text_lower:
            doc_type = "Notice to Appear (NTA)"
        elif "hearing notice" in text_lower and "immigration" in text_lower:
            doc_type = "Immigration Court Hearing Notice"
        elif "complaint" in text_lower or "indictment" in text_lower:
            doc_type = "Criminal Complaint/Indictment"
        elif "plea agreement" in text_lower:
            doc_type = "Plea Agreement"
        elif "police report" in text_lower:
            doc_type = "Police/Incident Report"
        elif "motion" in text_lower:
            doc_type = "Motion (Court Filing)"
        elif "brief" in text_lower or "memorandum" in text_lower:
            doc_type = "Legal Brief/Memorandum"
        elif "affidavit" in text_lower or "declaration" in text_lower:
            doc_type = "Witness Affidavit/Declaration"
        elif "correspondence" in text_lower or "letter" in text_lower:
            doc_type = "General Correspondence"

        # Category classification
        if is_immigration and is_criminal:
            # Both immigration and criminal elements present
            if "deportation" in text_lower or "removal" in text_lower:
                doc_category = "Removal & Deportation Defense"
            else:
                doc_category = "Criminal Defense (Pretrial & Trial)"
        elif is_immigration:
            # Immigration-specific categorization
            if "asylum" in text_lower or "refugee" in text_lower:
                doc_category = "Asylum & Refugee"
            elif "family" in text_lower or "spouse" in text_lower or "marriage" in text_lower:
                doc_category = "Family-Sponsored Immigration"
            elif "employment" in text_lower or "work" in text_lower or "job" in text_lower:
                doc_category = "Employment-Based Immigration"
            elif "tourist" in text_lower or "student" in text_lower or "visitor" in text_lower:
                doc_category = "Non-Immigrant Visas"
            elif "citizenship" in text_lower or "naturalization" in text_lower:
                doc_category = "Naturalization & Citizenship"
            elif "deportation" in text_lower or "removal" in text_lower:
                doc_category = "Removal & Deportation Defense"
            elif "detention" in text_lower or "bond" in text_lower:
                doc_category = "Immigration Detention & Bonds"
            elif "waiver" in text_lower or "inadmissibility" in text_lower:
                doc_category = "Waivers of Inadmissibility"
            elif "appeal" in text_lower or "motion" in text_lower:
                doc_category = "Immigration Appeals & Motions"
            elif "humanitarian" in text_lower or "vawa" in text_lower or "u visa" in text_lower:
                doc_category = "Humanitarian Relief & Special Programs"
            elif "ice" in text_lower or "supervision" in text_lower:
                doc_category = "ICE Enforcement & Compliance"
            else:
                doc_category = "Immigration Appeals & Motions"  # Default immigration
                
        elif is_criminal:
            # Criminal-specific categorization
            if "appeal" in text_lower:
                doc_category = "Criminal Appeals"
            elif "habeas corpus" in text_lower or "post-conviction" in text_lower:
                doc_category = "Criminal Post-Conviction Relief"
            elif "parole" in text_lower or "probation" in text_lower:
                doc_category = "Parole & Probation Proceedings"
            elif "investigation" in text_lower or "pre-charge" in text_lower:
                doc_category = "Investigations & Pre-Charge"
            else:
                doc_category = "Criminal Defense (Pretrial & Trial)"  # Default criminal

        # Increase confidence if we found specific indicators
        if doc_type != "Misc. Reference Material":
            confidence = "Medium"

        return {
            "doc_type": doc_type,
            "doc_category": doc_category,
            "confidence": confidence,
            "rag_context": {"context_used": False, "method": "rules-based fallback"}
        }

def main():
    """Test the enhanced RAG classifier."""
    print("🚀 Testing Enhanced RAG Classification System")
    
    classifier = EnhancedRAGClassifier()
    
    # Test with sample text
    test_text = """
    SOFTWARE DEVELOPMENT AGREEMENT
    
    This agreement is entered into between Company A and Company B
    for the development of a web application. The contract includes
    payment terms, deliverables, timeline, and intellectual property rights.
    """
    
    result = classifier.classify_with_rag(test_text, "test_agreement.pdf")
    
    print(f"\n📋 Classification Result:")
    print(f"   Document Type: {result.get('doc_type', 'Unknown')}")
    print(f"   Category: {result.get('doc_category', 'Unknown')}")
    print(f"   Confidence: {result.get('confidence', 'Unknown')}")
    print(f"   RAG Context: {result.get('rag_context', {})}")

if __name__ == "__main__":
    main()
