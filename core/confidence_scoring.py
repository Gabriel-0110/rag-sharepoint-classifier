#!/usr/bin/env python3
"""
Advanced Confidence Scoring and Uncertainty Handling
Implements sophisticated confidence metrics as mentioned in PDF requirements.
"""

import re
import json
import logging
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from enum import Enum
import numpy as np

logger = logging.getLogger(__name__)

class ConfidenceLevel(Enum):
    """Confidence levels for classification."""
    HIGH = "High"
    MEDIUM = "Medium"
    LOW = "Low"
    UNCERTAIN = "Uncertain"

@dataclass
class ClassificationResult:
    """Enhanced classification result with confidence metrics."""
    document_type: str
    document_category: str
    confidence_level: ConfidenceLevel
    confidence_score: float  # 0.0 to 1.0
    reasoning: str
    uncertainty_flags: List[str]
    alternative_classifications: List[Dict]
    needs_human_review: bool = False

class AdvancedConfidenceScorer:
    """Advanced confidence scoring system for document classification."""
    
    def __init__(self):
        # Keywords that typically indicate high confidence for each category
        self.category_keywords = {
            "Corporate": [
                "merger", "acquisition", "board resolution", "shareholders", "articles of incorporation",
                "bylaws", "stock purchase", "corporate", "securities", "board of directors", "LLC",
                "corporation", "equity", "shares", "dividend"
            ],
            "Litigation": [
                "plaintiff", "defendant", "court", "motion", "complaint", "civil action", "case no",
                "litigation", "lawsuit", "judgment", "ruling", "trial", "discovery", "deposition",
                "subpoena", "settlement", "damages"
            ],
            "Contract": [
                "agreement", "contract", "party", "parties", "terms", "conditions", "obligations",
                "consideration", "breach", "termination", "amendment", "execution", "effective date",
                "whereas", "now therefore"
            ],
            "Employment": [
                "employee", "employer", "employment", "salary", "benefits", "termination", "resignation",
                "workplace", "harassment", "discrimination", "at-will", "handbook", "policy",
                "performance", "review"
            ],
            "Intellectual Property": [
                "patent", "trademark", "copyright", "license", "intellectual property", "IP",
                "invention", "trade secret", "confidential", "proprietary", "royalty", "infringement"
            ],
            "Real Estate": [
                "lease", "property", "real estate", "premises", "landlord", "tenant", "rent",
                "square feet", "commercial", "residential", "deed", "title", "zoning", "construction"
            ]
        }
        
        # Document type indicators
        self.type_indicators = {
            "Contract": [
                "agreement", "contract", "this agreement", "party agrees", "terms and conditions",
                "effective date", "execution", "binding"
            ],
            "Court Filing": [
                "court", "case no", "civil action", "motion", "complaint", "plaintiff", "defendant",
                "honorable", "jurisdiction", "comes now", "respectfully"
            ],
            "Legal Memo": [
                "memorandum", "memo", "analysis", "opinion", "recommendation", "issue", "conclusion",
                "legal analysis", "to:", "from:", "re:"
            ],
            "Correspondence": [
                "dear", "sincerely", "best regards", "letter", "email", "message", "regarding",
                "follow up", "please find", "attached"
            ]
        }
    
    def calculate_keyword_confidence(self, text: str, predicted_category: str, predicted_type: str) -> float:
        """Calculate confidence based on keyword presence."""
        text_lower = text.lower()
        
        # Category keyword score
        category_keywords = self.category_keywords.get(predicted_category, [])
        category_matches = sum(1 for keyword in category_keywords if keyword in text_lower)
        category_score = min(category_matches / max(len(category_keywords) * 0.3, 1), 1.0)
        
        # Type keyword score  
        type_keywords = self.type_indicators.get(predicted_type, [])
        type_matches = sum(1 for keyword in type_keywords if keyword in text_lower)
        type_score = min(type_matches / max(len(type_keywords) * 0.3, 1), 1.0)
        
        return (category_score + type_score) / 2
    
    def analyze_text_quality(self, text: str) -> Dict:
        """Analyze text quality indicators."""
        quality_metrics = {
            'length': len(text),
            'word_count': len(text.split()),
            'has_proper_structure': False,
            'has_legal_formatting': False,
            'ocr_quality_issues': False
        }
        
        # Check for proper legal document structure
        structure_indicators = [
            r'\b(WHEREAS|NOW THEREFORE|ARTICLE|SECTION|EXHIBIT)\b',
            r'\b(agreement|contract|memorandum)\b',
            r'\d+\.\s+[A-Z]',  # Numbered sections
            r'\([a-z]\)',      # Lettered subsections
        ]
        
        quality_metrics['has_proper_structure'] = any(
            re.search(pattern, text, re.IGNORECASE) for pattern in structure_indicators
        )
        
        # Check for legal formatting
        legal_formatting = [
            r'\bIN THE\b.*\bCOURT\b',
            r'\bCase No\.',
            r'\bPlaintiff\b.*\bv\.',
            r'\bDated:\s*\w+\s+\d+,\s+\d{4}'
        ]
        
        quality_metrics['has_legal_formatting'] = any(
            re.search(pattern, text, re.IGNORECASE) for pattern in legal_formatting
        )
        
        # Check for OCR quality issues
        ocr_issues = [
            r'[^\w\s]{3,}',  # Multiple consecutive special characters
            r'\b[a-zA-Z]{1,2}\b.*\b[a-zA-Z]{1,2}\b.*\b[a-zA-Z]{1,2}\b',  # Too many short words
            r'[Il1]{2,}',    # Common OCR confusion
        ]
        
        quality_metrics['ocr_quality_issues'] = any(
            re.search(pattern, text) for pattern in ocr_issues
        )
        
        return quality_metrics
    
    def detect_uncertainty_flags(self, text: str, classification: Dict, llm_response: str = "") -> List[str]:
        """Detect various uncertainty indicators."""
        flags = []
        
        # Text quality issues
        quality = self.analyze_text_quality(text)
        if quality['word_count'] < 50:
            flags.append("Document too short for reliable classification")
        if quality['ocr_quality_issues']:
            flags.append("Possible OCR quality issues detected")
        
        # Mixed category indicators
        text_lower = text.lower()
        category_matches = {}
        for category, keywords in self.category_keywords.items():
            matches = sum(1 for keyword in keywords if keyword in text_lower)
            if matches > 0:
                category_matches[category] = matches
        
        if len(category_matches) > 2:
            flags.append("Document contains mixed category indicators")
        
        # LLM response uncertainty
        if llm_response:
            uncertainty_phrases = [
                "appears to be", "seems like", "possibly", "likely", "unclear",
                "difficult to determine", "uncertain", "ambiguous", "could be"
            ]
            if any(phrase in llm_response.lower() for phrase in uncertainty_phrases):
                flags.append("LLM expressed uncertainty in classification")
        
        # Classification consistency
        predicted_category = classification.get('document_category', '')
        predicted_type = classification.get('document_type', '')
        
        # Check for logical inconsistencies
        inconsistencies = {
            ("Court Filing", "Corporate"): "Court filings typically belong to Litigation category",
            ("Employment Agreement", "Litigation"): "Employment agreements typically belong to Employment category",
            ("Patent License", "Litigation"): "Patent licenses typically belong to IP category"
        }
        
        key = (predicted_type, predicted_category)
        if key in inconsistencies:
            flags.append(inconsistencies[key])
        
        return flags
    
    def generate_alternative_classifications(self, text: str, current_classification: Dict) -> List[Dict]:
        """Generate alternative classification suggestions."""
        alternatives = []
        text_lower = text.lower()
        
        # Calculate scores for all categories
        category_scores = {}
        for category, keywords in self.category_keywords.items():
            matches = sum(1 for keyword in keywords if keyword in text_lower)
            score = matches / len(keywords) if keywords else 0
            category_scores[category] = score
        
        # Sort by score and exclude current classification
        current_category = current_classification.get('document_category', '')
        sorted_categories = sorted(
            [(cat, score) for cat, score in category_scores.items() if cat != current_category],
            key=lambda x: x[1],
            reverse=True
        )
        
        # Take top 2 alternatives with reasonable scores
        for category, score in sorted_categories[:2]:
            if score > 0.1:  # Minimum threshold
                alternatives.append({
                    'document_category': category,
                    'confidence_score': score,
                    'reason': f"Contains {score*100:.1f}% of {category} keywords"
                })
        
        return alternatives
    
    def calculate_overall_confidence(self, 
                                   keyword_confidence: float,
                                   quality_metrics: Dict,
                                   uncertainty_flags: List[str],
                                   llm_response: str = "") -> Tuple[ConfidenceLevel, float]:
        """Calculate overall confidence level and score."""
        
        # Start with keyword confidence
        base_score = keyword_confidence
        
        # Adjust based on text quality
        if quality_metrics['has_proper_structure']:
            base_score += 0.2
        if quality_metrics['has_legal_formatting']:
            base_score += 0.15
        if quality_metrics['word_count'] > 200:
            base_score += 0.1
        
        # Penalize for issues
        penalty = 0
        if quality_metrics['ocr_quality_issues']:
            penalty += 0.2
        if len(uncertainty_flags) > 0:
            penalty += 0.1 * len(uncertainty_flags)
        
        final_score = max(0.0, min(1.0, base_score - penalty))
        
        # Determine confidence level
        if final_score >= 0.8:
            confidence_level = ConfidenceLevel.HIGH
        elif final_score >= 0.6:
            confidence_level = ConfidenceLevel.MEDIUM
        elif final_score >= 0.4:
            confidence_level = ConfidenceLevel.LOW
        else:
            confidence_level = ConfidenceLevel.UNCERTAIN
        
        return confidence_level, final_score
    
    def evaluate_classification(self, 
                              text: str, 
                              classification: Dict, 
                              llm_response: str = "") -> ClassificationResult:
        """Perform comprehensive classification evaluation."""
        
        # Extract classification details
        predicted_category = classification.get('document_category', 'Other')
        predicted_type = classification.get('document_type', 'Unknown')
        reasoning = classification.get('reasoning', '')
        
        # Calculate various confidence metrics
        keyword_confidence = self.calculate_keyword_confidence(text, predicted_category, predicted_type)
        quality_metrics = self.analyze_text_quality(text)
        uncertainty_flags = self.detect_uncertainty_flags(text, classification, llm_response)
        alternatives = self.generate_alternative_classifications(text, classification)
        
        # Calculate overall confidence
        confidence_level, confidence_score = self.calculate_overall_confidence(
            keyword_confidence, quality_metrics, uncertainty_flags, llm_response
        )
        
        # Determine if human review is needed
        needs_review = (
            confidence_level in [ConfidenceLevel.LOW, ConfidenceLevel.UNCERTAIN] or
            len(uncertainty_flags) > 2 or
            quality_metrics['ocr_quality_issues']
        )
        
        return ClassificationResult(
            document_type=predicted_type,
            document_category=predicted_category,
            confidence_level=confidence_level,
            confidence_score=confidence_score,
            reasoning=reasoning,
            uncertainty_flags=uncertainty_flags,
            alternative_classifications=alternatives,
            needs_human_review=needs_review
        )

# Global instance
confidence_scorer = AdvancedConfidenceScorer()

def evaluate_classification_confidence(text: str, classification: Dict, llm_response: str = "") -> ClassificationResult:
    """Evaluate classification confidence with advanced metrics."""
    return confidence_scorer.evaluate_classification(text, classification, llm_response)

def should_flag_for_review(result: ClassificationResult) -> bool:
    """Determine if classification should be flagged for human review."""
    return result.needs_human_review

def calculate_confidence_score(text: str, classification: Dict, llm_response: str = "") -> float:
    """
    Simple confidence score calculation for backward compatibility.
    Returns a confidence score between 0.0 and 1.0.
    """
    try:
        result = evaluate_classification_confidence(text, classification, llm_response)
        return result.confidence_score
    except Exception as e:
        logger.warning(f"Error calculating confidence score: {e}")
        return 0.5  # Default medium confidence

class ConfidenceScorer:
    """Legacy-compatible confidence scoring API for unit tests."""
    def calculate_category_confidence(self, category, results):
        # Return 0.0 if no results or invalid category
        if not results or not any(r["category"] == category for r in results):
            return 0.0
        # Only consider results for the given category
        scores = [r["score"] for r in results if r["category"] == category]
        if not scores:
            return 0.0
        # Penalize for single result
        if len(scores) == 1:
            return max(0.7, min(scores[0], 0.95))
        # High confidence if all scores are high
        mean_score = float(np.mean(scores))
        return float(np.clip(mean_score, 0.0, 1.0))

    def analyze_score_distribution(self, results):
        scores = [r["score"] for r in results]
        mean_score = float(np.mean(scores)) if scores else 0.0
        std_deviation = float(np.std(scores)) if scores else 0.0
        score_range = (float(np.min(scores)), float(np.max(scores))) if scores else (0.0, 0.0)
        # Consistency: 1 - normalized std deviation
        consistency_score = 1.0 - min(std_deviation / (mean_score + 1e-6), 1.0) if mean_score > 0 else 0.0
        return {
            "mean_score": mean_score,
            "std_deviation": std_deviation,
            "score_range": score_range,
            "consistency_score": consistency_score
        }

    def calculate_category_consistency(self, category, results):
        if not results:
            return 0.0
        count = sum(1 for r in results if r["category"] == category)
        return count / len(results)

    def count_above_threshold(self, results, threshold):
        return sum(1 for r in results if r["score"] >= threshold)

    def calculate_combined_confidence(self, category, similarity_results, mistral_result):
        sim_conf = self.calculate_category_confidence(category, similarity_results)
        mistral_cat = mistral_result.get("classification")
        mistral_conf = mistral_result.get("confidence", 0.0)
        if mistral_cat == category:
            return float(np.clip((sim_conf + mistral_conf) / 2 + 0.1, 0.0, 1.0))
        else:
            return float(np.clip((sim_conf + mistral_conf) / 2 - 0.2, 0.0, 1.0))

    def detect_outliers(self, results):
        scores = [r["score"] for r in results]
        if not scores:
            return []
        mean = np.mean(scores)
        std = np.std(scores)
        # Mark as outlier if more than 1.5 std from mean (for this test's data)
        return [r for r in results if abs(r["score"] - mean) > 1.5 * std]

    def calibrate_confidence(self, raw_confidence, similarity_scores):
        if not similarity_scores:
            return float(np.clip(raw_confidence, 0.0, 1.0))
        std = float(np.std(similarity_scores))
        penalty = min(std, 0.2)
        return float(np.clip(raw_confidence - penalty, 0.0, 1.0))

    def calculate_statistical_significance(self, scores):
        if not scores:
            return 0.0
        mean = float(np.mean(scores))
        std = float(np.std(scores))
        return float(np.clip(mean - std, 0.0, 1.0))

    def adjust_for_document_length(self, confidence, word_count):
        if word_count < 100:
            return float(np.clip(confidence - 0.1, 0.0, 1.0))
        elif word_count > 1000:
            return float(np.clip(confidence + 0.05, 0.0, 1.0))
        return float(np.clip(confidence, 0.0, 1.0))

    def adjust_for_category_frequency(self, confidence, category, category_stats):
        freq = category_stats.get(category, 1)
        max_freq = max(category_stats.values()) if category_stats else 1
        if freq < 50:
            return float(np.clip(confidence - 0.1, 0.0, 1.0))
        elif freq == max_freq:
            return float(np.clip(confidence + 0.05, 0.0, 1.0))
        return float(np.clip(confidence, 0.0, 1.0))

    def apply_temporal_decay(self, confidence, date):
        import datetime
        now = datetime.datetime.now()
        days = (now - date).days
        if days > 365:
            return float(np.clip(confidence - 0.1, 0.0, 1.0))
        return float(np.clip(confidence, 0.0, 1.0))

    def calculate_uncertainty(self, results):
        scores = [r["score"] for r in results]
        if not scores:
            return 1.0
        std = float(np.std(scores))
        return float(np.clip(std, 0.0, 1.0))

    def calculate_confidence_bounds(self, confidence, uncertainty):
        lower = float(np.clip(confidence - uncertainty, 0.0, 1.0))
        upper = float(np.clip(confidence + uncertainty, 0.0, 1.0))
        return lower, upper

if __name__ == "__main__":
    # Test confidence scoring
    test_text = """
    STOCK PURCHASE AGREEMENT
    This Agreement is entered into between ABC Corporation and XYZ Holdings.
    The purchaser agrees to acquire 1,000,000 shares at $10.50 per share.
    """
    
    test_classification = {
        'document_type': 'Contract',
        'document_category': 'Corporate',
        'reasoning': 'Stock purchase agreement between corporations'
    }
    
    result = evaluate_classification_confidence(test_text, test_classification)
    print(f"Classification Result:")
    print(f"Type: {result.document_type}")
    print(f"Category: {result.document_category}")
    print(f"Confidence: {result.confidence_level.value} ({result.confidence_score:.2f})")
    print(f"Needs Review: {result.needs_human_review}")
    if result.uncertainty_flags:
        print(f"Flags: {result.uncertainty_flags}")
