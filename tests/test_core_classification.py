#!/usr/bin/env python3
"""
Core Test for Enhanced 3-Model RAG Classification System

This test directly tests the classification pipeline with sample documents.
"""

import os
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

def test_direct_classification():
    """Test the enhanced classification system directly with sample documents"""
    print("🧪 ENHANCED 3-MODEL CLASSIFICATION CORE TEST")
    print("=" * 60)
    
    try:
        from core.enhanced_rag_classifier import EnhancedRAGClassifier
        
        # Initialize classifier
        print("🚀 Initializing Enhanced RAG Classifier...")
        classifier = EnhancedRAGClassifier()
        print("✅ Classifier initialized successfully")
        
        # Test documents
        test_documents = [
            {
                "filename": "i601a_waiver_packet.txt",
                "text": """
                I-601A Application for Provisional Unlawful Presence Waiver
                
                I am submitting this I-601A application to request a provisional waiver 
                of the unlawful presence grounds of inadmissibility. I understand that 
                this waiver is for individuals who can demonstrate extreme hardship to 
                a qualifying relative if the waiver is not granted.
                
                My qualifying relative is my U.S. citizen spouse who would face extreme 
                hardship if I am unable to return to the United States. The evidence 
                shows financial, emotional, and medical hardship.
                """
            },
            {
                "filename": "medical_evaluation.txt", 
                "text": """
                PSYCHOLOGICAL EVALUATION REPORT
                
                Patient: John Doe
                Date of Evaluation: November 15, 2024
                Psychologist: Dr. Jane Smith, Ph.D.
                
                CLINICAL INTERVIEW:
                The patient was referred for psychological evaluation in connection with 
                immigration proceedings. He reports symptoms of depression and anxiety 
                related to separation from family members.
                
                DIAGNOSIS:
                - Major Depressive Disorder, Moderate
                - Generalized Anxiety Disorder
                
                RECOMMENDATIONS:
                Continued therapy and medication management are recommended.
                """
            },
            {
                "filename": "asylum_application.txt",
                "text": """
                Form I-589, Application for Asylum and for Withholding of Removal
                
                I am applying for asylum in the United States because I have been 
                persecuted in my home country of [Country] on account of my political 
                opinion. I fear returning to my country because the government has 
                threatened my life due to my opposition activities.
                
                In 2023, I was detained and tortured by government forces for 
                participating in peaceful protests. I escaped and fled to the United States 
                seeking protection.
                """
            },
            {
                "filename": "court_motion.txt",
                "text": """
                MOTION TO CONTINUE HEARING
                
                TO THE HONORABLE IMMIGRATION JUDGE:
                
                Respondent, through undersigned counsel, respectfully moves this Court 
                for a continuance of the scheduled master calendar hearing currently 
                set for December 1, 2024.
                
                The basis for this motion is that additional time is needed to gather 
                evidence and prepare the case. Respondent's attorney needs more time 
                to obtain country condition evidence.
                
                WHEREFORE, Respondent respectfully requests this motion be granted.
                """
            },
            {
                "filename": "family_petition.txt",
                "text": """
                Form I-130, Petition for Alien Relative
                
                I am a U.S. citizen petitioning for my spouse who is currently residing 
                abroad. We were married on June 15, 2023, in a civil ceremony.
                
                Evidence submitted includes:
                - Marriage certificate
                - Birth certificates  
                - Photos from wedding
                - Joint bank account statements
                - Communication records
                
                We request approval of this petition so my spouse can immigrate to the United States.
                """
            }
        ]
        
        print(f"\n📄 Testing {len(test_documents)} sample documents...")
        print("-" * 60)
        
        results = []
        
        for i, doc in enumerate(test_documents, 1):
            print(f"\n📋 Document {i}: {doc['filename']}")
            
            try:
                # Classify using the enhanced system
                result = classifier.classify_with_rag(doc['text'], doc['filename'])
                
                # Display results
                category = result.get('doc_category', result.get('category', 'Unknown'))
                doc_type = result.get('doc_type', result.get('type', 'Unknown'))
                confidence = result.get('confidence', 'Unknown')
                confidence_score = result.get('confidence_score', 0.0)
                model_used = result.get('model_used', 'Unknown')
                
                print(f"   📊 Category: {category}")
                print(f"   📝 Type: {doc_type}")
                print(f"   🎯 Confidence: {confidence} ({confidence_score:.3f})")
                print(f"   🤖 Model: {model_used}")
                
                # Store result
                results.append({
                    'filename': doc['filename'],
                    'category': category,
                    'doc_type': doc_type,
                    'confidence': confidence,
                    'confidence_score': confidence_score,
                    'model_used': model_used,
                    'success': True
                })
                
                print(f"   ✅ Classification successful")
                
            except Exception as e:
                print(f"   ❌ Classification failed: {e}")
                results.append({
                    'filename': doc['filename'],
                    'error': str(e),
                    'success': False
                })
        
        # Summary
        print("\n" + "=" * 60)
        print("📊 CLASSIFICATION RESULTS SUMMARY")
        print("=" * 60)
        
        successful = sum(1 for r in results if r.get('success', False))
        total = len(results)
        
        print(f"✅ Successful classifications: {successful}/{total}")
        print(f"📈 Success rate: {successful/total*100:.1f}%")
        
        if successful > 0:
            # Show category distribution
            categories = {}
            models = {}
            
            for result in results:
                if result.get('success'):
                    cat = result.get('category', 'Unknown')
                    model = result.get('model_used', 'Unknown')
                    categories[cat] = categories.get(cat, 0) + 1
                    models[model] = models.get(model, 0) + 1
            
            print(f"\n🏷️  Categories found:")
            for cat, count in sorted(categories.items()):
                print(f"   {cat}: {count}")
            
            print(f"\n🤖 Models used:")
            for model, count in sorted(models.items()):
                print(f"   {model}: {count}")
        
        print("\n🎉 Core classification test completed!")
        return successful == total
        
    except Exception as e:
        print(f"💥 Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_direct_classification()
    print(f"\n{'🎯 TEST PASSED' if success else '❌ TEST FAILED'}")
    sys.exit(0 if success else 1)
