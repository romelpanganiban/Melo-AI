#!/usr/bin/env python
"""Quick test to verify PDF parsing works"""

import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

from services.document_parser import DocumentParser

# Test with your actual PDF file
pdf_path = Path("C:/Users/romel/Downloads")  # Change to where your PDF is
pdf_files = list(pdf_path.glob("*.pdf"))

if not pdf_files:
    print("❌ No PDF files found in Downloads folder")
    sys.exit(1)

parser = DocumentParser()

for pdf_file in pdf_files[:3]:  # Test first 3 PDFs
    print(f"\n📄 Testing: {pdf_file.name}")
    print(f"   Size: {pdf_file.stat().st_size} bytes")
    
    try:
        with open(pdf_file, 'rb') as f:
            result = parser.parse(f, pdf_file.name)
        
        print(f"   ✅ Successfully parsed!")
        print(f"   Content length: {len(result['content'])} characters")
        print(f"   Preview: {result['content'][:100]}...")
        
    except Exception as e:
        print(f"   ❌ Error: {type(e).__name__}: {str(e)}")
