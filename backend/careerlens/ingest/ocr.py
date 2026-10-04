import cv2
import pytesseract
import numpy as np
from pdf2image import convert_from_path
from typing import Dict, Any, Tuple
import time
import os

# Ensure tesseract is installed and available in PATH or set explicitly if needed
# pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

def preprocess_image_for_ocr(image: np.ndarray) -> np.ndarray:
    """
    Preprocess image for better OCR results using OpenCV.
    - Grayscale
    - Denoise
    - Adaptive Thresholding
    """
    # Convert to grayscale
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    
    # Denoise
    denoised = cv2.fastNlMeansDenoising(gray, h=10, searchWindowSize=21, templateWindowSize=7)
    
    # Adaptive thresholding
    binary = cv2.adaptiveThreshold(
        denoised, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2
    )
    
    return binary

def extract_text_with_ocr(pdf_path: str, lang: str = 'eng') -> Tuple[str, float, int]:
    """
    Convert PDF to images and run OCR on each page.
    Returns extracted text, average confidence, and page count.
    """
    # 300 DPI for high quality
    pages = convert_from_path(pdf_path, dpi=300)
    full_text = []
    total_confidence = 0
    valid_words_count = 0
    
    for page in pages:
        # Convert PIL image to OpenCV format
        open_cv_image = np.array(page)
        # Convert RGB to BGR
        open_cv_image = open_cv_image[:, :, ::-1].copy()
        
        preprocessed = preprocess_image_for_ocr(open_cv_image)
        
        # image_to_data for confidence scores
        data = pytesseract.image_to_data(preprocessed, lang=lang, output_type=pytesseract.Output.DICT)
        
        page_text = []
        for i, word in enumerate(data['text']):
            conf = int(data['conf'][i])
            # Filter out empty strings and low confidence artifacts
            if word.strip() and conf > 0:
                page_text.append(word)
                total_confidence += conf
                valid_words_count += 1
                
        full_text.append(" ".join(page_text))
        
    avg_confidence = total_confidence / valid_words_count if valid_words_count > 0 else 0.0
    return "\n\n".join(full_text), avg_confidence, len(pages)
