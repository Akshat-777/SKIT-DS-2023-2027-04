import argparse
import json
import sys
import os
from .extractor import process_resume
from .validators import validate_file

def main():
    parser = argparse.ArgumentParser(description="CareerLens Resume Ingestion CLI")
    parser.add_argument("filepath", help="Path to the PDF or DOCX file to process")
    parser.add_argument("--lang", default="eng", help="OCR language code (default: eng)")
    
    args = parser.parse_args()
    
    if not os.path.exists(args.filepath):
        print(f"Error: File '{args.filepath}' does not exist.", file=sys.stderr)
        sys.exit(1)
        
    try:
        validate_file(args.filepath, os.path.basename(args.filepath))
    except ValueError as e:
        print(f"Validation Error: {e}", file=sys.stderr)
        sys.exit(1)
        
    print(f"Processing {args.filepath}...", file=sys.stderr)
    result = process_resume(args.filepath, os.path.basename(args.filepath), args.lang)
    
    print(json.dumps(result, indent=2))

if __name__ == "__main__":
    main()
