#!/usr/bin/env python3
"""
Test for SharePoint integration from core directory
"""

import pytest
import sys
import os

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from core import sharepoint_integration

def test_sharepoint_integration_functions():
    """Test SharePoint integration module functions exist and are callable"""
    assert callable(sharepoint_integration.update_metadata)
    assert callable(sharepoint_integration.batch_update_metadata)
    assert callable(sharepoint_integration.get_access_token)
    print("✅ Successfully verified SharePoint integration functions")

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
