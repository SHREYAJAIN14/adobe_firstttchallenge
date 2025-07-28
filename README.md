# Adobe India Hackathon Challenge 1a - PDF Processing Solution

## Overview
This solution extracts structured data from PDF documents and outputs JSON files that conform to the specified schema.

## Features
- Processes multiple PDFs automatically
- Extracts text, tables, and document structure
- Fast processing with fallback methods
- Dockerized for consistent deployment
- Meets all challenge constraints

## Libraries Used
- **pdfplumber**: Primary PDF text and table extraction
- **PyPDF2**: Fallback text extraction method
- **json**: JSON output formatting
- **pathlib**: File system operations

## Build and Run Commands

### Build
```bash
docker build --platform linux/amd64 -t pdf-processor .
