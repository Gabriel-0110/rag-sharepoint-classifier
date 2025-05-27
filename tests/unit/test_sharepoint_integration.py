#!/usr/bin/env python3
"""
Comprehensive tests for SharePoint Integration
"""

import pytest
import os
import sys
import tempfile
import json
from unittest.mock import Mock, patch, MagicMock
import requests

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from core.sharepoint_processor import SharePointProcessor
from core import sharepoint_integration
class TestSharePointIntegration:
    """Test suite for SharePoint integration functionality"""
    
    @pytest.fixture
    def mock_credentials(self):
        """Mock SharePoint credentials"""
        return {
            'tenant_id': 'test-tenant-id',
            'client_id': 'test-client-id', 
            'client_secret': 'test-client-secret',
            'site_url': 'https://testcompany.sharepoint.com/sites/LegalServices'
        }
    
    @pytest.fixture
    def processor(self, mock_credentials):
        """Create SharePoint processor with mocked authentication"""
        with patch('core.sharepoint_processor.ConfidentialClientApplication'), \
             patch.dict(os.environ, {
                 'AZURE_TENANT_ID': mock_credentials['tenant_id'],
                 'AZURE_CLIENT_ID': mock_credentials['client_id'],
                 'AZURE_CLIENT_SECRET': mock_credentials['client_secret']
             }):
            return SharePointProcessor()
    
    @pytest.fixture
    def mock_token_response(self):
        """Mock successful token response"""
        return {
            'access_token': 'mock-access-token',
            'token_type': 'Bearer',
            'expires_in': 3600
        }
    
    @pytest.fixture
    def mock_site_response(self):
        """Mock SharePoint site response"""
        return {
            'id': 'test-site-id',
            'name': 'Legal Services',
            'webUrl': 'https://testcompany.sharepoint.com/sites/LegalServices'
        }
    
    @pytest.fixture
    def mock_documents(self):
        """Mock SharePoint documents list"""
        return [
            {
                'id': 'doc1',
                'name': 'immigration_petition.pdf',
                'file': {'mimeType': 'application/pdf'},
                'size': 150000,
                'lastModifiedDateTime': '2025-05-26T10:00:00Z',
                '@microsoft.graph.downloadUrl': 'https://mock-download-url1.com'
            },
            {
                'id': 'doc2', 
                'name': 'criminal_motion.docx',
                'file': {'mimeType': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'},
                'size': 95000,
                'lastModifiedDateTime': '2025-05-26T11:30:00Z',
                '@microsoft.graph.downloadUrl': 'https://mock-download-url2.com'
            },
            {
                'id': 'doc3',
                'name': 'civil_complaint.pdf',
                'file': {'mimeType': 'application/pdf'},
                'size': 200000,
                'lastModifiedDateTime': '2025-05-26T14:15:00Z',
                '@microsoft.graph.downloadUrl': 'https://mock-download-url3.com'
            }
        ]
    
    def test_processor_initialization(self, processor):
        """Test SharePoint processor initialization"""
        assert processor is not None
        assert hasattr(processor, 'app')
        assert hasattr(processor, 'site_id')
    
    @patch('core.sharepoint_processor.ConfidentialClientApplication')
    def test_authentication_success(self, mock_app, processor, mock_token_response):
        """Test successful SharePoint authentication"""
        mock_client = Mock()
        mock_client.acquire_token_for_client.return_value = mock_token_response
        mock_app.return_value = mock_client
        
        token = processor.authenticate()
        
        assert token == 'mock-access-token'
        mock_client.acquire_token_for_client.assert_called_once()
    
    @patch('core.sharepoint_processor.ConfidentialClientApplication')
    def test_authentication_failure(self, mock_app, processor):
        """Test SharePoint authentication failure"""
        mock_client = Mock()
        mock_client.acquire_token_for_client.return_value = {'error': 'invalid_client'}
        mock_app.return_value = mock_client
        
        with pytest.raises(Exception):
            processor.authenticate()
    
    @patch('requests.get')
    def test_get_site_info(self, mock_get, processor, mock_site_response):
        """Test getting SharePoint site information"""
        mock_response = Mock()
        mock_response.json.return_value = mock_site_response
        mock_response.status_code = 200
        mock_get.return_value = mock_response
        
        processor.access_token = 'mock-token'
        site_info = processor.get_site_info()
        
        assert site_info['id'] == 'test-site-id'
        assert site_info['name'] == 'Legal Services'
        mock_get.assert_called_once()
    
    @patch('requests.get')
    def test_list_documents(self, mock_get, processor, mock_documents):
        """Test listing documents from SharePoint"""
        mock_response = Mock()
        mock_response.json.return_value = {'value': mock_documents}
        mock_response.status_code = 200
        mock_get.return_value = mock_response
        
        processor.access_token = 'mock-token'
        processor.site_id = 'test-site-id'
        
        documents = processor.list_documents()
        
        assert len(documents) == 3
        assert documents[0]['name'] == 'immigration_petition.pdf'
        assert documents[1]['name'] == 'criminal_motion.docx'
        assert documents[2]['name'] == 'civil_complaint.pdf'
    
    @patch('requests.get')
    def test_download_document(self, mock_get, processor):
        """Test downloading a document from SharePoint"""
        # Mock document content response
        mock_response = Mock()
        mock_response.content = b'Mock PDF content'
        mock_response.status_code = 200
        mock_get.return_value = mock_response
        
        processor.access_token = 'mock-token'
        
        content = processor.download_document('https://mock-download-url.com')
        
        assert content == b'Mock PDF content'
        mock_get.assert_called_once()
    
    def test_filter_documents_by_type(self, processor, mock_documents):
        """Test filtering documents by file type"""
        pdf_docs = processor.filter_documents_by_type(mock_documents, 'pdf')
        docx_docs = processor.filter_documents_by_type(mock_documents, 'docx')
        
        assert len(pdf_docs) == 2
        assert len(docx_docs) == 1
        assert all('.pdf' in doc['name'] for doc in pdf_docs)
        assert all('.docx' in doc['name'] for doc in docx_docs)
    
    def test_filter_documents_by_date(self, processor, mock_documents):
        """Test filtering documents by modification date"""
        from datetime import datetime, timedelta
        
        cutoff_date = datetime.now() - timedelta(days=1)
        recent_docs = processor.filter_documents_by_date(mock_documents, cutoff_date)
        
        # All mock documents should be recent (created with today's date)
        assert len(recent_docs) == 3
    
    def test_filter_documents_by_size(self, processor, mock_documents):
        """Test filtering documents by file size"""
        # Filter documents larger than 100KB
        large_docs = processor.filter_documents_by_size(mock_documents, min_size=100000)
        
        assert len(large_docs) == 2  # immigration_petition.pdf and civil_complaint.pdf
        assert all(doc['size'] >= 100000 for doc in large_docs)
    
    @patch('core.sharepoint_processor.os.makedirs')
    @patch('builtins.open', create=True)
    def test_save_document_locally(self, mock_open, mock_makedirs, processor):
        """Test saving downloaded document locally"""
        mock_file = Mock()
        mock_open.return_value.__enter__.return_value = mock_file
        
        content = b'Document content'
        filename = 'test_document.pdf'
        
        saved_path = processor.save_document_locally(content, filename)
        
        assert filename in saved_path
        mock_file.write.assert_called_once_with(content)
    
    @patch('requests.post')
    def test_upload_document(self, mock_post, processor):
        """Test uploading a document to SharePoint"""
        mock_response = Mock()
        mock_response.json.return_value = {'id': 'uploaded-doc-id'}
        mock_response.status_code = 201
        mock_post.return_value = mock_response
        
        processor.access_token = 'mock-token'
        processor.site_id = 'test-site-id'
        
        file_content = b'New document content'
        filename = 'new_document.pdf'
        
        result = processor.upload_document(file_content, filename)
        
        assert result['id'] == 'uploaded-doc-id'
        mock_post.assert_called_once()
    
    @patch('requests.patch')
    def test_update_document_metadata(self, mock_patch, processor):
        """Test updating document metadata in SharePoint"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_patch.return_value = mock_response
        
        processor.access_token = 'mock-token'
        processor.site_id = 'test-site-id'
        
        metadata = {
            'classification': 'Immigration',
            'confidence': 0.85,
            'processed_date': '2025-05-26T15:30:00Z'
        }
        
        result = processor.update_document_metadata('doc-id', metadata)
        
        assert result is True
        mock_patch.assert_called_once()
    
    def test_batch_download_processing(self, processor, mock_documents):
        """Test batch downloading and processing of documents"""
        # Mock individual download and classification
        processor.download_document = Mock(side_effect=[
            b'PDF content 1',
            b'DOCX content 2',
            b'PDF content 3'
        ])
        
        processor.classify_document_content = Mock(side_effect=[
            {'classification': 'Immigration', 'confidence': 0.9},
            {'classification': 'Criminal', 'confidence': 0.85},
            {'classification': 'Civil', 'confidence': 0.8}
        ])
        
        results = processor.process_documents_batch(mock_documents)
        
        assert len(results) == 3
        assert results[0]['classification'] == 'Immigration'
        assert results[1]['classification'] == 'Criminal'
        assert results[2]['classification'] == 'Civil'
    
    @patch('requests.get')
    def test_search_documents(self, mock_get, processor):
        """Test searching documents in SharePoint"""
        mock_response = Mock()
        mock_response.json.return_value = {
            'value': [
                {'name': 'immigration_case.pdf', 'id': 'search-result-1'},
                {'name': 'immigration_petition.docx', 'id': 'search-result-2'}
            ]
        }
        mock_response.status_code = 200
        mock_get.return_value = mock_response
        
        processor.access_token = 'mock-token'
        processor.site_id = 'test-site-id'
        
        results = processor.search_documents('immigration')
        
        assert len(results) == 2
        assert 'immigration' in results[0]['name'].lower()
        assert 'immigration' in results[1]['name'].lower()
    
    def test_error_handling_network_failure(self, processor):
        """Test error handling for network failures"""
        with patch('requests.get', side_effect=requests.ConnectionError("Network error")):
            processor.access_token = 'mock-token'
            
            with pytest.raises(requests.ConnectionError):
                processor.list_documents()
    
    def test_error_handling_authentication_expired(self, processor):
        """Test error handling for expired authentication"""
        mock_response = Mock()
        mock_response.status_code = 401
        mock_response.json.return_value = {'error': 'token_expired'}
        
        with patch('requests.get', return_value=mock_response):
            processor.access_token = 'expired-token'
            
            # Should attempt re-authentication
            processor.authenticate = Mock(return_value='new-token')
            
            try:
                processor.list_documents()
            except Exception:
                pass  # Expected to fail in test environment
            
            processor.authenticate.assert_called()
    
    def test_pagination_handling(self, processor, mock_documents):
        """Test handling of paginated SharePoint responses"""
        # Mock paginated responses
        page1_response = Mock()
        page1_response.json.return_value = {
            'value': mock_documents[:2],
            '@odata.nextLink': 'https://graph.microsoft.com/v1.0/next-page'
        }
        page1_response.status_code = 200
        
        page2_response = Mock()
        page2_response.json.return_value = {
            'value': mock_documents[2:],
        }
        page2_response.status_code = 200
        
        with patch('requests.get', side_effect=[page1_response, page2_response]):
            processor.access_token = 'mock-token'
            processor.site_id = 'test-site-id'
            
            all_documents = processor.list_all_documents()
            
            assert len(all_documents) == 3
    
    def test_document_version_handling(self, processor):
        """Test handling of document versions"""
        mock_versions = [
            {'id': 'v1', 'versionLabel': '1.0', 'lastModifiedDateTime': '2025-05-25T10:00:00Z'},
            {'id': 'v2', 'versionLabel': '2.0', 'lastModifiedDateTime': '2025-05-26T10:00:00Z'}
        ]
        
        with patch('requests.get') as mock_get:
            mock_response = Mock()
            mock_response.json.return_value = {'value': mock_versions}
            mock_response.status_code = 200
            mock_get.return_value = mock_response
            
            processor.access_token = 'mock-token'
            processor.site_id = 'test-site-id'
            
            versions = processor.get_document_versions('doc-id')
            
            assert len(versions) == 2
            assert versions[1]['versionLabel'] == '2.0'  # Latest version
    
    def test_bulk_metadata_update(self, processor):
        """Test bulk updating of document metadata"""
        updates = [
            {'doc_id': 'doc1', 'metadata': {'classification': 'Immigration'}},
            {'doc_id': 'doc2', 'metadata': {'classification': 'Criminal'}},
            {'doc_id': 'doc3', 'metadata': {'classification': 'Civil'}}
        ]
        
        processor.update_document_metadata = Mock(return_value=True)
        
        results = processor.bulk_update_metadata(updates)
        
        assert len(results) == 3
        assert all(result['success'] for result in results)
        assert processor.update_document_metadata.call_count == 3
    
    @patch('core.sharepoint_processor.logging')
    def test_logging_functionality(self, mock_logging, processor):
        """Test logging during SharePoint operations"""
        processor.access_token = 'mock-token'
        
        with patch('requests.get') as mock_get:
            mock_response = Mock()
            mock_response.json.return_value = {'value': []}
            mock_response.status_code = 200
            mock_get.return_value = mock_response
            
            processor.list_documents()
            
            # Verify logging calls were made
            assert mock_logging.info.call_count > 0 or mock_logging.debug.call_count > 0

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
