import cv2
import pytesseract
import numpy as np
from pdf2image import convert_from_path

class ChartExtractor:
    """Class to extract and structure text from chart images in PDF pages."""
    
    def __init__(self, pdf_path):
        self.pdf_path = pdf_path

    def preprocess_image(self, image):
        """Convert to grayscale and apply thresholding to enhance text detection."""
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        _, thresh = cv2.threshold(gray, 150, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        return thresh

    def extract_text_from_image(self, image):
        """Use OCR to extract text from the preprocessed image."""
        custom_config = r'--oem 3 --psm 6'  # Optimized OCR settings
        text = pytesseract.image_to_string(image, config=custom_config)
        return text.strip()

    def detect_charts_and_extract_text(self, page_number):
        """Extracts charts from a page and retrieves structured data."""
        print(f"🔍 Processing charts on page {page_number}...")

        images = convert_from_path(self.pdf_path, first_page=page_number, last_page=page_number)
        extracted_data = {}

        for index, image in enumerate(images):
            open_cv_image = np.array(image)
            open_cv_image = open_cv_image[:, :, ::-1].copy()  # Convert RGB to BGR (for OpenCV)

            text_data = self.extract_text_from_image(open_cv_image)
            cleaned_text = self.clean_extracted_chart_text(text_data)
            extracted_data[f"Chart_{index+1}"] = cleaned_text
        
        return extracted_data

    def clean_extracted_chart_text(self, text):
        """Cleans extracted text and structures it into numerical arrays if possible."""
        lines = text.split("\n")
        structured_data = []
        for line in lines:
            cleaned_line = line.strip()
            if cleaned_line:
                structured_data.append(cleaned_line)
        
        return structured_data

    def extract_charts_from_pdf(self, start_page, end_page):
        """Extracts chart text from multiple pages."""
        all_chart_data = {}
        for page in range(start_page, end_page + 1):
            chart_data = self.detect_charts_and_extract_text(page)
            if chart_data:
                all_chart_data[f"Page_{page}"] = chart_data
        
        return all_chart_data
    
    def extract_charts_from_page(self, page_number):
        """Extract chart-like data from a given page number."""
        images = convert_from_path(self.pdf_path, first_page=page_number, last_page=page_number)
        extracted_data = []

        for img in images:
            processed_img = self.preprocess_image(np.array(img))
            text_data = self.extract_text_from_image(processed_img)
            structured_data = self.parse_chart_data(text_data)
            extracted_data.append(structured_data)

        return extracted_data

    def extract_numerical_values(self, text):
        """Extracts structured numerical values from OCR text"""
        numbers = [num for num in text.split() if num.replace('.', '', 1).isdigit()]
        return numbers if numbers else None
        
    def parse_chart_data(self, text):
        """Extract relevant numerical values from the detected text."""
        extracted_values = [val for val in text.split() if val.replace('.', '', 1).isdigit()]
        return {"chart_data": extracted_values}
    
# Example usage:
# pdf_path = "Infographics English.pdf"
# chart_extractor = ChartExtractor(pdf_path)
# chart_data = chart_extractor.extract_charts_from_pdf(1, 31)  # Process all pages
# print(chart_data)
