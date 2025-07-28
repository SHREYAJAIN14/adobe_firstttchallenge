#!/usr/bin/env python3
"""
Adobe India Hackathon Challenge 1a - PDF Processing Solution
Extracts structured data from PDF documents and outputs JSON files
"""

import json
import os
import time
from pathlib import Path
from typing import Dict, List, Any
import logging

try:
    import PyPDF2
    import pdfplumber
except ImportError as e:
    print(f"Required libraries not installed: {e}")
    print("Please run: pip install PyPDF2 pdfplumber python-json-logger pytesseract Pillow")
    exit(1)

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def extract_text_with_pypdf2(pdf_path: Path) -> str:
    """Extract text using PyPDF2 (fallback method)"""
    try:
        with open(pdf_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            text = ""
            for page in pdf_reader.pages:
                text += page.extract_text() + "\n"
            return text
    except Exception as e:
        logger.error(f"PyPDF2 extraction failed for {pdf_path}: {e}")
        return ""

def extract_text_with_pdfplumber(pdf_path: Path) -> Dict[str, Any]:
    """Extract structured text using pdfplumber (primary method)"""
    try:
        with pdfplumber.open(pdf_path) as pdf:
            pages_data = []
            total_text = ""
            
            for page_num, page in enumerate(pdf.pages, 1):
                page_text = page.extract_text() or ""
                total_text += page_text + "\n"
                
                # Extract tables if any
                tables = page.extract_tables()
                
                page_data = {
                    "page_number": page_num,
                    "text": page_text,
                    "tables": tables if tables else [],
                    "width": page.width,
                    "height": page.height
                }
                pages_data.append(page_data)
            
            return {
                "total_pages": len(pdf.pages),
                "full_text": total_text,
                "pages": pages_data
            }
    except Exception as e:
        logger.error(f"pdfplumber extraction failed for {pdf_path}: {e}")
        return {"total_pages": 0, "full_text": "", "pages": []}

def analyze_document_structure(pdf_data: Dict[str, Any]) -> Dict[str, Any]:
    """Analyze document structure and extract meaningful information"""
    full_text = pdf_data.get("full_text", "")
    pages = pdf_data.get("pages", [])
    
    if not full_text:
        return {
            "document_stats": {
                "total_pages": 0,
                "word_count": 0,
                "character_count": 0,
                "paragraph_count": 0,
                "table_count": 0
            },
            "content_structure": {
                "headings": [],
                "paragraphs": [],
                "tables": []
            },
            "metadata": {
                "extraction_method": "failed",
                "processing_timestamp": time.time()
            }
        }
    
    # Basic text analysis
    words = full_text.split()
    word_count = len(words)
    char_count = len(full_text)
    
    # Extract potential headings (lines with fewer words, often capitalized)
    lines = full_text.split('\n')
    headings = []
    paragraphs = []
    
    for line in lines:
        line = line.strip()
        if line:
            words_in_line = line.split()
            if len(words_in_line) <= 10 and (line.isupper() or line.istitle()):
                headings.append(line)
            elif len(words_in_line) > 10:
                paragraphs.append(line)
    
    # Extract tables from all pages
    all_tables = []
    for page in pages:
        if page.get("tables"):
            all_tables.extend(page["tables"])
    
    return {
        "document_stats": {
            "total_pages": pdf_data.get("total_pages", 0),
            "word_count": word_count,
            "character_count": char_count,
            "paragraph_count": len(paragraphs),
            "table_count": len(all_tables)
        },
        "content_structure": {
            "headings": headings[:10],  # Limit to first 10 headings
            "paragraphs": paragraphs[:5],  # Limit to first 5 paragraphs
            "tables": all_tables
        },
        "metadata": {
            "extraction_method": "pdfplumber",
            "processing_timestamp": time.time()
        }
    }

def process_single_pdf(pdf_path: Path, output_dir: Path) -> bool:
    """Process a single PDF file and generate JSON output"""
    try:
        logger.info(f"Processing {pdf_path.name}")
        start_time = time.time()
        
        # Extract data using pdfplumber (primary method)
        pdf_data = extract_text_with_pdfplumber(pdf_path)
        
        # If pdfplumber fails, fallback to PyPDF2
        if not pdf_data.get("full_text"):
            logger.warning(f"Falling back to PyPDF2 for {pdf_path.name}")
            fallback_text = extract_text_with_pypdf2(pdf_path)
            pdf_data = {
                "total_pages": 1,
                "full_text": fallback_text,
                "pages": [{"page_number": 1, "text": fallback_text, "tables": []}]
            }
        
        # Analyze document structure
        
        structured_data = analyze_document_structure(pdf_data)
        
        # Create output JSON
        output_data = {
            "filename": pdf_path.name,
            "processing_time": time.time() - start_time,
            **structured_data
        }
        
        # Save JSON output
        output_file = output_dir / f"{pdf_path.stem}.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Successfully processed {pdf_path.name} in {output_data['processing_time']:.2f}s")
        return True
        
    except Exception as e:
        logger.error(f"Failed to process {pdf_path.name}: {e}")
        return False

def process_pdfs():
    """Main function to process all PDFs in the input directory"""
    # Use local paths instead of Docker paths
    input_dir = Path("input")
    output_dir = Path("output")
    
    # Ensure directories exist
    input_dir.mkdir(exist_ok=True)
    output_dir.mkdir(exist_ok=True)
    
    logger.info("Starting PDF Processing Solution")
    logger.info(f"Input directory: {input_dir.absolute()}")
    logger.info(f"Output directory: {output_dir.absolute()}")
    
    # Find all PDF files
    pdf_files = list(input_dir.glob("*.pdf"))
    
    if not pdf_files:
        logger.warning("No PDF files found in 'input' directory")
        logger.info("Please place your PDF files in the 'input' folder")
        
        # Create helpful instructions
        print("\n" + "="*60)
        print("📋 INSTRUCTIONS:")
        print("1. Place your PDF files in the 'input' folder")
        print("2. Run this script again: python process_pdfs.py")
        print("3. Check results in the 'output' folder")
        print("="*60)
        
        # Show current directory structure
        print(f"\n📁 Current directory: {Path.cwd()}")
        if input_dir.exists():
            files_in_input = list(input_dir.iterdir())
            if files_in_input:
                print(f"📂 Files in input folder: {[f.name for f in files_in_input]}")
            else:
                print("📂 Input folder is empty")
        else:
            print("📂 Input folder will be created")
        
        return
    
    logger.info(f"Found {len(pdf_files)} PDF files to process")
    print(f"\n🔍 Found PDF files: {[f.name for f in pdf_files]}")
    
    # Process each PDF
    successful = 0
    failed = 0
    total_start_time = time.time()
    
    for pdf_file in pdf_files:
        if process_single_pdf(pdf_file, output_dir):
            successful += 1
        else:
            failed += 1
    
    total_time = time.time() - total_start_time
    
    # Final summary
    print(f"\n" + "="*60)
    print(f"📊 PROCESSING SUMMARY:")
    print(f"✅ Successfully processed: {successful} files")
    if failed > 0:
        print(f"❌ Failed to process: {failed} files")
    print(f"⏱️  Total processing time: {total_time:.2f} seconds")
    print(f"📁 Output location: {output_dir.absolute()}")
    print("="*60)
    
    if successful > 0:
        logger.info(f"JSON outputs saved in 'output' directory")
        print(f"\n🎉 Success! Check the 'output' folder for JSON results")
        
        # List generated files
        output_files = list(output_dir.glob("*.json"))
        if output_files:
            print(f"📄 Generated files: {[f.name for f in output_files]}")

def main():
    """Main entry point with error handling"""
    try:
        process_pdfs()
    except KeyboardInterrupt:
        print("\n\n⚠️  Processing interrupted by user")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        print(f"\n❌ An error occurred: {e}")
        print("Please check your PDF files and try again")

if __name__ == "__main__":
    main()