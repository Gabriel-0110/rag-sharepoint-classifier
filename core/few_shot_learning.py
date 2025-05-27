#!/usr/bin/env python3
"""
Few-Shot Learning Enhancement for RAG Classification
Implements few-shot examples as mentioned in PDF requirements.
"""

import json
import logging
from typing import Dict, List, Tuple
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class ClassificationExample:
    """Represents a few-shot classification example."""
    document_text: str
    document_type: str
    document_category: str
    reasoning: str = ""

class FewShotExampleManager:
    """Manages few-shot examples for classification enhancement."""
    
    def __init__(self):
        self.examples = self._initialize_examples()
    
    def _initialize_examples(self) -> Dict[str, List[ClassificationExample]]:
        """Initialize curated few-shot examples for each category."""
        
        examples = {
            "Corporate": [
                ClassificationExample(
                    document_text="STOCK PURCHASE AGREEMENT This Stock Purchase Agreement is entered into on March 15, 2024, between ABC Corporation, a Delaware corporation and XYZ Holdings LLC. The Purchaser agrees to purchase 1,000,000 shares of common stock at $10.50 per share. Terms and conditions include standard representations, warranties, and closing conditions typical for corporate transactions.",
                    document_type="Contract",
                    document_category="Corporate",
                    reasoning="Contains stock purchase terms, corporate entities, and transaction language"
                ),
                ClassificationExample(
                    document_text="BOARD OF DIRECTORS RESOLUTION WHEREAS, the Board of Directors of TechCorp Inc. has determined it necessary to approve the acquisition of StartupCo for consideration of $50M; NOW THEREFORE BE IT RESOLVED that the Board hereby approves and authorizes the CEO to execute all documents necessary to complete this acquisition.",
                    document_type="Corporate Document",
                    document_category="Corporate",
                    reasoning="Board resolution for corporate acquisition with formal whereas/resolved structure"
                )
            ],
            
            "Litigation": [
                ClassificationExample(
                    document_text="CIVIL ACTION NO. 2024-CV-1234 IN THE UNITED STATES DISTRICT COURT FOR THE DISTRICT OF DELAWARE Plaintiff XYZ Corp v. Defendant ABC Inc. COMPLAINT FOR PATENT INFRINGEMENT Plaintiff brings this action against Defendant for infringement of U.S. Patent No. 10,123,456 entitled 'Method for Data Processing'. COMES NOW Plaintiff and alleges as follows:",
                    document_type="Court Filing",
                    document_category="Litigation",
                    reasoning="Federal court case filing with case number, patent infringement claim, and formal legal pleading structure"
                ),
                ClassificationExample(
                    document_text="MOTION FOR SUMMARY JUDGMENT TO THE HONORABLE COURT: Defendant respectfully moves this Court for summary judgment pursuant to Rule 56 of the Federal Rules of Civil Procedure. There are no genuine issues of material fact and Defendant is entitled to judgment as a matter of law. Supporting memorandum is filed herewith.",
                    document_type="Court Filing",
                    document_category="Litigation",
                    reasoning="Legal motion with formal court address and Rule 56 reference indicating litigation proceeding"
                )
            ],
            
            "Contract": [
                ClassificationExample(
                    document_text="NON-DISCLOSURE AGREEMENT This Mutual Non-Disclosure Agreement is entered into between Company A and Company B for the purpose of evaluating a potential business relationship. Each party agrees to maintain in confidence all Confidential Information received from the other party. Term: 3 years from execution.",
                    document_type="Contract",
                    document_category="Corporate",
                    reasoning="Mutual NDA with confidentiality obligations and specific term period"
                ),
                ClassificationExample(
                    document_text="EMPLOYMENT AGREEMENT This Employment Agreement is between TechStart Inc. (Company) and John Smith (Employee). Position: Senior Software Engineer. Salary: $120,000 annually. Benefits include health insurance, 401k matching, and equity participation. At-will employment with 30-day notice period.",
                    document_type="Contract",
                    document_category="Employment",
                    reasoning="Employment contract with salary, benefits, and at-will terms"
                )
            ],
            
            "Employment": [
                ClassificationExample(
                    document_text="EMPLOYEE HANDBOOK - SECTION 4: HARASSMENT POLICY CompanyX maintains a zero-tolerance policy for harassment based on protected characteristics. All employees must complete annual training. Reporting procedures include direct supervisor, HR department, or anonymous hotline. Investigation procedures ensure confidentiality and non-retaliation.",
                    document_type="Corporate Document",
                    document_category="Employment",
                    reasoning="Employee handbook section covering workplace harassment policy and procedures"
                )
            ],
            
            "Intellectual Property": [
                ClassificationExample(
                    document_text="PATENT LICENSE AGREEMENT Licensor grants to Licensee a non-exclusive license to practice U.S. Patent No. 9,876,543 titled 'Advanced Neural Network Architecture' in the field of artificial intelligence. Royalty: 3.5% of net sales. Minimum annual royalty: $100,000. Territory: Worldwide excluding China.",
                    document_type="Contract",
                    document_category="Intellectual Property",
                    reasoning="Patent licensing agreement with specific patent number, royalty terms, and territorial restrictions"
                )
            ],
            
            "Real Estate": [
                ClassificationExample(
                    document_text="COMMERCIAL LEASE AGREEMENT Landlord: Downtown Properties LLC. Tenant: TechStartup Inc. Premises: 5,000 sq ft at 123 Business Park Drive, Suite 200. Term: 5 years commencing January 1, 2024. Base rent: $25/sq ft annually plus CAM charges. Security deposit: $20,833. Use: General office purposes only.",
                    document_type="Contract",
                    document_category="Real Estate",
                    reasoning="Commercial lease with specific square footage, rent terms, and property use restrictions"
                )
            ]
        }
        
        return examples
    
    def get_relevant_examples(self, predicted_category: str, max_examples: int = 2) -> List[ClassificationExample]:
        """Get relevant few-shot examples for a predicted category."""
        if predicted_category in self.examples:
            return self.examples[predicted_category][:max_examples]
        
        # If no direct match, return general examples
        all_examples = []
        for category_examples in self.examples.values():
            all_examples.extend(category_examples)
        
        return all_examples[:max_examples]
    
    def generate_few_shot_prompt(self, document_text: str, examples: List[ClassificationExample]) -> str:
        """Generate a few-shot prompt with examples."""
        
        prompt_parts = [
            "You are a legal document classification expert. Here are some examples:",
            ""
        ]
        
        # Add examples
        for i, example in enumerate(examples, 1):
            example_text = example.document_text[:300] + "..." if len(example.document_text) > 300 else example.document_text
            prompt_parts.extend([
                f"Example {i}:",
                f"Document: {example_text}",
                f"Classification: Type: {example.document_type}, Category: {example.document_category}",
                f"Reasoning: {example.reasoning}",
                ""
            ])
        
        # Add the actual document to classify
        doc_text = document_text[:1000] + "..." if len(document_text) > 1000 else document_text
        prompt_parts.extend([
            "Now classify this document:",
            f"Document: {doc_text}",
            "",
            "Provide classification in the format:",
            "Type: [Document Type]",
            "Category: [Document Category]",
            "Reasoning: [Brief explanation]"
        ])
        
        return "\n".join(prompt_parts)

class EnhancedClassificationPrompts:
    """Enhanced prompts with few-shot learning and confidence scoring."""
    
    def __init__(self):
        self.few_shot_manager = FewShotExampleManager()
    
    def create_enhanced_prompt(self, document_text: str, context_info: Dict = None) -> str:
        """Create an enhanced classification prompt with context and examples."""
        
        # Basic classification instruction
        base_prompt = """You are a legal document classification expert. Classify documents into:

Document Types: Contract, Legal Memo, Court Filing, Correspondence, Legal Opinion, Regulatory Document, Corporate Document, Financial Document

Document Categories: Corporate, Litigation, Contract, Employment, Intellectual Property, Real Estate, Immigration, Criminal Justice, Family Law, Tax

"""
        
        # Add context if available (from RAG retrieval)
        if context_info and context_info.get('similar_categories'):
            base_prompt += f"\nBased on similar documents, this appears related to: {', '.join(context_info['similar_categories'])}\n"
        
        # For very important classifications, add few-shot examples
        if context_info and context_info.get('use_few_shot', False):
            predicted_category = context_info.get('predicted_category', 'Corporate')
            examples = self.few_shot_manager.get_relevant_examples(predicted_category, max_examples=1)
            
            if examples:
                return self.few_shot_manager.generate_few_shot_prompt(document_text, examples)
        
        # Standard prompt
        doc_text = document_text[:2000] + "..." if len(document_text) > 2000 else document_text
        
        prompt = f"""{base_prompt}

Document to classify:
{doc_text}

Provide your classification with confidence level:
Type: [Document Type]
Category: [Document Category] 
Confidence: [High/Medium/Low]
Reasoning: [Brief explanation]"""
        
        return prompt
    
    def parse_enhanced_response(self, response: str) -> Dict:
        """Parse the enhanced response including confidence and reasoning."""
        result = {
            'document_type': 'Unknown',
            'document_category': 'Other',
            'confidence': 'Low',
            'reasoning': ''
        }
        
        lines = response.strip().split('\n')
        
        for line in lines:
            line = line.strip()
            if line.startswith('Type:'):
                result['document_type'] = line.replace('Type:', '').strip()
            elif line.startswith('Category:'):
                result['document_category'] = line.replace('Category:', '').strip()
            elif line.startswith('Confidence:'):
                result['confidence'] = line.replace('Confidence:', '').strip()
            elif line.startswith('Reasoning:'):
                result['reasoning'] = line.replace('Reasoning:', '').strip()
        
        return result

# Global instance
enhanced_prompts = EnhancedClassificationPrompts()

def create_enhanced_classification_prompt(document_text: str, context_info: Dict = None) -> str:
    """Create an enhanced prompt with few-shot learning."""
    return enhanced_prompts.create_enhanced_prompt(document_text, context_info)

def parse_enhanced_classification_response(response: str) -> Dict:
    """Parse enhanced classification response."""
    return enhanced_prompts.parse_enhanced_response(response)

if __name__ == "__main__":
    # Test few-shot examples
    test_doc = "MERGER AGREEMENT between ABC Corp and XYZ Inc for $500M transaction..."
    context = {'use_few_shot': True, 'predicted_category': 'Corporate'}
    
    prompt = create_enhanced_classification_prompt(test_doc, context)
    print("Enhanced Few-Shot Prompt:")
    print("=" * 50)
    print(prompt)
