import pytesseract
from pdf2image import convert_from_bytes
from PIL import Image
import cv2
import numpy as np
import re
from typing import Dict, Any, Optional, List
from io import BytesIO


class OCRService:
    """Service for OCR processing of medical documents"""

    @staticmethod
    def preprocess_image(image: Image.Image) -> Image.Image:
        """Preprocess image for better OCR results"""
        # Convert PIL Image to OpenCV format
        img_array = np.array(image)

        # Convert to grayscale
        gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)

        # Apply thresholding
        _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

        # Noise removal
        denoised = cv2.fastNlMeansDenoising(binary)

        # Convert back to PIL Image
        return Image.fromarray(denoised)

    @staticmethod
    def extract_text_from_image(image: Image.Image) -> str:
        """Extract text from an image using Tesseract OCR"""
        try:
            # Preprocess image
            processed_image = OCRService.preprocess_image(image)

            # Perform OCR
            text = pytesseract.image_to_string(processed_image, lang='eng')
            return text.strip()
        except Exception as e:
            print(f"Error in OCR: {e}")
            return ""

    @staticmethod
    def extract_text_from_pdf(pdf_bytes: bytes) -> str:
        """Extract text from PDF file"""
        try:
            # Convert PDF to images
            images = convert_from_bytes(pdf_bytes)

            # Extract text from each page
            full_text = []
            for i, image in enumerate(images):
                text = OCRService.extract_text_from_image(image)
                full_text.append(f"--- Page {i+1} ---\n{text}")

            return "\n\n".join(full_text)
        except Exception as e:
            print(f"Error processing PDF: {e}")
            return ""

    @staticmethod
    def extract_medical_data(text: str) -> Dict[str, Any]:
        """
        Extract structured medical data from OCR text
        This uses regex patterns to extract common medical fields
        """
        data = {}

        # Patient Name patterns
        name_patterns = [
            r"Patient\s+Name[:\s]+([A-Z][a-zA-Z\s]+)",
            r"Name[:\s]+([A-Z][a-zA-Z\s]+)",
        ]
        for pattern in name_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                data['patient_name'] = match.group(1).strip()
                break

        # Date of Birth patterns
        dob_patterns = [
            r"Date\s+of\s+Birth[:\s]+(\d{1,2}[-/]\d{1,2}[-/]\d{2,4})",
            r"DOB[:\s]+(\d{1,2}[-/]\d{1,2}[-/]\d{2,4})",
            r"Birth\s+Date[:\s]+(\d{1,2}[-/]\d{1,2}[-/]\d{2,4})",
        ]
        for pattern in dob_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                data['date_of_birth'] = match.group(1).strip()
                break

        # Gender patterns
        gender_patterns = [
            r"Gender[:\s]+(Male|Female|M|F)",
            r"Sex[:\s]+(Male|Female|M|F)",
        ]
        for pattern in gender_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                gender = match.group(1).strip().upper()
                if gender in ['M', 'MALE']:
                    data['gender'] = 'male'
                elif gender in ['F', 'FEMALE']:
                    data['gender'] = 'female'
                break

        # Blood Pressure patterns
        bp_pattern = r"Blood\s+Pressure[:\s]+(\d{2,3})/(\d{2,3})"
        match = re.search(bp_pattern, text, re.IGNORECASE)
        if match:
            data['blood_pressure_systolic'] = int(match.group(1))
            data['blood_pressure_diastolic'] = int(match.group(2))

        # Heart Rate patterns
        hr_patterns = [
            r"Heart\s+Rate[:\s]+(\d{2,3})",
            r"Pulse[:\s]+(\d{2,3})",
            r"HR[:\s]+(\d{2,3})",
        ]
        for pattern in hr_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                data['heart_rate'] = int(match.group(1))
                break

        # Temperature patterns
        temp_patterns = [
            r"Temperature[:\s]+(\d{2,3}\.?\d*)",
            r"Temp[:\s]+(\d{2,3}\.?\d*)",
        ]
        for pattern in temp_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                data['temperature_celsius'] = float(match.group(1))
                break

        # Weight patterns
        weight_patterns = [
            r"Weight[:\s]+(\d{2,3}\.?\d*)\s*(?:kg|KG)",
            r"Wt[:\s]+(\d{2,3}\.?\d*)\s*(?:kg|KG)",
        ]
        for pattern in weight_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                data['weight_kg'] = float(match.group(1))
                break

        # Height patterns
        height_patterns = [
            r"Height[:\s]+(\d{2,3}\.?\d*)\s*(?:cm|CM)",
            r"Ht[:\s]+(\d{2,3}\.?\d*)\s*(?:cm|CM)",
        ]
        for pattern in height_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                data['height_cm'] = float(match.group(1))
                break

        # Diagnosis patterns
        diagnosis_pattern = r"Diagnosis[:\s]+([^\n]+)"
        match = re.search(diagnosis_pattern, text, re.IGNORECASE)
        if match:
            data['diagnosis'] = match.group(1).strip()

        # Blood Type patterns
        blood_type_pattern = r"Blood\s+Type[:\s]+(A|B|AB|O)[+-]"
        match = re.search(blood_type_pattern, text, re.IGNORECASE)
        if match:
            data['blood_type'] = match.group(0).split(':')[-1].strip()

        # Allergies patterns
        allergy_pattern = r"Allergies[:\s]+([^\n]+)"
        match = re.search(allergy_pattern, text, re.IGNORECASE)
        if match:
            data['allergies'] = match.group(1).strip()

        # Medications patterns
        medication_pattern = r"Medications?[:\s]+([^\n]+(?:\n(?!\n)[^\n]+)*)"
        match = re.search(medication_pattern, text, re.IGNORECASE)
        if match:
            data['current_medications'] = match.group(1).strip()

        return data

    @staticmethod
    def process_ehr_document(file_bytes: bytes, file_type: str) -> Dict[str, Any]:
        """
        Process an EHR document (PDF or image) and extract structured data
        Returns: Dictionary with extracted text and structured data
        """
        try:
            # Extract text based on file type
            if file_type.lower() == 'pdf' or file_type == 'application/pdf':
                text = OCRService.extract_text_from_pdf(file_bytes)
            else:
                # Assume it's an image
                image = Image.open(BytesIO(file_bytes))
                text = OCRService.extract_text_from_image(image)

            # Extract structured data from text
            structured_data = OCRService.extract_medical_data(text)

            return {
                'success': True,
                'raw_text': text,
                'extracted_data': structured_data,
                'confidence': 'medium'  # Could be enhanced with confidence scoring
            }

        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'raw_text': '',
                'extracted_data': {}
            }
