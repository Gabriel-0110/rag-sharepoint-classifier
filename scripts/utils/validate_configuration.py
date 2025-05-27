#!/usr/bin/env python3
"""
Configuration Validator
Checks what configuration information is missing and provides guidance.
"""

import os
import json
from typing import Dict, List, Tuple

class ConfigurationValidator:
    def __init__(self):
        self.env_file = "/home/azureuser/rag_project/.env"
        self.missing_items = []
        self.warnings = []
        self.success_items = []
    
    def check_env_file(self) -> Dict:
        """Check .env file configuration."""
        print("🔍 Checking .env configuration...")
        
        if not os.path.exists(self.env_file):
            self.missing_items.append("❌ .env file not found")
            return {}
        
        env_vars = {}
        with open(self.env_file, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    env_vars[key] = value
        
        # Check required SharePoint settings
        sharepoint_vars = [
            'TENANT_ID', 'CLIENT_ID', 'CLIENT_SECRET', 'SITE_ID', 'LIST_ID'
        ]
        
        for var in sharepoint_vars:
            if var in env_vars and env_vars[var] and env_vars[var] != 'your-value-here':
                self.success_items.append(f"✅ {var}: Configured")
            else:
                self.missing_items.append(f"❌ {var}: Missing or placeholder")
        
        # Check Teams configuration
        if 'TEAMS_WEBHOOK_URL' in env_vars and 'webhook.office.com' in env_vars['TEAMS_WEBHOOK_URL']:
            self.success_items.append("✅ TEAMS_WEBHOOK_URL: Configured")
        else:
            self.warnings.append("⚠️ TEAMS_WEBHOOK_URL: Not configured (optional)")
        
        if env_vars.get('TEAMS_NOTIFICATIONS_ENABLED', 'false').lower() == 'true':
            self.success_items.append("✅ Teams notifications: Enabled")
        else:
            self.warnings.append("⚠️ Teams notifications: Disabled")
        
        # Check SharePoint details
        sharepoint_details = ['SHAREPOINT_SITE_URL', 'SHAREPOINT_LIBRARY_NAME', 
                            'DOCUMENT_TYPE_COLUMN', 'DOCUMENT_CATEGORY_COLUMN']
        
        for detail in sharepoint_details:
            if detail in env_vars and env_vars[detail] and env_vars[detail] != 'your-value-here':
                self.success_items.append(f"✅ {detail}: Configured")
            else:
                self.missing_items.append(f"❌ {detail}: Missing or placeholder")
        
        return env_vars
    
    def check_sharepoint_details(self) -> Dict:
        """Check if we have specific SharePoint details."""
        print("\n🔍 Checking SharePoint configuration details...")
        
        # This is now handled in check_env_file method
        return {}
    
    def check_business_categories(self) -> List:
        """Check if business categories need customization."""
        print("\n🔍 Checking business categories...")
        
        classifier_file = "/home/azureuser/rag_project/core/enhanced_rag_classifier.py"
        
        if os.path.exists(classifier_file):
            with open(classifier_file, 'r') as f:
                content = f.read()
                # Check for specialized legal categories
                legal_categories = [
                    "Family-Sponsored Immigration",
                    "Asylum & Refugee", 
                    "Employment-Based Immigration",
                    "Criminal Defense (Pretrial & Trial)",
                    "Criminal Appeals",
                    "Waivers of Inadmissibility",
                    "Humanitarian & Special Programs"
                ]
                
                found_categories = []
                for category in legal_categories:
                    if f'"{category}"' in content:
                        found_categories.append(category)
                
                if len(found_categories) >= 5:  # Most specialized categories found
                    self.success_items.append("✅ Business categories: Immigration & Criminal Law specialized categories configured")
                elif len(found_categories) >= 2:
                    self.success_items.append(f"✅ Business categories: {len(found_categories)} specialized legal categories found")
                elif '"Corporate"' in content and '"Real Estate"' in content:
                    self.warnings.append("⚠️ Business categories: Default categories (may need customization for legal practice)")
                else:
                    self.missing_items.append("❌ Business categories: Not found in classifier")
        else:
            self.missing_items.append("❌ Enhanced RAG classifier file not found")
        
        return []
    
    def generate_configuration_template(self) -> str:
        """Generate a template for missing configuration."""
        template = """
# Configuration Template
# Please fill in the following information:

## SharePoint Configuration
SHAREPOINT_SITE_URL=https://arandialaw.sharepoint.com/sites/[YOUR_SITE_NAME]
SHAREPOINT_LIBRARY_NAME=[YOUR_DOCUMENT_LIBRARY_NAME]
DOCUMENT_TYPE_COLUMN=[YOUR_DOCUMENT_TYPE_COLUMN_NAME]
DOCUMENT_CATEGORY_COLUMN=[YOUR_CATEGORY_COLUMN_NAME]

## Teams Configuration (Optional)
ENABLE_TEAMS_NOTIFICATIONS=[true/false]
NOTIFICATION_PREFERENCES=success,errors,low_confidence

## Business Categories Review
# Current categories: Corporate, Real Estate, Employment, IP, Litigation, 
# Regulatory, Financial, Technology, Healthcare, Other
# 
# Do you need to add/modify categories for your practice?
# Examples: Immigration, Family Law, Criminal Law, Tax Law, etc.

CUSTOM_CATEGORIES=[LIST_ANY_ADDITIONAL_CATEGORIES]

## Document Types Review  
# Current types: Contract, Policy, Communication, Report, Legal Document,
# Financial Document, Technical Document, Other
#
# Do you need specific legal document types?
# Examples: Pleadings, Motions, Discovery, Briefs, etc.

CUSTOM_DOCUMENT_TYPES=[LIST_ANY_ADDITIONAL_TYPES]
"""
        return template
    
    def run_validation(self):
        """Run complete configuration validation."""
        print("🚀 RAG Document Classification System - Configuration Validator")
        print("=" * 70)
        
        # Check configurations
        env_vars = self.check_env_file()
        sharepoint_details = self.check_sharepoint_details()
        business_categories = self.check_business_categories()
        
        # Print results
        print("\n📊 Configuration Status:")
        print("=" * 40)
        
        if self.success_items:
            print("\n✅ Successfully Configured:")
            for item in self.success_items:
                print(f"   {item}")
        
        if self.warnings:
            print("\n⚠️  Needs Attention/Review:")
            for item in self.warnings:
                print(f"   {item}")
        
        if self.missing_items:
            print("\n❌ Missing Configuration:")
            for item in self.missing_items:
                print(f"   {item}")
        
        # Generate recommendations
        print("\n🎯 Next Steps:")
        print("=" * 40)
        
        if len(self.missing_items) > len(self.success_items):
            print("📋 HIGH PRIORITY: Several configuration items need attention")
            print("   1. Review the CONFIGURATION_GUIDE.md document")
            print("   2. Provide the missing SharePoint details")
            print("   3. Customize business categories if needed")
            print("   4. Test the configuration")
        elif self.missing_items:
            print("📋 MEDIUM PRIORITY: Some configuration items need attention")
            print("   1. Fill in the missing details")
            print("   2. Test the configuration")
        else:
            print("🎉 EXCELLENT: Configuration appears complete!")
            print("   1. Run system tests to validate")
            print("   2. Deploy to production")
        
        # Save template
        template_file = "/home/azureuser/rag_project/docs/CONFIGURATION_TEMPLATE.txt"
        with open(template_file, 'w') as f:
            f.write(self.generate_configuration_template())
        
        print(f"\n📄 Configuration template saved to: {template_file}")
        
        # Calculate completion percentage
        total_items = len(self.success_items) + len(self.missing_items)
        completion = 0
        if total_items > 0:
            completion = (len(self.success_items) / total_items) * 100
            print(f"\n📈 Configuration Completion: {completion:.1f}%")
        
        print("\n" + "=" * 70)
        
        return {
            'success_count': len(self.success_items),
            'warning_count': len(self.warnings), 
            'missing_count': len(self.missing_items),
            'completion_percentage': completion
        }

if __name__ == "__main__":
    validator = ConfigurationValidator()
    results = validator.run_validation()
    
    if results['missing_count'] == 0:
        print("🚀 Ready to proceed with system testing!")
    else:
        print("🔧 Please complete the configuration before proceeding.")
