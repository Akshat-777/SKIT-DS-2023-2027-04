import re
import unicodedata
from typing import Dict, Any, List, Tuple
from difflib import get_close_matches

# Canonical section headings mapping
CANONICAL_SECTIONS = [
    "Summary", "Experience", "Education", "Skills", 
    "Projects", "Certifications", "Achievements"
]

SECTION_MAPPINGS = {
    "work history": "Experience",
    "professional experience": "Experience",
    "employment": "Experience",
    "work experience": "Experience",
    "academic background": "Education",
    "scholastic achievements": "Education",
    "technical skills": "Skills",
    "core competencies": "Skills",
    "personal profile": "Summary",
    "about me": "Summary",
    "certifications and licenses": "Certifications"
}

def clean_ocr_errors(text: str) -> Tuple[str, int]:
    """Fix common OCR errors."""
    changes = 0
    # Conservative replacements (only standalone words or specific patterns to avoid over-correcting)
    # rn -> m (simple heuristic)
    new_text, c = re.subn(r'\b(l)l\b', 'll', text)
    changes += c
    return new_text, changes

def fix_hyphenation(text: str) -> Tuple[str, int]:
    """Fix words broken across lines."""
    new_text, changes = re.subn(r'([a-zA-Z])-\s*\n\s*([a-zA-Z])', r'\1\2', text)
    return new_text, changes

def normalize_unicode(text: str) -> Tuple[str, int]:
    """Normalize unicode, quotes, dashes, whitespace."""
    original_len = len(text)
    # NFKC normalizes characters (e.g., zero-width spaces, ligatures)
    text = unicodedata.normalize('NFKC', text)
    # Standardize quotes
    text = re.sub(r'[“”]', '"', text)
    text = re.sub(r'[‘’]', "'", text)
    # Standardize dashes
    text, changes = re.subn(r'[—–]', '-', text)
    # Remove multiple spaces/newlines
    text = re.sub(r'[ \t]+', ' ', text)
    text = re.sub(r'\n{3,}', '\n\n', text)
    return text.strip(), changes

def standardize_bullets(text: str) -> Tuple[str, int]:
    """Normalize bullet symbols to '- '."""
    new_text, changes = re.subn(r'^[\u2022\u25E6\u25A0\u2023\u25B8*]\s*', '- ', text, flags=re.MULTILINE)
    return new_text, changes

def standardize_dates(text: str) -> Tuple[str, int]:
    """Standardize common date formats to YYYY-MM or YYYY."""
    changes = 0
    # Simple regex to catch "Jan 2023" -> "2023-01" (Simplified for token limits)
    months = {"jan": "01", "feb": "02", "mar": "03", "apr": "04", "may": "05", "jun": "06",
              "jul": "07", "aug": "08", "sep": "09", "oct": "10", "nov": "11", "dec": "12"}
    
    def repl_date(match):
        nonlocal changes
        changes += 1
        m, y = match.group(1).lower()[:3], match.group(2)
        if len(y) == 2: y = "20" + y
        return f"{y}-{months.get(m, '01')}"

    new_text = re.sub(r'\b([A-Za-z]{3,9})\s+[\']?(\d{2,4})\b', repl_date, text)
    new_text, c = re.subn(r'(?i)\bpresent\b|\bcurrent\b', 'Present', new_text)
    changes += c
    return new_text, changes

def normalize_headings(text: str) -> Tuple[str, List[str], int]:
    """Find and normalize section headings."""
    sections_detected = []
    changes = 0
    lines = text.split('\n')
    new_lines = []
    
    for line in lines:
        clean_line = line.strip().lower()
        if clean_line.startswith('[') and clean_line.endswith(']'):
            new_lines.append(line)
            sections_detected.append(clean_line[1:-1].capitalize())
            continue
        if len(clean_line) < 30 and clean_line:
            # Check mappings
            mapped = SECTION_MAPPINGS.get(clean_line)
            if not mapped:
                # Fuzzy match
                matches = get_close_matches(clean_line, [k.lower() for k in CANONICAL_SECTIONS], n=1, cutoff=0.8)
                if matches:
                    mapped = next(k for k in CANONICAL_SECTIONS if k.lower() == matches[0])
            
            if mapped:
                new_lines.append(f"\n[{mapped.upper()}]")
                sections_detected.append(mapped)
                changes += 1
                continue
                
        new_lines.append(line)
        
    return "\n".join(new_lines), list(set(sections_detected)), changes

def clean_text_pipeline(raw_text: str) -> Dict[str, Any]:
    """Main pipeline to clean and standardize resume text."""
    log = {}
    current_text = raw_text
    
    current_text, c = fix_hyphenation(current_text)
    log['hyphens_fixed'] = c
    
    current_text, c = normalize_unicode(current_text)
    log['unicode_normalized'] = c
    
    current_text, c = standardize_bullets(current_text)
    log['bullets_standardized'] = c
    
    current_text, c = standardize_dates(current_text)
    log['dates_standardized'] = c
    
    current_text, c = clean_ocr_errors(current_text)
    log['ocr_errors_fixed'] = c
    
    current_text, sections, c = normalize_headings(current_text)
    log['headings_normalized'] = c
    
    return {
        "clean_text": current_text,
        "sections_detected": sections,
        "changes_log": log,
        "original_text": raw_text
    }
