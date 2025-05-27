#!/usr/bin/env python3
"""
Enhanced RAG Classification with Category Definitions
Implements the advanced RAG features mentioned in the PDF document.
"""

import json
import numpy as np
from sentence_transformers import SentenceTransformer
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct, Filter, FieldCondition, Range
import requests
from typing import List, Dict, Tuple
import hashlib
import logging
import torch
from transformers import (
    AutoTokenizer, AutoModelForCausalLM, AutoModelForSequenceClassification,
    BitsAndBytesConfig, pipeline
)
import gc

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class EnhancedRAGClassifier:
    """
    Enhanced RAG Classification with 3-Model Architecture:
    1. PRIMARY CLASSIFIER: SaulLM (Equall/Saul-7B-Instruct-v1) with 8-bit quantization
    2. FALLBACK CLASSIFIER: Mistral (mistralai/Mistral-7B-Instruct-v0.3) with 8-bit quantization  
    3. VALIDATOR: BART-MNLI (facebook/bart-large-mnli) for zero-shot validation
    
    Maintains existing Qdrant embedding + search logic, SharePoint integration, and CSV logging.
    """
    
    def __init__(self):
        """Initialize the 3-model RAG classification system."""
        logger.info("🚀 Initializing Enhanced RAG Classifier with 3-Model Architecture")
        
        # Initialize Qdrant client and embedding model (preserve existing logic)
        self.client = QdrantClient(url="http://localhost:6333")
        # Force CPU usage for embedding model to avoid CUDA memory conflicts
        self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2', device='cpu')
        
        # Initialize model components
        self.primary_model = None      # SaulLM - loaded on demand
        self.primary_tokenizer = None
        self.fallback_model = None     # Mistral - loaded on demand  
        self.fallback_tokenizer = None
        self.validator_pipeline = None # BART-MNLI - loaded on demand
        
        # Model configuration for 8-bit quantization
        self.quantization_config = BitsAndBytesConfig(
            load_in_8bit=True,
            llm_int8_enable_fp32_cpu_offload=True
        )
        
        # Legacy Mistral API URL (keep for backwards compatibility)
        self.mistral_url = "http://localhost:8001/chat/completions"
        
        logger.info("📊 Setting up vector database collections")
        
        # Category definitions (preserve existing logic)
        self.category_definitions = {
            "Asylum & Refugee": {
                "description": "Immigration cases of individuals seeking protection due to past persecution or fear of persecution (e.g. asylum applications, refugee status claims).",
                "keywords": ["asylum", "refugee", "persecution", "fear", "protection", "withholding", "removal", "torture", "CAT"],
                "document_types": ["asylum application", "refugee petition", "country condition evidence", "persecution evidence"]
            },
            "Family-Sponsored Immigration": {
                "description": "Immigration cases based on family relationships (e.g. visa petitions for spouses, children, parents of U.S. citizens or residents).",
                "keywords": ["family", "spouse", "marriage", "i-130", "i-485", "petition", "relative", "child", "parent"],
                "document_types": ["marriage certificate", "birth certificate", "family petition", "adjustment of status"]
            },
            "Employment-Based Immigration": {
                "description": "Immigration cases for employment-based visas and permanent residence through work sponsorship.",
                "keywords": ["employment", "work", "job", "labor", "h1b", "eb-1", "eb-2", "eb-3", "perm", "sponsor"],
                "document_types": ["labor certification", "employment petition", "work authorization", "job offer"]
            },
            "Non-Immigrant Visas": {
                "description": "Temporary visa applications for tourists, students, workers, and other temporary visitors.",
                "keywords": ["tourist", "student", "visitor", "f-1", "b-1", "b-2", "temporary", "visa", "nonimmigrant"],
                "document_types": ["visa application", "student records", "travel documents", "temporary status"]
            },
            "Naturalization & Citizenship": {
                "description": "Cases about obtaining U.S. citizenship or proof of citizenship (e.g. naturalization applications, citizenship certificates).",
                "keywords": ["citizenship", "naturalization", "n-400", "oath", "ceremony", "citizen", "passport application"],
                "document_types": ["citizenship application", "naturalization certificate", "citizenship test", "passport"]
            },
            "Removal & Deportation Defense": {
                "description": "Cases of individuals in deportation/removal proceedings, fighting to remain in the U.S. (immigration court defense).",
                "keywords": ["removal", "deportation", "nta", "notice to appear", "immigration court", "eoir", "hearing"],
                "document_types": ["notice to appear", "hearing notice", "motion to terminate", "cancellation"]
            },
            "Immigration Detention & Bonds": {
                "description": "Matters involving ICE detention and bond hearings to secure release from immigration custody.",
                "keywords": ["detention", "bond", "ice", "custody", "release", "parole", "detained"],
                "document_types": ["bond motion", "detention order", "parole request", "custody records"]
            },
            "Waivers of Inadmissibility": {
                "description": "Cases focused on waivers/exceptions that forgive immigration violations or criminal grounds to allow relief.",
                "keywords": ["waiver", "inadmissibility", "i-601", "i-212", "forgiveness", "hardship", "extreme"],
                "document_types": ["waiver application", "hardship evidence", "medical waiver", "criminal waiver"]
            },
            "Immigration Appeals & Motions": {
                "description": "Appeals or motions to reopen/reconsider in immigration matters (BIA appeals, motions to reopen cases, etc.).",
                "keywords": ["appeal", "motion", "reopen", "reconsider", "bia", "federal court", "petition for review"],
                "document_types": ["notice of appeal", "motion to reopen", "brief", "petition for review"]
            },
            "Humanitarian & Special Programs": {
                "description": "Immigration cases under humanitarian programs (e.g. VAWA, U visas, T visas, TPS, DACA, humanitarian parole, SIJS).",
                "keywords": ["vawa", "u visa", "t visa", "tps", "daca", "humanitarian", "sijs", "violence", "trafficking"],
                "document_types": ["u visa petition", "vawa petition", "tps application", "trafficking evidence"]
            },
            "ICE Enforcement & Compliance": {
                "description": "Issues related to ICE check-ins, orders of supervision, compliance with enforcement for individuals not detained.",
                "keywords": ["ice", "supervision", "check-in", "compliance", "monitoring", "enforcement"],
                "document_types": ["supervision order", "check-in notice", "compliance report", "monitoring agreement"]
            },
            "Criminal Defense (Pretrial & Trial)": {
                "description": "Criminal cases defending individuals charged with crimes, from investigation through trial and verdict.",
                "keywords": ["criminal", "charges", "indictment", "trial", "defense", "plea", "guilty", "innocent"],
                "document_types": ["indictment", "complaint", "plea agreement", "trial transcript", "discovery"]
            },
            "Criminal Appeals": {
                "description": "Cases appealing criminal convictions or sentences to higher courts.",
                "keywords": ["appeal", "conviction", "sentence", "appellate", "review", "overturn"],
                "document_types": ["notice of appeal", "appellate brief", "court decision", "sentencing memo"]
            },
            "Criminal Post-Conviction Relief": {
                "description": "Motions or petitions attacking a finalized criminal conviction/sentence (e.g. habeas corpus, motions to vacate).",
                "keywords": ["habeas", "corpus", "post-conviction", "vacate", "ineffective", "assistance", "counsel"],
                "document_types": ["habeas petition", "motion to vacate", "ineffective assistance claim"]
            },
            "Parole & Probation Proceedings": {
                "description": "Matters involving parole board hearings for release from prison, or court hearings on probation violations.",
                "keywords": ["parole", "probation", "violation", "hearing", "release", "supervision", "conditions"],
                "document_types": ["parole hearing", "probation report", "violation notice", "supervision agreement"]
            }
        }

        self.document_types = {
            # Immigration Document Types
            "USCIS Receipt Notice": "USCIS notice confirming receipt of an application or petition (Form I-797C Notice of Action).",
            "USCIS Approval Notice": "USCIS notice indicating an application or petition was approved (often Form I-797 notice of action).",
            "USCIS Appointment Notice": "USCIS notice scheduling biometrics or an interview (contains date/time for fingerprinting or interview).",
            "USCIS Request for Evidence (RFE)": "USCIS letter requesting additional evidence for a pending application.",
            "USCIS Intent to Deny/Revoke": "USCIS notice of intent to deny an application or revoke a prior approval (often abbreviated NOID or NOIR).",
            "USCIS Denial Notice": "USCIS decision letter denying an application or petition.",
            "Notice to Appear (NTA)": "Charging document initiating immigration court removal proceedings (lists allegations and hearing info).",
            "Immigration Court Hearing Notice": "Notice of scheduled immigration court hearing (Master or Individual hearing date).",
            "Immigration Judge Decision/Order": "Written decision or order from an Immigration Judge (granting or denying relief, removal order, etc.).",
            "BIA/AAO Appeal Decision": "Decision from the Board of Immigration Appeals or USCIS Administrative Appeals Office on an appeal.",
            "ICE Supervision Report Notice": "ICE Order of Supervision or notice to report for ICE check-ins (conditions for release from detention).",
            "Parole Board Notice/Decision": "Correspondence scheduling a parole hearing or announcing a parole board's decision in a criminal or immigration case.",
            "Motion (Court Filing)": "A legal motion filed in court (requesting a court order on a specific issue).",
            "Legal Brief/Memorandum": "A document outlining legal arguments, filed in support of a motion or on appeal.",
            "Notice of Appeal": "Filing that initiates an appeal of a court or agency decision.",
            "Subpoena": "Legal document ordering someone to appear in court or produce evidence.",
            "Notice of Appearance": "Form or letter entering an attorney's appearance in a case (e.g. Form G-28 for immigration, attorney notice in court).",
            "Official Form/Application": "Completed official form for an application or petition (e.g. visa application form, immigration petition form).",
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
            "Support/Reference Letter": "Letter of support or character reference from a third party (not notarized, typically informal).",
            "Witness Affidavit/Declaration": "Sworn statement by a witness or third party (notarized affidavit or signed declaration under penalty of perjury).",
            "Affidavit": "A sworn written statement made under oath or affirmation, used as evidence in court or agency proceedings.",
            "Bond Packet": "Compiled set of documents submitted for an immigration bond hearing (cover letter, exhibits like support letters, etc.).",
            "FOIA Request": "Letter or form requesting records under the Freedom of Information Act.",
            "FOIA Records Response": "Documents received from a FOIA request (agency's response and released records).",
            "Legal Research Memo": "Internal memo analyzing legal issues or case law (attorney work product).",
            "Case Strategy Memo": "Internal document outlining legal strategy or case plan (attorney work product).",
            "Client Timeline": "Chronology of events prepared for the case (attorney or client prepared timeline of facts).",
            "Interview/Meeting Notes": "Attorney's notes from client interviews, witness interviews, or meetings.",
            "Evidence Index": "List or index of exhibits/evidence prepared for the case.",
            "Draft (Unfiled) Document": "Draft version of a legal document (e.g. draft affidavit, draft motion) not yet signed or filed.",
            "Unsigned Declaration": "An unsigned sworn statement prepared for someone to sign (e.g. draft client declaration awaiting signature).",
            "Attorney-Client Correspondence": "Letters or emails between the lawyer and client regarding the case.",
            "General Correspondence": "Other case-related correspondence (letters to/from agencies, opposing counsel, cover letters, etc.).",
            "Misc. Reference Material": "Any other documents in the file for reference (e.g. copies of laws, practice advisories, articles in the file).",
            # Criminal Document Types
            "Criminal Complaint/Indictment": "Formal criminal charging document (complaint filed by prosecutor or indictment from a grand jury).",
            "Plea Agreement": "Written agreement in a criminal case where defendant pleads guilty under agreed terms.",
            "Court Order/Judgment": "Official court order or judgment (e.g. sentencing order, final judgment, court's written order on a motion).",
            "Sentencing Memo": "Memorandum to the court arguing for a particular sentence (usually by defense, before sentencing in a criminal case)."
        }

        # Initialize vector database and category data (preserve existing logic)
        self._setup_collections()
        self._populate_category_vectors()
    
    def _load_primary_classifier(self):
        """
        Load SaulLM (Equall/Saul-7B-Instruct-v1) as primary classifier with 8-bit quantization.
        This model specializes in legal document understanding.
        """
        if self.primary_model is not None:
            return  # Already loaded
            
        try:
            logger.info("🔥 Loading PRIMARY CLASSIFIER: SaulLM (Equall/Saul-7B-Instruct-v1) with 8-bit quantization")
            
            model_name = "Equall/Saul-7B-Instruct-v1"
            
            # Load tokenizer first
            self.primary_tokenizer = AutoTokenizer.from_pretrained(model_name)
            if self.primary_tokenizer.pad_token is None:
                self.primary_tokenizer.pad_token = self.primary_tokenizer.eos_token
            
            # Load model with 8-bit quantization
            self.primary_model = AutoModelForCausalLM.from_pretrained(
                model_name,
                quantization_config=self.quantization_config,
                device_map="auto",
                torch_dtype=torch.float16,
                trust_remote_code=True
            )
            
            logger.info("✅ SaulLM primary classifier loaded successfully")
            
        except Exception as e:
            logger.error(f"❌ Failed to load SaulLM primary classifier: {e}")
            self.primary_model = None
            self.primary_tokenizer = None
    
    def _load_fallback_classifier(self):
        """
        Load Mistral (mistralai/Mistral-7B-Instruct-v0.3) as fallback classifier with 8-bit quantization.
        Used when primary classifier fails or has low confidence.
        """
        if self.fallback_model is not None:
            return  # Already loaded
            
        try:
            logger.info("🔄 Loading FALLBACK CLASSIFIER: Mistral-7B-Instruct-v0.3 with 8-bit quantization")
            
            model_name = "mistralai/Mistral-7B-Instruct-v0.3"
            
            # Load tokenizer first
            self.fallback_tokenizer = AutoTokenizer.from_pretrained(model_name)
            if self.fallback_tokenizer.pad_token is None:
                self.fallback_tokenizer.pad_token = self.fallback_tokenizer.eos_token
            
            # Load model with 8-bit quantization
            self.fallback_model = AutoModelForCausalLM.from_pretrained(
                model_name,
                quantization_config=self.quantization_config,
                device_map="auto",
                torch_dtype=torch.float16,
                trust_remote_code=True
            )
            
            logger.info("✅ Mistral fallback classifier loaded successfully")
            
        except Exception as e:
            logger.error(f"❌ Failed to load Mistral fallback classifier: {e}")
            self.fallback_model = None
            self.fallback_tokenizer = None
    
    def _load_validator(self):
        """
        Load BART-MNLI (facebook/bart-large-mnli) as zero-shot validator.
        Used to validate classification results from primary/fallback models.
        """
        if self.validator_pipeline is not None:
            return  # Already loaded
            
        try:
            logger.info("🔍 Loading VALIDATOR: BART-MNLI for zero-shot classification validation")
            
            # Create zero-shot classification pipeline
            self.validator_pipeline = pipeline(
                "zero-shot-classification",
                model="facebook/bart-large-mnli",
                device=0 if torch.cuda.is_available() else -1  # Use GPU if available
            )
            
            logger.info("✅ BART-MNLI validator loaded successfully")
            
        except Exception as e:
            logger.error(f"❌ Failed to load BART-MNLI validator: {e}")
            self.validator_pipeline = None
    
    def _cleanup_model_memory(self, model_type: str = "all"):
        """
        Clean up model memory to prevent CUDA OOM errors.
        Args:
            model_type: "primary", "fallback", "validator", or "all"
        """
        try:
            if model_type in ["primary", "all"] and self.primary_model is not None:
                logger.info("🧹 Cleaning up primary classifier memory")
                del self.primary_model
                del self.primary_tokenizer
                self.primary_model = None
                self.primary_tokenizer = None
            
            if model_type in ["fallback", "all"] and self.fallback_model is not None:
                logger.info("🧹 Cleaning up fallback classifier memory")
                del self.fallback_model
                del self.fallback_tokenizer
                self.fallback_model = None
                self.fallback_tokenizer = None
            
            if model_type in ["validator", "all"] and self.validator_pipeline is not None:
                logger.info("🧹 Cleaning up validator memory")
                del self.validator_pipeline
                self.validator_pipeline = None
            
            # Force garbage collection and clear CUDA cache
            gc.collect()
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
                
        except Exception as e:
            logger.warning(f"⚠️ Error during memory cleanup: {e}")

    def _setup_collections(self):
        """Setup both category definitions and document collections in Qdrant."""
        try:
            collections = self.client.get_collections().collections
            collection_names = [c.name for c in collections]
            
            # Setup categories collection for category definitions
            if "categories" not in collection_names:
                logger.info("Creating categories collection...")
                self.client.create_collection(
                    collection_name="categories",
                    vectors_config=VectorParams(size=384, distance=Distance.COSINE)
                )
                logger.info("Categories collection created")
            
            # Setup documents collection for storing processed documents
            if "documents" not in collection_names:
                logger.info("Creating documents collection...")
                self.client.create_collection(
                    collection_name="documents", 
                    vectors_config=VectorParams(size=384, distance=Distance.COSINE)
                )
                logger.info("Documents collection created")
                
            # Setup examples collection for classification examples
            if "examples" not in collection_names:
                logger.info("Creating examples collection...")
                self.client.create_collection(
                    collection_name="examples",
                    vectors_config=VectorParams(size=384, distance=Distance.COSINE)
                )
                logger.info("Examples collection created")
                
        except Exception as e:
            logger.error(f"Error setting up collections: {e}")
    
    def _populate_category_vectors(self):
        """Populate the categories collection with category definitions and examples."""
        try:
            # Check if categories are already populated
            count = self.client.count("categories")
            if count.count > 0:
                logger.info(f"Categories collection already populated with {count.count} entries")
                return
            
            logger.info("Populating category vectors...")
            points = []
            
            for idx, (category, details) in enumerate(self.category_definitions.items()):
                # Create text for embedding
                category_text = f"{category}: {details['description']} Keywords: {', '.join(details['keywords'])} Common documents: {', '.join(details['document_types'])}"
                
                # Generate embedding
                embedding = self.embedding_model.encode(category_text)
                
                # Create point
                point = PointStruct(
                    id=idx,
                    vector=embedding.tolist(),
                    payload={
                        "category": category,
                        "description": details["description"],
                        "keywords": details["keywords"],
                        "document_types": details["document_types"],
                        "type": "category_definition"
                    }
                )
                points.append(point)
            
            # Insert points
            self.client.upsert("categories", points)
            logger.info(f"Populated {len(points)} category definitions in vector database")
            
            # Add some classification examples
            self._add_classification_examples()
            
        except Exception as e:
            logger.error(f"Error populating category vectors: {e}")
    
    def _add_classification_examples(self):
        """Add real classification examples to improve RAG context."""
        examples = [
            {
                "text": "USCIS Receipt Notice I-797C for Form I-130 Petition for Alien Relative filed for spouse",
                "category": "Family-Sponsored Immigration",
                "doc_type": "USCIS Receipt Notice",
                "description": "Receipt notice for family petition"
            },
            {
                "text": "Notice to Appear charging removability under section 237(a)(1)(A) for overstaying authorized period",
                "category": "Removal & Deportation Defense", 
                "doc_type": "Notice to Appear (NTA)",
                "description": "Immigration court removal proceedings charging document"
            },
            {
                "text": "Application for Asylum and for Withholding of Removal based on political persecution",
                "category": "Asylum & Refugee",
                "doc_type": "Official Form/Application",
                "description": "Asylum application form"
            },
            {
                "text": "Criminal Complaint charging defendant with aggravated assault in the first degree",
                "category": "Criminal Defense (Pretrial & Trial)",
                "doc_type": "Criminal Complaint/Indictment", 
                "description": "Formal criminal charging document"
            },
            {
                "text": "Motion for Bond Redetermination in Immigration Court proceedings",
                "category": "Immigration Detention & Bonds",
                "doc_type": "Motion (Court Filing)",
                "description": "Motion requesting bond hearing in immigration court"
            },
            {
                "text": "I-601 Application for Waiver of Grounds of Inadmissibility based on extreme hardship",
                "category": "Waivers of Inadmissibility", 
                "doc_type": "Official Form/Application",
                "description": "Waiver application for immigration violations"
            },
            {
                "text": "U-Visa Petition for victims of qualifying criminal activity who suffered mental trauma",
                "category": "Humanitarian & Special Programs",
                "doc_type": "Official Form/Application", 
                "description": "U visa petition for crime victims"
            },
            {
                "text": "Birth Certificate from Mexico with certified English translation for immigration purposes",
                "category": "Family-Sponsored Immigration",
                "doc_type": "ID or Civil Document",
                "description": "Supporting civil document for family petition"
            }
        ]
        
        try:
            points = []
            for idx, example in enumerate(examples):
                embedding = self.embedding_model.encode(example["text"])
                
                point = PointStruct(
                    id=1000 + idx,  # Use different ID range for examples
                    vector=embedding.tolist(),
                    payload={
                        "text": example["text"],
                        "category": example["category"],
                        "doc_type": example["doc_type"],
                        "description": example["description"],
                        "type": "classification_example"
                    }
                )
                points.append(point)
            
            self.client.upsert("examples", points)
            logger.info(f"Added {len(examples)} classification examples to vector database")
            
        except Exception as e:
            logger.error(f"Error adding classification examples: {e}")
    
    def store_processed_document(self, text: str, filename: str, doc_type: str, doc_category: str, confidence: str):
        """Store processed document in vector database for future RAG context."""
        try:
            # Create document hash for ID
            doc_hash = hashlib.md5(f"{filename}_{text[:100]}".encode()).hexdigest()
            doc_id = int(doc_hash[:8], 16)  # Convert to integer ID
            
            # Generate embedding
            embedding = self.embedding_model.encode(text[:2000])  # Limit text length
            
            # Store document
            point = PointStruct(
                id=doc_id,
                vector=embedding.tolist(),
                payload={
                    "filename": filename,
                    "text_excerpt": text[:500],
                    "doc_type": doc_type,
                    "doc_category": doc_category,
                    "confidence": confidence,
                    "type": "processed_document"
                }
            )
            
            self.client.upsert("documents", [point])
            logger.info(f"Stored document {filename} in vector database")
            
        except Exception as e:
            logger.error(f"Error storing document {filename}: {e}")
    
    def _get_rag_context(self, document_text: str, filename: str) -> Dict:
        """Get RAG context using vector similarity search."""
        try:
            # Generate embedding for the document
            query_embedding = self.embedding_model.encode(document_text[:1000])
            
            # Search for similar categories (very low threshold to ensure matches)
            category_results = self.client.search(
                collection_name="categories",
                query_vector=query_embedding.tolist(),
                limit=5,
                score_threshold=0.0  # Remove threshold to get all results
            )
            
            # Search for similar examples
            example_results = []
            try:
                example_results = self.client.search(
                    collection_name="examples", 
                    query_vector=query_embedding.tolist(),
                    limit=5,
                    score_threshold=0.0  # Remove threshold to get all results
                )
            except Exception as e:
                logger.debug(f"No examples found or examples collection empty: {e}")
            
            # Search for similar processed documents
            similar_docs = []
            try:
                doc_results = self.client.search(
                    collection_name="documents",
                    query_vector=query_embedding.tolist(), 
                    limit=3,
                    score_threshold=0.0  # Remove threshold to get all results
                )
                similar_docs = doc_results
            except Exception as e:
                logger.debug(f"No similar documents found: {e}")
            
            return {
                "similar_categories": [
                    {
                        "category": result.payload.get("category", "Unknown"),
                        "description": result.payload.get("description", ""),
                        "score": result.score,
                        "keywords": result.payload.get("keywords", []) if isinstance(result.payload.get("keywords"), list) else []
                    }
                    for result in category_results if result.payload and "category" in result.payload
                ],
                "similar_examples": [
                    {
                        "text": result.payload.get("text", ""),
                        "category": result.payload.get("category", "Unknown"), 
                        "doc_type": result.payload.get("doc_type", "Unknown"),
                        "score": result.score
                    }
                    for result in example_results if result.payload and "category" in result.payload
                ],
                "similar_documents": [
                    {
                        "filename": result.payload.get("filename", "Unknown"),
                        "doc_type": result.payload.get("doc_type", "Unknown"),
                        "doc_category": result.payload.get("doc_category", "Unknown"),
                        "score": result.score
                    }
                    for result in similar_docs if result.payload and "doc_category" in result.payload
                ]
            }
            
        except Exception as e:
            logger.error(f"Error getting RAG context: {e}")
            return {"similar_categories": [], "similar_examples": [], "similar_documents": []}

    def get_rag_context(self, document_text: str, top_k: int = 3) -> Tuple[List, List]:
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
        NEW 3-MODEL CLASSIFICATION PIPELINE:
        1. Get RAG context from Qdrant vector database (preserve existing logic)
        2. Try PRIMARY CLASSIFIER: SaulLM (legal-specialized model)
        3. If primary fails/low confidence, try FALLBACK CLASSIFIER: Mistral
        4. Validate result with BART-MNLI zero-shot classifier
        5. Return enhanced result with confidence scoring
        """
        logger.info(f"🚀 Starting 3-Model RAG Classification Pipeline for {filename}")
        
        try:
            # STEP 1: Get RAG context using existing vector similarity search (preserve logic)
            logger.info("📊 Step 1: Retrieving RAG context from Qdrant vector database")
            rag_context = self._get_rag_context(document_text, filename)
            
            logger.info(f"✅ RAG context retrieved: {len(rag_context['similar_categories'])} categories, "
                       f"{len(rag_context['similar_examples'])} examples, "
                       f"{len(rag_context['similar_documents'])} similar docs")
            
            # STEP 2: Try PRIMARY CLASSIFIER (SaulLM)
            logger.info("🔥 Step 2: Attempting classification with PRIMARY CLASSIFIER (SaulLM)")
            primary_result = self._classify_with_primary(document_text, rag_context, filename)
            
            # STEP 3: Check if primary classification was successful and confident
            if primary_result and primary_result.get("confidence_score", 0) >= 0.7:
                logger.info(f"✅ PRIMARY CLASSIFIER successful with high confidence: {primary_result.get('confidence_score', 0):.2f}")
                final_result = primary_result
                final_result["model_used"] = "SaulLM_Primary"
            else:
                # STEP 4: Try FALLBACK CLASSIFIER (Mistral)
                logger.info("🔄 Step 3: PRIMARY failed/low confidence, trying FALLBACK CLASSIFIER (Mistral)")
                fallback_result = self._classify_with_fallback(document_text, rag_context, filename)
                
                if fallback_result and fallback_result.get("confidence_score", 0) >= 0.6:
                    logger.info(f"✅ FALLBACK CLASSIFIER successful: {fallback_result.get('confidence_score', 0):.2f}")
                    final_result = fallback_result
                    final_result["model_used"] = "Mistral_Fallback"
                else:
                    # STEP 5: Use enhanced pattern-based fallback
                    logger.info("🔄 Step 4: Both models failed, using enhanced pattern-based classification")
                    final_result = self._fallback_classification(document_text, filename)
                    final_result["model_used"] = "Pattern_Based_Fallback"
            
            # STEP 6: Validate result with BART-MNLI zero-shot classifier
            logger.info("🔍 Step 5: Validating classification with BART-MNLI validator")
            validation_result = self._validate_with_bart(document_text, final_result)
            
            # STEP 7: Combine results and add enhanced metadata
            enhanced_result = self._combine_classification_results(
                final_result, validation_result, rag_context, filename
            )
            
            # STEP 8: Store processed document for future RAG context (preserve existing logic)
            if enhanced_result.get("doc_type") and enhanced_result.get("doc_category"):
                logger.info("💾 Step 6: Storing document in vector database for future RAG context")
                self.store_processed_document(
                    document_text, filename,
                    enhanced_result["doc_type"], enhanced_result["doc_category"],
                    enhanced_result.get("confidence", "Medium")
                )
            
            logger.info(f"🎯 3-Model classification complete: {enhanced_result.get('doc_type')} | {enhanced_result.get('doc_category')} | Confidence: {enhanced_result.get('confidence')}")
            return enhanced_result
            
        except Exception as e:
            logger.error(f"❌ Error in 3-model RAG classification: {e}")
            # Fallback to pattern-based classification
            fallback_result = self._fallback_classification(document_text, filename)
            fallback_result["model_used"] = "Emergency_Fallback"
            fallback_result["error"] = str(e)
            return fallback_result
    
    def _classify_with_primary(self, document_text: str, rag_context: Dict, filename: str) -> Dict:
        """
        PRIMARY CLASSIFIER: Use SaulLM (Equall/Saul-7B-Instruct-v1) for classification.
        This model is specialized for legal document understanding.
        """
        try:
            # Load primary classifier if not already loaded
            self._load_primary_classifier()
            
            if self.primary_model is None or self.primary_tokenizer is None:
                logger.warning("⚠️ Primary classifier (SaulLM) not available")
                return None
            
            # Build legal-specialized prompt for SaulLM
            prompt = self._build_saul_prompt(document_text, rag_context, filename)
            
            # Tokenize input
            inputs = self.primary_tokenizer(
                prompt, 
                return_tensors="pt", 
                max_length=2048,
                truncation=True,
                padding=True
            )
            
            # Move inputs to same device as model
            inputs = {k: v.to(self.primary_model.device) for k, v in inputs.items()}
            
            # Generate classification
            with torch.no_grad():
                outputs = self.primary_model.generate(
                    **inputs,
                    max_new_tokens=100,
                    temperature=0.1,
                    do_sample=True,
                    pad_token_id=self.primary_tokenizer.eos_token_id
                )
            
            # Decode response
            response = self.primary_tokenizer.decode(outputs[0], skip_special_tokens=True)
            
            # Extract classification from response (remove input prompt)
            classification_text = response[len(prompt):].strip()
            
            # Parse result
            result = self._parse_classification_result(classification_text)
            result["raw_response"] = classification_text
            result["model"] = "SaulLM_Primary"
            
            # Calculate confidence score based on response quality
            confidence_score = self._calculate_confidence_score(classification_text, result)
            result["confidence_score"] = confidence_score
            
            logger.info(f"✅ SaulLM classification: {result.get('doc_category')} | {result.get('doc_type')} | Confidence: {confidence_score:.2f}")
            
            return result
            
        except Exception as e:
            logger.error(f"❌ Error in SaulLM primary classification: {e}")
            return None
    
    def _build_rag_prompt(self, document_text: str, rag_context: Dict, filename: str) -> str:
        """Build enhanced prompt with RAG context using vector similarity results."""
        
        # Start building the prompt
        prompt = f"""You are an expert AI legal document classifier for a law firm specializing in U.S. immigration and criminal law. 

TASK: Analyze the document text and classify it using the exact format: "Category: [Category Name]; Type: [Document Type]"

DOCUMENT TO CLASSIFY:
Filename: {filename}
Text: {document_text[:2500]}

--- RAG CONTEXT FROM VECTOR DATABASE ---

SIMILAR CATEGORIES (based on semantic similarity):"""
        
        # Add similar categories from vector search
        if rag_context["similar_categories"]:
            for i, cat in enumerate(rag_context["similar_categories"][:3]):
                keywords = cat.get('keywords', [])
                if isinstance(keywords, list):
                    keywords_str = ', '.join(keywords[:8])
                else:
                    keywords_str = str(keywords)
                prompt += f"""
{i+1}. {cat['category']} (similarity: {cat['score']:.3f})
   Description: {cat['description']}
   Keywords: {keywords_str}"""
        else:
            prompt += "\nNo similar categories found in vector database."
        
        # Add similar examples from vector search
        prompt += f"\n\nSIMILAR CLASSIFICATION EXAMPLES (from vector database):"
        if rag_context["similar_examples"]:
            for i, example in enumerate(rag_context["similar_examples"][:3]):
                prompt += f"""
{i+1}. Text: {example['text'][:200]}...
   Classification: Category: {example['category']}; Type: {example['doc_type']}
   Similarity: {example['score']:.3f}"""
        else:
            prompt += "\nNo similar examples found in vector database."
        
        # Add similar processed documents
        if rag_context["similar_documents"]:
            prompt += f"\n\nSIMILAR PROCESSED DOCUMENTS:"
            for i, doc in enumerate(rag_context["similar_documents"][:2]):
                prompt += f"""
{i+1}. {doc['filename']} (similarity: {doc['score']:.3f})
   Previous classification: Category: {doc['doc_category']}; Type: {doc['doc_type']}"""
        
        # Add complete category and type lists
        prompt += f"""

--- COMPLETE CLASSIFICATION TAXONOMY ---

DOCUMENT CATEGORIES (choose exactly one):
"""
        for category in self.category_definitions.keys():
            prompt += f"- {category}\n"
        
        prompt += f"""
DOCUMENT TYPES (choose exactly one):
"""
        for doc_type in list(self.document_types.keys())[:25]:
            prompt += f"- {doc_type}\n"
        
        prompt += f"""

CLASSIFICATION INSTRUCTIONS:
1. Use the RAG context above to understand similar documents and categories
2. Consider the semantic similarity scores from the vector database
3. Match document content with the most appropriate category and type
4. Focus on immigration law (asylum, family, employment, deportation, etc.) or criminal law
5. Return EXACTLY this format: "Category: [Category Name]; Type: [Document Type]"

Based on the document content and RAG context above, classify this document:"""
        
        return prompt
    
    def _classify_with_fallback(self, document_text: str, rag_context: Dict, filename: str) -> Dict:
        """
        FALLBACK CLASSIFIER: Use Mistral (mistralai/Mistral-7B-Instruct-v0.3) for classification.
        Used when primary classifier fails or has low confidence.
        """
        try:
            # First try the existing Mistral API if available
            api_result = self._try_mistral_api(document_text, rag_context, filename)
            if api_result and api_result.get("confidence_score", 0) >= 0.6:
                api_result["model"] = "Mistral_API_Fallback"
                return api_result
            
            # If API fails, load local Mistral model
            self._load_fallback_classifier()
            
            if self.fallback_model is None or self.fallback_tokenizer is None:
                logger.warning("⚠️ Fallback classifier (Mistral) not available")
                return None
            
            # Build prompt for Mistral
            prompt = self._build_rag_prompt(document_text, rag_context, filename)
            
            # Tokenize input
            inputs = self.fallback_tokenizer(
                prompt,
                return_tensors="pt",
                max_length=2048, 
                truncation=True,
                padding=True
            )
            
            # Move inputs to same device as model
            inputs = {k: v.to(self.fallback_model.device) for k, v in inputs.items()}
            
            # Generate classification
            with torch.no_grad():
                outputs = self.fallback_model.generate(
                    **inputs,
                    max_new_tokens=100,
                    temperature=0.1,
                    do_sample=True,
                    pad_token_id=self.fallback_tokenizer.eos_token_id
                )
            
            # Decode response
            response = self.fallback_tokenizer.decode(outputs[0], skip_special_tokens=True)
            
            # Extract classification from response (remove input prompt)
            classification_text = response[len(prompt):].strip()
            
            # Parse result
            result = self._parse_classification_result(classification_text)
            result["raw_response"] = classification_text
            result["model"] = "Mistral_Local_Fallback"
            
            # Calculate confidence score
            confidence_score = self._calculate_confidence_score(classification_text, result)
            result["confidence_score"] = confidence_score
            
            logger.info(f"✅ Mistral classification: {result.get('doc_category')} | {result.get('doc_type')} | Confidence: {confidence_score:.2f}")
            
            return result
            
        except Exception as e:
            logger.error(f"❌ Error in Mistral fallback classification: {e}")
            return None
    
    def _try_mistral_api(self, document_text: str, rag_context: Dict, filename: str) -> Dict:
        """
        Try the existing Mistral API endpoint for backwards compatibility.
        """
        try:
            prompt = self._build_rag_prompt(document_text, rag_context, filename)
            
            response = requests.post(
                self.mistral_url,
                json={
                    "model": "mistral",
                    "messages": [{"role": "user", "content": prompt}],
                    "max_tokens": 150,
                    "temperature": 0.1
                },
                timeout=10
            )
            
            if response.status_code == 200:
                api_result = response.json()
                
                if "choices" in api_result and len(api_result["choices"]) > 0:
                    content = api_result["choices"][0]["message"]["content"].strip()
                    result = self._parse_classification_result(content)
                    result["raw_response"] = content
                    result["model"] = "Mistral_API"
                    
                    # Calculate confidence score
                    confidence_score = self._calculate_confidence_score(content, result)
                    result["confidence_score"] = confidence_score
                    
                    logger.info(f"✅ Mistral API classification: {result.get('doc_category')} | {result.get('doc_type')}")
                    return result
            
            return None
            
        except Exception as e:
            logger.debug(f"Mistral API not available: {e}")
            return None
    
    def _build_saul_prompt(self, document_text: str, rag_context: Dict, filename: str) -> str:
        """
        Build specialized prompt for SaulLM legal document classifier.
        SaulLM is trained on legal texts, so we use legal-specific language.
        """
        prompt = f"""<|im_start|>system
You are SaulLM, a specialized legal AI trained on legal documents. Classify this legal document into the appropriate immigration or criminal law category and document type.

<|im_end|>
<|im_start|>user
LEGAL DOCUMENT CLASSIFICATION TASK

Document: {filename}
Text: {document_text[:1500]}

CONTEXT FROM CASE DATABASE:"""
        
        # Add RAG context in legal format
        if rag_context["similar_categories"]:
            prompt += "\n\nSimilar Legal Categories:"
            for i, cat in enumerate(rag_context["similar_categories"][:2]):
                prompt += f"\n{i+1}. {cat['category']}: {cat['description'][:100]}..."
        
        if rag_context["similar_examples"]:
            prompt += "\n\nSimilar Case Examples:"
            for i, example in enumerate(rag_context["similar_examples"][:2]):
                prompt += f"\n{i+1}. {example['text'][:150]}... → {example['category']}"
        
        prompt += f"""

LEGAL CATEGORIES:
{', '.join(list(self.category_definitions.keys())[:10])}

DOCUMENT TYPES:
{', '.join(list(self.document_types.keys())[:15])}

Classify using EXACT format: "Category: [Category Name]; Type: [Document Type]"
<|im_end|>
<|im_start|assistant
"""
        
        return prompt

    def _fallback_classification(self, document_text: str, filename: str = "") -> Dict:
        """Enhanced pattern-based fallback classification with improved accuracy."""
        import re
        
        text_lower = document_text.lower().strip()
        filename_lower = filename.lower()
        
        # Enhanced document type patterns
        document_patterns = {
            "Witness Affidavit/Declaration": [
                r"affidavit", r"declaration", r"sworn\s+statement", r"under\s+penalty\s+of\s+perjury",
                r"being\s+duly\s+sworn", r"declare\s+that", r"hereby\s+declare"
            ],
            "Official Form/Application": [
                r"form\s+[a-zA-Z]?-?\d+", r"application\s+for", r"petition\s+for",
                r"i-\d+", r"n-\d+", r"ar-\d+", r"g-\d+"
            ],
            "General Correspondence": [
                r"letter", r"correspondence", r"memo", r"email", r"communication"
            ],
            "Medical Record/Report": [
                r"medical\s+record", r"medical\s+report", r"psychological\s+evaluation",
                r"doctor\s+report", r"health\s+record", r"medical\s+exam"
            ],
            "Notice to Appear (NTA)": [
                r"notice\s+to\s+appear", r"nta", r"removal\s+proceeding", r"immigration\s+court"
            ],
            "USCIS Receipt Notice": [
                r"receipt\s+notice", r"case\s+receipt", r"uscis\s+receipt", r"msc\d+"
            ],
            "USCIS Approval Notice": [
                r"approval\s+notice", r"approved", r"grant", r"petition\s+approved"
            ],
            "USCIS Request for Evidence (RFE)": [
                r"request\s+for\s+evidence", r"rfe", r"additional\s+evidence", r"further\s+evidence"
            ],
            "ID or Civil Document": [
                r"birth\s+certificate", r"passport", r"driver\s+license", r"marriage\s+certificate",
                r"divorce\s+decree", r"death\s+certificate"
            ],
            "Financial Document": [
                r"tax\s+return", r"bank\s+statement", r"employment\s+verification", r"pay\s+stub",
                r"income\s+statement", r"financial\s+support"
            ],
            "Criminal Complaint/Indictment": [
                r"criminal\s+complaint", r"indictment", r"charges", r"criminal\s+case"
            ],
            "Court Order/Judgment": [
                r"court\s+order", r"judgment", r"decree", r"ruling", r"decision"
            ],
            "Motion (Court Filing)": [
                r"motion\s+to", r"motion\s+for", r"petition\s+to", r"request\s+to\s+court"
            ],
            "Misc. Reference Material": [
                r"reference", r"supporting\s+document", r"evidence", r"exhibit"
            ]
        }
        
        # Category patterns for better classification
        category_patterns = {
            "Waivers of Inadmissibility": [
                r"i-601", r"waiver", r"inadmissibility", r"hardship", r"extreme\s+hardship"
            ],
            "Family-Sponsored Immigration": [
                r"family", r"spouse", r"marriage", r"i-130", r"relative\s+petition"
            ],
            "Removal & Deportation Defense": [
                r"removal", r"deportation", r"nta", r"immigration\s+court", r"defense"
            ],
            "Criminal Defense (Pretrial & Trial)": [
                r"criminal", r"charges", r"trial", r"defense", r"indictment"
            ],
            "Asylum & Refugee": [
                r"asylum", r"refugee", r"persecution", r"fear", r"i-589"
            ],
            "Employment-Based Immigration": [
                r"employment", r"work", r"job", r"labor", r"i-140", r"h-1b"
            ],
            "Naturalization & Citizenship": [
                r"citizenship", r"naturalization", r"n-400", r"citizen"
            ]
        }
        
        # Step 1: Document Type Classification (Priority-based)
        doc_type = "Misc. Reference Material"
        
        # 1. Affidavits/Declarations (high priority)
        if any(re.search(pattern, text_lower) for pattern in document_patterns["Witness Affidavit/Declaration"]):
            doc_type = "Witness Affidavit/Declaration"
        elif "affidavit" in filename_lower or "affd" in filename_lower:
            doc_type = "Witness Affidavit/Declaration"
        
        # 2. Medical documents
        elif any(re.search(pattern, text_lower) for pattern in document_patterns["Medical Record/Report"]):
            doc_type = "Medical Record/Report"
        elif any(term in filename_lower for term in ["medical", "psychological", "doctor", "health"]):
            doc_type = "Medical Record/Report"
        
        # 3. Forms and applications
        elif any(re.search(pattern, text_lower) for pattern in document_patterns["Official Form/Application"]):
            doc_type = "Official Form/Application"
        elif re.search(r"[ig]-\d+", filename_lower):
            doc_type = "Official Form/Application"
        
        # 4. Financial documents
        elif any(re.search(pattern, text_lower) for pattern in document_patterns["Financial Document"]):
            doc_type = "Financial Document"
        elif any(term in filename_lower for term in ["tax", "income", "bank", "employment", "pay", "bill"]):
            doc_type = "Financial Document"
        
        # 5. ID/Civil documents
        elif any(re.search(pattern, text_lower) for pattern in document_patterns["ID or Civil Document"]):
            doc_type = "ID or Civil Document"
        elif any(term in filename_lower for term in ["passport", "certificate", "birth", "marriage"]):
            doc_type = "ID or Civil Document"
        
        # 6. USCIS notices
        elif any(re.search(pattern, text_lower) for pattern in document_patterns["USCIS Receipt Notice"]):
            doc_type = "USCIS Receipt Notice"
        elif any(re.search(pattern, text_lower) for pattern in document_patterns["USCIS Approval Notice"]):
            doc_type = "USCIS Approval Notice"
        elif any(re.search(pattern, text_lower) for pattern in document_patterns["USCIS Request for Evidence (RFE)"]):
            doc_type = "USCIS Request for Evidence (RFE)"
        
        # 7. Court documents
        elif any(re.search(pattern, text_lower) for pattern in document_patterns["Motion (Court Filing)"]):
            doc_type = "Motion (Court Filing)"
        elif any(re.search(pattern, text_lower) for pattern in document_patterns["Court Order/Judgment"]):
            doc_type = "Court Order/Judgment"
        
        # 8. Correspondence
        elif any(re.search(pattern, text_lower) for pattern in document_patterns["General Correspondence"]):
            doc_type = "General Correspondence"
        elif any(term in filename_lower for term in ["letter", "cover"]):
            doc_type = "General Correspondence"
        
        # Step 2: Category Classification (Priority-based)
        doc_category = "Immigration Appeals & Motions"  # Default
        
        # 1. Waiver applications (I-601A context)
        if any(re.search(pattern, text_lower) for pattern in category_patterns["Waivers of Inadmissibility"]):
            doc_category = "Waivers of Inadmissibility"
        elif "601a" in filename_lower or "waiver" in filename_lower:
            doc_category = "Waivers of Inadmissibility"
        
        # 2. Family immigration (expanded patterns)
        elif any(re.search(pattern, text_lower) for pattern in category_patterns["Family-Sponsored Immigration"]):
            doc_category = "Family-Sponsored Immigration"
        elif any(term in filename_lower for term in ["family", "spouse", "marriage", "wife", "medical", "passport", "bill", "financial"]):
            doc_category = "Family-Sponsored Immigration"
        
        # 3. Criminal matters
        elif any(re.search(pattern, text_lower) for pattern in category_patterns["Criminal Defense (Pretrial & Trial)"]):
            doc_category = "Criminal Defense (Pretrial & Trial)"
        elif any(term in filename_lower for term in ["criminal", "disposition", "charges"]):
            doc_category = "Criminal Defense (Pretrial & Trial)"
        
        # 4. Removal/deportation
        elif any(re.search(pattern, text_lower) for pattern in category_patterns["Removal & Deportation Defense"]):
            doc_category = "Removal & Deportation Defense"
        elif any(term in filename_lower for term in ["nta", "removal", "deportation"]):
            doc_category = "Removal & Deportation Defense"
        
        # 5. Employment immigration
        elif any(re.search(pattern, text_lower) for pattern in category_patterns["Employment-Based Immigration"]):
            doc_category = "Employment-Based Immigration"
        elif any(term in filename_lower for term in ["employment", "work", "job"]):
            doc_category = "Employment-Based Immigration"
        
        # 6. Asylum
        elif any(re.search(pattern, text_lower) for pattern in category_patterns["Asylum & Refugee"]):
            doc_category = "Asylum & Refugee"
        
        # Default based on document type context
        elif doc_type in ["Witness Affidavit/Declaration", "Official Form/Application"]:
            doc_category = "Waivers of Inadmissibility"  # Most common in this context
        elif doc_type in ["Medical Record/Report", "Financial Document"]:
            doc_category = "Family-Sponsored Immigration"  # Supporting documents
        
        # Step 3: Confidence Assessment
        confidence_score = 0
        
        # Strong indicators boost confidence
        if doc_type == "Witness Affidavit/Declaration" and "affidavit" in filename_lower:
            confidence_score += 3
        if "601a" in filename_lower and doc_category == "Waivers of Inadmissibility":
            confidence_score += 3
        if "medical" in filename_lower and doc_type == "Medical Record/Report":
            confidence_score += 2
        
        # Text content matching
        if len([p for p in document_patterns.get(doc_type, []) if re.search(p, text_lower)]) >= 2:
            confidence_score += 2
        if len([p for p in category_patterns.get(doc_category, []) if re.search(p, text_lower)]) >= 1:
            confidence_score += 1
        
        # Return confidence level
        if confidence_score >= 4:
            confidence = "High"
        elif confidence_score >= 2:
            confidence = "Medium"
        else:
            confidence = "Low"

        return {
            "doc_type": doc_type,
            "doc_category": doc_category,
            "confidence": confidence,
            "rag_context": {"context_used": False, "method": "enhanced_pattern_based_fallback"}
        }
    
    def _parse_classification_result(self, content: str) -> Dict:
        """Parse classification result from Mistral response."""
        try:
            # Look for the expected format: "Category: [Category]; Type: [Type]"
            content = content.strip()
            
            # Initialize defaults
            doc_category = "Immigration Appeals & Motions"
            doc_type = "Misc. Reference Material"
            confidence = "Low"
            
            # Try to extract category and type
            if "Category:" in content and "Type:" in content:
                # Split on semicolon or newline
                parts = content.replace(";", "\n").split("\n")
                
                for part in parts:
                    part = part.strip()
                    if part.startswith("Category:"):
                        category_text = part.replace("Category:", "").strip()
                        # Check if it's a valid category
                        if category_text in self.category_definitions:
                            doc_category = category_text
                            confidence = "High"
                    elif part.startswith("Type:"):
                        type_text = part.replace("Type:", "").strip()
                        # Check if it's a valid document type
                        if type_text in self.document_types:
                            doc_type = type_text
                            if confidence == "High":
                                confidence = "High"
                            else:
                                confidence = "Medium"
            
            return {
                "doc_type": doc_type,
                "doc_category": doc_category,
                "confidence": confidence,
                "method": "mistral_rag_classification",
                "raw_response": content
            }
            
        except Exception as e:
            logger.error(f"Error parsing classification result: {e}")
            return {
                "doc_type": "Misc. Reference Material",
                "doc_category": "Immigration Appeals & Motions",
                "confidence": "Low",
                "method": "parse_error",
                "raw_response": content
            }
    
    def _classify_with_primary(self, document_text: str, rag_context: Dict, filename: str) -> Dict:
        """
        PRIMARY CLASSIFIER: Use SaulLM (Equall/Saul-7B-Instruct-v1) for classification.
        This model is specialized for legal document understanding.
        """
        try:
            # Load primary classifier if not already loaded
            self._load_primary_classifier()
            
            if self.primary_model is None or self.primary_tokenizer is None:
                logger.warning("⚠️ Primary classifier (SaulLM) not available")
                return None
            
            # Build legal-specialized prompt for SaulLM
            prompt = self._build_saul_prompt(document_text, rag_context, filename)
            
            # Tokenize input
            inputs = self.primary_tokenizer(
                prompt, 
                return_tensors="pt", 
                max_length=2048,
                truncation=True,
                padding=True
            )
            
            # Move inputs to same device as model
            inputs = {k: v.to(self.primary_model.device) for k, v in inputs.items()}
            
            # Generate classification
            with torch.no_grad():
                outputs = self.primary_model.generate(
                    **inputs,
                    max_new_tokens=100,
                    temperature=0.1,
                    do_sample=True,
                    pad_token_id=self.primary_tokenizer.eos_token_id
                )
            
            # Decode response
            response = self.primary_tokenizer.decode(outputs[0], skip_special_tokens=True)
            
            # Extract classification from response (remove input prompt)
            classification_text = response[len(prompt):].strip()
            
            # Parse result
            result = self._parse_classification_result(classification_text)
            result["raw_response"] = classification_text
            result["model"] = "SaulLM_Primary"
            
            # Calculate confidence score based on response quality
            confidence_score = self._calculate_confidence_score(classification_text, result)
            result["confidence_score"] = confidence_score
            
            logger.info(f"✅ SaulLM classification: {result.get('doc_category')} | {result.get('doc_type')} | Confidence: {confidence_score:.2f}")
            
            return result
            
        except Exception as e:
            logger.error(f"❌ Error in SaulLM primary classification: {e}")
            return None
    
    def _classify_with_fallback(self, document_text: str, rag_context: Dict, filename: str) -> Dict:
        """
        FALLBACK CLASSIFIER: Use Mistral (mistralai/Mistral-7B-Instruct-v0.3) for classification.
        Used when primary classifier fails or has low confidence.
        """
        try:
            # First try the existing Mistral API if available
            api_result = self._try_mistral_api(document_text, rag_context, filename)
            if api_result and api_result.get("confidence_score", 0) >= 0.6:
                api_result["model"] = "Mistral_API_Fallback"
                return api_result
            
            # If API fails, load local Mistral model
            self._load_fallback_classifier()
            
            if self.fallback_model is None or self.fallback_tokenizer is None:
                logger.warning("⚠️ Fallback classifier (Mistral) not available")
                return None
            
            # Build prompt for Mistral
            prompt = self._build_rag_prompt(document_text, rag_context, filename)
            
            # Tokenize input
            inputs = self.fallback_tokenizer(
                prompt,
                return_tensors="pt",
                max_length=2048, 
                truncation=True,
                padding=True
            )
            
            # Move inputs to same device as model
            inputs = {k: v.to(self.fallback_model.device) for k, v in inputs.items()}
            
            # Generate classification
            with torch.no_grad():
                outputs = self.fallback_model.generate(
                    **inputs,
                    max_new_tokens=100,
                    temperature=0.1,
                    do_sample=True,
                    pad_token_id=self.fallback_tokenizer.eos_token_id
                )
            
            # Decode response
            response = self.fallback_tokenizer.decode(outputs[0], skip_special_tokens=True)
            
            # Extract classification from response (remove input prompt)
            classification_text = response[len(prompt):].strip()
            
            # Parse result
            result = self._parse_classification_result(classification_text)
            result["raw_response"] = classification_text
            result["model"] = "Mistral_Local_Fallback"
            
            # Calculate confidence score
            confidence_score = self._calculate_confidence_score(classification_text, result)
            result["confidence_score"] = confidence_score
            
            logger.info(f"✅ Mistral classification: {result.get('doc_category')} | {result.get('doc_type')} | Confidence: {confidence_score:.2f}")
            
            return result
            
        except Exception as e:
            logger.error(f"❌ Error in Mistral fallback classification: {e}")
            return None
    
    def _try_mistral_api(self, document_text: str, rag_context: Dict, filename: str) -> Dict:
        """
        Try the existing Mistral API endpoint for backwards compatibility.
        """
        try:
            prompt = self._build_rag_prompt(document_text, rag_context, filename)
            
            response = requests.post(
                self.mistral_url,
                json={
                    "model": "mistral",
                    "messages": [{"role": "user", "content": prompt}],
                    "max_tokens": 150,
                    "temperature": 0.1
                },
                timeout=10
            )
            
            if response.status_code == 200:
                api_result = response.json()
                
                if "choices" in api_result and len(api_result["choices"]) > 0:
                    content = api_result["choices"][0]["message"]["content"].strip()
                    result = self._parse_classification_result(content)
                    result["raw_response"] = content
                    result["model"] = "Mistral_API"
                    
                    # Calculate confidence score
                    confidence_score = self._calculate_confidence_score(content, result)
                    result["confidence_score"] = confidence_score
                    
                    logger.info(f"✅ Mistral API classification: {result.get('doc_category')} | {result.get('doc_type')}")
                    return result
            
            return None
            
        except Exception as e:
            logger.debug(f"Mistral API not available: {e}")
            return None
    
    def _validate_with_bart(self, document_text: str, classification_result: Dict) -> Dict:
        """
        VALIDATOR: Use BART-MNLI for zero-shot validation of classification results.
        Provides additional confidence scoring and validation.
        """
        try:
            # Load validator if not already loaded
            self._load_validator()
            
            if self.validator_pipeline is None:
                logger.warning("⚠️ BART-MNLI validator not available")
                return {"validation_available": False}
            
            # Prepare category labels for zero-shot classification
            category_labels = list(self.category_definitions.keys())
            
            # Validate document category
            category_result = self.validator_pipeline(
                document_text[:1000],  # Limit text length
                category_labels,
                multi_label=False
            )
            
            # Prepare document type labels (subset for efficiency)
            doc_type_labels = [
                "Witness Affidavit/Declaration", "Official Form/Application", 
                "Medical Record/Report", "Financial Document", "ID or Civil Document",
                "USCIS Receipt Notice", "USCIS Approval Notice", "General Correspondence",
                "Motion (Court Filing)", "Court Order/Judgment", "Criminal Complaint/Indictment"
            ]
            
            # Validate document type
            doc_type_result = self.validator_pipeline(
                document_text[:1000],
                doc_type_labels,
                multi_label=False
            )
            
            # Extract validation results
            predicted_category = category_result["labels"][0]
            category_confidence = category_result["scores"][0]
            
            predicted_doc_type = doc_type_result["labels"][0] 
            doc_type_confidence = doc_type_result["scores"][0]
            
            # Check if validation agrees with classification
            category_match = predicted_category == classification_result.get("doc_category")
            doc_type_match = predicted_doc_type == classification_result.get("doc_type")
            
            validation_result = {
                "validation_available": True,
                "validator_category": predicted_category,
                "validator_doc_type": predicted_doc_type,
                "category_confidence": float(category_confidence),
                "doc_type_confidence": float(doc_type_confidence),
                "category_match": category_match,
                "doc_type_match": doc_type_match,
                "overall_validation_score": (category_confidence + doc_type_confidence) / 2
            }
            
            logger.info(f"🔍 BART validation: Category={predicted_category}({category_confidence:.2f}) | "
                       f"Type={predicted_doc_type}({doc_type_confidence:.2f}) | "
                       f"Matches: Cat={category_match}, Type={doc_type_match}")
            
            return validation_result
            
        except Exception as e:
            logger.error(f"❌ Error in BART-MNLI validation: {e}")
            return {"validation_available": False, "error": str(e)}
    
    def _build_saul_prompt(self, document_text: str, rag_context: Dict, filename: str) -> str:
        """
        Build specialized prompt for SaulLM legal document classifier.
        SaulLM is trained on legal texts, so we use legal-specific language.
        """
        prompt = f"""<|im_start|>system
You are SaulLM, a specialized legal AI trained on legal documents. Classify this legal document into the appropriate immigration or criminal law category and document type.

<|im_end|>
<|im_start|>user
LEGAL DOCUMENT CLASSIFICATION TASK

Document: {filename}
Text: {document_text[:1500]}

CONTEXT FROM CASE DATABASE:"""
        
        # Add RAG context in legal format
        if rag_context["similar_categories"]:
            prompt += "\n\nSimilar Legal Categories:"
            for i, cat in enumerate(rag_context["similar_categories"][:2]):
                prompt += f"\n{i+1}. {cat['category']}: {cat['description'][:100]}..."
        
        if rag_context["similar_examples"]:
            prompt += "\n\nSimilar Case Examples:"
            for i, example in enumerate(rag_context["similar_examples"][:2]):
                prompt += f"\n{i+1}. {example['text'][:150]}... → {example['category']}"
        
        prompt += f"""

LEGAL CATEGORIES:
{', '.join(list(self.category_definitions.keys())[:10])}

DOCUMENT TYPES:
{', '.join(list(self.document_types.keys())[:15])}

Classify using EXACT format: "Category: [Category Name]; Type: [Document Type]"
<|im_end|>
<|im_start|assistant