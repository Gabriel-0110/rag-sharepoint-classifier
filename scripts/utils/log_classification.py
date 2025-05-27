#!/usr/bin/env python3
"""
Classification result logging utilities
"""
import csv
import os
import datetime
import json
from pathlib import Path

def log_classification_result(filename: str, doc_type: str, doc_category: str, 
                            confidence: str = "Unknown", processing_time: float = 0.0,
                            additional_data: dict = None):
    """
    Log classification result to CSV file
    
    Args:
        filename: Document filename
        doc_type: Classified document type
        doc_category: Classified document category
        confidence: Confidence level
        processing_time: Processing time in seconds
        additional_data: Additional metadata to log
    """
    
    log_file = "/home/azureuser/rag_project/logs/classification_log.csv"
    
    # Ensure logs directory exists
    os.makedirs(os.path.dirname(log_file), exist_ok=True)
    
    # Check if file exists to determine if we need headers
    file_exists = os.path.exists(log_file)
    
    # Prepare row data
    timestamp = datetime.datetime.now().isoformat()
    row_data = {
        "timestamp": timestamp,
        "filename": filename,
        "document_type": doc_type,
        "document_category": doc_category,
        "confidence": confidence,
        "processing_time": processing_time
    }
    
    # Add additional data if provided
    if additional_data:
        row_data.update(additional_data)
    
    # Write to CSV
    try:
        with open(log_file, 'a', newline='', encoding='utf-8') as csvfile:
            fieldnames = list(row_data.keys())
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            
            # Write header if file is new
            if not file_exists:
                writer.writeheader()
            
            writer.writerow(row_data)
            
        print(f"✅ Logged classification: {filename} -> {doc_type} | {doc_category}")
        
    except Exception as e:
        print(f"❌ Failed to log classification: {e}")

def get_classification_stats(days: int = 7) -> dict:
    """
    Get classification statistics from log file
    
    Args:
        days: Number of days to analyze
        
    Returns:
        dict: Statistics summary
    """
    log_file = "/home/azureuser/rag_project/logs/classification_log.csv"
    
    if not os.path.exists(log_file):
        return {"error": "No log file found"}
    
    try:
        cutoff_date = datetime.datetime.now() - datetime.timedelta(days=days)
        
        stats = {
            "total_documents": 0,
            "by_category": {},
            "by_type": {},
            "avg_processing_time": 0.0,
            "confidence_distribution": {}
        }
        
        total_time = 0.0
        
        with open(log_file, 'r', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            
            for row in reader:
                try:
                    # Check if within date range
                    row_date = datetime.datetime.fromisoformat(row['timestamp'])
                    if row_date < cutoff_date:
                        continue
                    
                    stats["total_documents"] += 1
                    
                    # Count by category
                    category = row.get('document_category', 'Unknown')
                    stats["by_category"][category] = stats["by_category"].get(category, 0) + 1
                    
                    # Count by type
                    doc_type = row.get('document_type', 'Unknown')
                    stats["by_type"][doc_type] = stats["by_type"].get(doc_type, 0) + 1
                    
                    # Confidence distribution
                    confidence = row.get('confidence', 'Unknown')
                    stats["confidence_distribution"][confidence] = stats["confidence_distribution"].get(confidence, 0) + 1
                    
                    # Processing time
                    try:
                        processing_time = float(row.get('processing_time', 0))
                        total_time += processing_time
                    except (ValueError, TypeError):
                        pass
                        
                except Exception as e:
                    print(f"Warning: Error processing row: {e}")
                    continue
        
        # Calculate average processing time
        if stats["total_documents"] > 0:
            stats["avg_processing_time"] = total_time / stats["total_documents"]
        
        return stats
        
    except Exception as e:
        return {"error": f"Failed to analyze log file: {e}"}

if __name__ == "__main__":
    # Test logging
    log_classification_result(
        "test_document.pdf",
        "Legal Brief",
        "Immigration Appeals",
        "High",
        1.25,
        {"method": "enhanced_rag", "fallback_used": False}
    )
    
    # Get stats
    stats = get_classification_stats(7)
    print(f"Classification stats: {json.dumps(stats, indent=2)}")
