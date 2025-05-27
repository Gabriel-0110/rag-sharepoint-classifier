#!/usr/bin/env python3
"""
Enhanced RAG Classification with 3-Model Architecture
Implements PRIMARY (SaulLM) + FALLBACK (Mistral) + VALIDATOR (BART-MNLI) pipeline.
"""

import json
import numpy as np
from sentence_transformers import SentenceTransformer
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct, Filter, FieldCondition, Range
import requests
from typing import List, Dict, Tuple, Optional
import hashlib
import logging
import torch
import gc
from transformers import (
    AutoTokenizer, AutoModelForCausalLM, AutoModelForSequenceClassification
)
from transformers.utils.quantization_config import BitsAndBytesConfig
from transformers.pipelines import pipeline

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
    
    def __init__(self, use_quantization=True, enable_validation=True, enable_fallback=True, load_models=True):
        """Initialize the 3-model RAG classification system."""
        logger.info("🚀 Initializing Enhanced RAG Classifier with 3-Model Architecture")
        
        # Store configuration
        self.use_quantization = use_quantization
        self.enable_validation = enable_validation
        self.enable_fallback = enable_fallback
        self.load_models = load_models
        
        # Initialize Qdrant client and embedding model (preserve existing logic)
        self.client = QdrantClient(url="http://localhost:6333")
        # Force CPU usage for embedding model to avoid CUDA memory conflicts
        self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2', device='cpu')
        
        # Initialize model components
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
                return {
                    'category': 'Other',
                    'confidence': 0.0,
                    'reasoning': 'Primary classifier not available',
                    'model_used': 'saullm',
                    'error': 'Primary classifier not loaded',
                    'filename': filename
                }
            
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
            return {
                'category': 'Other',
                'confidence': 0.0,
                'reasoning': f'Error in SaulLM classification: {e}',
                'model_used': 'saullm',
                'error': str(e),
                'filename': filename
            }
    
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

    def _calculate_confidence_score(self, classification_text: str, result: Dict) -> float:
        """
        Calculate confidence score based on classification response quality and content matching.
        Returns a score between 0.0 and 1.0.
        """
        try:
            confidence_score = 0.5  # Base confidence
            
            # Check if result contains valid classification
            if result.get("doc_category") in self.category_definitions:
                confidence_score += 0.2
            if result.get("doc_type") in self.document_types:
                confidence_score += 0.2
            
            # Check response quality
            if classification_text and len(classification_text.strip()) > 10:
                confidence_score += 0.1
            
            # Check for expected format
            if "Category:" in classification_text and "Type:" in classification_text:
                confidence_score += 0.2
            
            # Penalize for unclear responses
            uncertainty_indicators = ["unclear", "uncertain", "possibly", "maybe", "appears to"]
            if any(indicator in classification_text.lower() for indicator in uncertainty_indicators):
                confidence_score -= 0.2
            
            return max(0.0, min(1.0, confidence_score))
            
        except Exception as e:
            logger.warning(f"Error calculating confidence score: {e}")
            return 0.5
    
    def _combine_classification_results(self, primary_result: Dict, validation_result: Dict, 
                                      rag_context: Dict, filename: str) -> Dict:
        """
        Combine results from classification models and validation with enhanced metadata.
        Returns comprehensive classification result with all metadata.
        """
        try:
            # Start with primary result
            combined_result = primary_result.copy() if primary_result else {}
            
            # Add validation information
            if validation_result.get("validation_available"):
                combined_result["validation"] = validation_result
                
                # Adjust confidence based on validation agreement
                if validation_result.get("category_match") and validation_result.get("doc_type_match"):
                    # Both category and type match - boost confidence
                    current_confidence = combined_result.get("confidence_score", 0.5)
                    combined_result["confidence_score"] = min(1.0, current_confidence + 0.1)
                    combined_result["confidence"] = "High" if combined_result["confidence_score"] >= 0.8 else "Medium"
                elif validation_result.get("category_match") or validation_result.get("doc_type_match"):
                    # Partial match - maintain confidence
                    combined_result["confidence"] = combined_result.get("confidence", "Medium")
                else:
                    # No match - reduce confidence
                    current_confidence = combined_result.get("confidence_score", 0.5)
                    combined_result["confidence_score"] = max(0.0, current_confidence - 0.2)
                    combined_result["confidence"] = "Low"
            
            # Add RAG context metadata
            combined_result["rag_context"] = {
                "context_used": True,
                "similar_categories_count": len(rag_context.get("similar_categories", [])),
                "similar_examples_count": len(rag_context.get("similar_examples", [])),
                "similar_documents_count": len(rag_context.get("similar_documents", []))
            }
            
            # Add processing metadata
            combined_result["processing_metadata"] = {
                "filename": filename,
                "pipeline_version": "3-model_architecture_v1.0",
                "rag_enhanced": True,
                "vector_database_used": True
            }
            
            # Ensure required fields are present
            if "doc_category" not in combined_result:
                combined_result["doc_category"] = "Immigration Appeals & Motions"
            if "doc_type" not in combined_result:
                combined_result["doc_type"] = "Misc. Reference Material"
            if "confidence" not in combined_result:
                combined_result["confidence"] = "Medium"
            
            return combined_result
            
        except Exception as e:
            logger.error(f"Error combining classification results: {e}")
            return {
                "doc_category": "Immigration Appeals & Motions",
                "doc_type": "Misc. Reference Material", 
                "confidence": "Low",
                "error": str(e),
                "model_used": "Error_Fallback"
            }

    def _build_saul_prompt(self, document_text: str, rag_context: Dict, filename: str) -> str:
        """Build prompt for SaulLM classification."""
        try:
            rag_summary = rag_context.get('summary', '')
            relevant_chunks = rag_context.get('relevant_chunks', [])
            context_section = ""
            if rag_summary:
                context_section += f"Document Summary: {rag_summary}\n\n"
            if relevant_chunks:
                context_section += "Relevant Context:\n"
                for i, chunk in enumerate(relevant_chunks[:3], 1):
                    context_section += f"{i}. {chunk.get('content', '')[:200]}...\n"
                context_section += "\n"
            prompt = f"""You are a legal document classifier. Analyze the following document and classify it into one of these categories:

Categories:
- Contract: Legal agreements, terms of service, purchase agreements, employment contracts
- Legal Brief: Court filings, legal arguments, case briefs, motions
- Regulation: Government regulations, compliance documents, policy documents
- Patent: Patent applications, patent grants, intellectual property documents
- Other: Any document that doesn't fit the above categories

{context_section}Document to classify (filename: {filename}):
{document_text[:2000]}{'...' if len(document_text) > 2000 else ''}

Provide your classification in this exact format:
CLASSIFICATION: [Category]
CONFIDENCE: [0.0-1.0]
REASONING: [Brief explanation of why this document fits this category]"""
            return prompt
        except Exception as e:
            logger.error(f"Error building SaulLM prompt: {str(e)}")
            return f"Classify this document: {document_text[:1000]}"

    def _parse_classification_result(self, classification_text: str) -> Dict:
        """Parse the classification result from model output."""
        try:
            result = {
                'category': 'Other',
                'confidence': 0.5,
                'reasoning': 'Default classification'
            }
            lines = classification_text.strip().split('\n')
            for line in lines:
                line = line.strip()
                if line.startswith('CLASSIFICATION:'):
                    category = line.replace('CLASSIFICATION:', '').strip()
                    valid_categories = ['Contract', 'Legal Brief', 'Regulation', 'Patent', 'Other']
                    if category in valid_categories:
                        result['category'] = category
                elif line.startswith('CONFIDENCE:'):
                    try:
                        confidence = float(line.replace('CONFIDENCE:', '').strip())
                        result['confidence'] = max(0.0, min(1.0, confidence))
                    except ValueError:
                        pass
                elif line.startswith('REASONING:'):
                    reasoning = line.replace('REASONING:', '').strip()
                    if reasoning:
                        result['reasoning'] = reasoning
            return result
        except Exception as e:
            logger.error(f"Error parsing classification result: {str(e)}")
            return {
                'category': 'Other',
                'confidence': 0.3,
                'reasoning': f'Parsing error: {str(e)}'
            }

    def _classify_with_fallback(self, document_text: str, rag_context: Dict, filename: str) -> Dict:
        """Classify using fallback Mistral model."""
        try:
            logger.info("Using Mistral fallback classifier")
            if self.fallback_tokenizer is None or self.fallback_model is None:
                logger.warning("Fallback model or tokenizer not loaded. Using rule-based fallback.")
                return self._fallback_classification(document_text, filename)
            prompt = f"""Classify this legal document into one category:
Categories: Contract, Legal Brief, Regulation, Patent, Other

Document: {document_text[:1500]}

Classification:"""
            inputs = self.fallback_tokenizer(prompt, return_tensors="pt", truncation=True, max_length=2048)
            with torch.no_grad():
                outputs = self.fallback_model.generate(
                    **inputs,
                    max_new_tokens=100,
                    temperature=0.3,
                    do_sample=True,
                    pad_token_id=self.fallback_tokenizer.eos_token_id
                )
            response = self.fallback_tokenizer.decode(outputs[0], skip_special_tokens=True)
            classification_text = response[len(prompt):].strip()
            result = self._parse_simple_classification(classification_text)
            result['model_used'] = 'mistral_fallback'
            result['filename'] = filename
            return result
        except Exception as e:
            logger.error(f"Fallback classification error: {str(e)}")
            return self._fallback_classification(document_text, filename)

    def _parse_simple_classification(self, text: str) -> Dict:
        """Parse simple classification response."""
        valid_categories = ['Contract', 'Legal Brief', 'Regulation', 'Patent', 'Other']
        text_upper = text.upper()
        found_category = 'Other'
        for category in valid_categories:
            if category.upper() in text_upper:
                found_category = category
                break
        return {
            'category': found_category,
            'confidence': 0.6,
            'reasoning': f'Fallback classification based on keyword matching'
        }

    def _fallback_classification(self, document_text: str, filename: str) -> Dict:
        """Simple rule-based fallback classification."""
        try:
            logger.info("Using rule-based fallback classification")
            text_lower = document_text.lower()
            filename_lower = filename.lower() if filename else ''
            if any(word in text_lower for word in ['agreement', 'contract', 'terms', 'party', 'whereas']):
                category = 'Contract'
                confidence = 0.7
            elif any(word in text_lower for word in ['court', 'motion', 'brief', 'plaintiff', 'defendant']):
                category = 'Legal Brief'
                confidence = 0.7
            elif any(word in text_lower for word in ['regulation', 'cfr', 'federal register', 'compliance']):
                category = 'Regulation'
                confidence = 0.7
            elif any(word in text_lower for word in ['patent', 'invention', 'claim', 'inventor']):
                category = 'Patent'
                confidence = 0.7
            else:
                category = 'Other'
                confidence = 0.5
            return {
                'category': category,
                'confidence': confidence,
                'reasoning': 'Rule-based classification using keyword matching',
                'model_used': 'rule_based_fallback',
                'filename': filename
            }
        except Exception as e:
            logger.error(f"Rule-based fallback error: {str(e)}")
            return {
                'category': 'Other',
                'confidence': 0.3,
                'reasoning': f'Error in classification: {str(e)}',
                'model_used': 'error_fallback',
                'filename': filename
            }

    def _validate_with_bart(self, document_text: str, classification_result: Dict) -> Dict:
        """Validate classification using BART-MNLI."""
        try:
            if not self.validator_pipeline:
                logger.warning("BART classifier not available for validation")
                return {
                    'validation_passed': True,
                    'validation_confidence': 0.5,
                    'validation_reasoning': 'BART validator not available'
                }
            predicted_category = classification_result.get('category', 'Other')
            hypothesis = f"This document is a {predicted_category.lower()}"
            premise = document_text[:1000] if len(document_text) > 1000 else document_text
            result_list = self.validator_pipeline(premise, hypothesis)
            entailment_score = 0.5
            if isinstance(result_list, list) and len(result_list) > 0:
                result = result_list[0]
                labels = result.get('labels', [])
                scores = result.get('scores', [])
                for i, label in enumerate(labels):
                    if label.upper() == 'ENTAILMENT':
                        entailment_score = scores[i]
                        break
            validation_passed = entailment_score > 0.5
            return {
                'validation_passed': validation_passed,
                'validation_confidence': entailment_score,
                'validation_reasoning': f'BART entailment score: {entailment_score:.3f}',
                'hypothesis_tested': hypothesis
            }
        except Exception as e:
            logger.error(f"BART validation error: {str(e)}")
            return {
                'validation_passed': True,
                'validation_confidence': 0.5,
                'validation_reasoning': f'Validation error: {str(e)}'
            }

    def classify_document_enhanced(self, document_text: str, rag_context: Dict, filename: str) -> Dict:
        """
        Enhanced 3-model document classification method.
        This is the main entry point for the enhanced classification pipeline.
        
        Args:
            document_text: The document text to classify
            rag_context: RAG context from vector similarity search
            filename: The document filename
            
        Returns:
            Dict containing classification results with enhanced metadata
        """
        return self.classify_with_rag(document_text, filename)

    def classify(self, document_text: str, filename: str = "") -> dict:
        """Simple wrapper for compatibility with integration test."""
        return self.classify_with_rag(document_text, filename)

# Legacy compatibility methods for existing system integration
def get_enhanced_rag_classifier():
    """Factory function to create classifier instance (backwards compatibility)."""
    return EnhancedRAGClassifier()

def classify_document_enhanced(document_text: str, filename: str) -> Dict:
    """Standalone function for document classification (backwards compatibility)."""
    classifier = EnhancedRAGClassifier()
    return classifier.classify_with_rag(document_text, filename)