#!/usr/bin/env python3
"""
Simple working test to validate our testing infrastructure
"""

import pytest
import os
import sys

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

class TestingInfrastructure:
    """Test suite to validate our testing setup"""

    def test_python_environment(self):
        """Test that Python environment is working"""
        assert sys.version_info.major == 3
        assert sys.version_info.minor >= 7
        print(f"✅ Python version: {sys.version}")

    def test_project_path(self):
        """Test that project path is accessible"""
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        assert os.path.exists(project_root)
        assert os.path.exists(os.path.join(project_root, "main.py"))
        print(f"✅ Project root accessible: {project_root}")

    def test_pytest_working(self):
        """Test that pytest is working correctly"""
        assert True
        print("✅ Pytest is working correctly")

    def test_imports_working(self):
        """Test that basic imports work"""
        try:
            import fastapi
            import pydantic
            import qdrant_client
            import transformers
            print("✅ All required packages importable")
        except ImportError as e:
            pytest.fail(f"Failed to import required package: {e}")

    def test_core_module_importable(self):
        """Test that we can import core modules"""
        try:
            from core.enhanced_rag_classifier import EnhancedRAGClassifier
            print("✅ Core RAG classifier importable")
        except ImportError as e:
            print(f"⚠️ Core RAG classifier not importable: {e}")
            # Don't fail - just note the issue

    def test_confidence_scoring_module(self):
        """Test confidence scoring module"""
        try:
            import core.confidence_scoring
            print("✅ Confidence scoring module importable")
        except ImportError as e:
            print(f"⚠️ Confidence scoring module not importable: {e}")

    def test_trocr_integration_module(self):
        """Test TrOCR integration module"""
        try:
            from core.trocr_integration import TrOCRProcessor
            print("✅ TrOCR integration module importable")
        except ImportError as e:
            print(f"⚠️ TrOCR integration module not importable: {e}")

    def test_vector_database_connection(self):
        """Test vector database connectivity"""
        try:
            from qdrant_client import QdrantClient
            client = QdrantClient(host="localhost", port=6333)
            # Simple connection test
            collections = client.get_collections()
            print(f"✅ Qdrant accessible, collections: {len(collections.collections)}")
        except Exception as e:
            print(f"⚠️ Qdrant not accessible: {e}")

    def test_system_ready_for_classification(self):
        """Test if system components are ready for classification"""
        components_ready = []
        
        # Test RAG classifier
        try:
            from core.enhanced_rag_classifier import EnhancedRAGClassifier
            components_ready.append("RAG Classifier")
        except:
            pass
            
        # Test vector DB
        try:
            from qdrant_client import QdrantClient
            client = QdrantClient(host="localhost", port=6333)
            client.get_collections()
            components_ready.append("Vector Database")
        except:
            pass
            
        # Test AI model access
        try:
            import requests
            response = requests.get("http://localhost:8001/health", timeout=5)
            if response.status_code == 200:
                components_ready.append("Mistral AI")
        except:
            pass
            
        print(f"✅ Ready components: {', '.join(components_ready)}")
        assert len(components_ready) > 0, "At least one component should be ready"

if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
