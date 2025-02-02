import requests
import re
import nltk
import PyPDF2
import pytesseract
import time
import os
import concurrent.futures
from pdf2image import convert_from_path
from nltk.tokenize import sent_tokenize
from utils.ChartExtractor import ChartExtractor
from utils.SummaryGenerator import SummaryGenerator

# Download NLTK tokenization model
nltk.download('punkt')

# Constants
OLLAMA_API_URL = "http://localhost:11434/api/generate"
MODEL_NAME = "deepseek-r1:1.5b"
MAX_WORKERS = 8  # Optimized threading for fast processing
EXTRACTED_TEXT_FILE = "extracted_text.txt"
EXTRACTED_TEXT_DIR = "extracted_text"

os.makedirs(EXTRACTED_TEXT_DIR, exist_ok=True)


class PDFProcessor:
    def __init__(self, pdf_path):
        self.pdf_path = pdf_path
        self.num_pages = self.get_number_of_pages()
        self.process_status = []
        self.indexed_sections = self.extract_indexed_sections()
        self.process_status = []
        self.timestamp = time.strftime("%Y%m%d_%H%M%S")
        self.extracted_text_file = os.path.join(EXTRACTED_TEXT_DIR, f"extracted_{self.timestamp}.txt")

    def get_number_of_pages(self):
        """Fetches the total number of pages in the PDF."""
        with open(self.pdf_path, 'rb') as f:
            reader = PyPDF2.PdfReader(f)
            return len(reader.pages)

    def clean_text(self, text):
        """Cleans extracted text by removing unnecessary whitespace and noise."""
        text = re.sub(r'\n+', ' ', text)  # Replace multiple newlines with a space
        text = re.sub(r'\s+', ' ', text).strip()  # Remove extra spaces
        return text

    def extract_text_from_pdf_page(self, page_number):
        """Extracts text from a specific page of a PDF file using OCR if needed."""
        self.process_status.append({"page": page_number, "status": "Extracting Text"})
        print(f"\n📄 Extracting text from page {page_number}...")

        text = ""
        with open(self.pdf_path, 'rb') as f:
            reader = PyPDF2.PdfReader(f)
            if page_number < 1 or page_number > self.num_pages:
                print(f"❌ Page {page_number} is out of range. PDF has {self.num_pages} pages.")
                return text
            page = reader.pages[page_number - 1]
            extracted_text = page.extract_text()
            if extracted_text:
                text += extracted_text
                print(f"✅ Extracted text from page {page_number}")
            else:
                print(f"⚠️ No extractable text on page {page_number}, attempting OCR...")
                text += self.extract_text_from_images(page_number)
        
        return self.clean_text(text)

    def extract_text_from_images(self, page_number):
        """Extracts text from images using OCR."""
        self.process_status.append({"page": page_number, "status": "Extracting Image"})
        images = convert_from_path(self.pdf_path, first_page=page_number, last_page=page_number)
        text = ""
        for image in images:
            extracted_text = pytesseract.image_to_string(image)
            cleaned_text = self.clean_text(extracted_text)
            if cleaned_text.strip():
                text += cleaned_text + " "
                print(f"✅ Extracted text from image-based content on page {page_number}")
        return text

    def extract_indexed_sections(self):
        """Extracts section titles and page numbers from index (assuming Page 3 contains the index)."""
        print("\n📑 Extracting index sections...")
        index_text = self.extract_text_from_pdf_page(3)
        sections = {}
        matches = re.findall(r'(\d+)\.\s*(.+?)\s+(\d+)', index_text)
        for match in matches:
            section_number, section_title, page_number = match
            sections[int(page_number)] = section_title.strip()
        print(f"✅ Found {len(sections)} indexed sections.")
        return sections

    def process_page(self, page_number):
        """Processes a single page and returns structured data."""
        text = self.extract_text_from_pdf_page(page_number)
        chart_extractor = ChartExtractor(self.pdf_path)
        chart_data = chart_extractor.extract_charts_from_page(page_number)

        final_output = {
            "page": page_number,
            "text": text,
            "charts": chart_data
        }
        return final_output

    def process_pdf(self):
        """Processes the entire PDF and returns structured JSON output."""
        start_time = time.time()
        extracted_data = []

        with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
            futures = {executor.submit(self.process_page, page): page for page in range(1, self.num_pages + 1)}
            for future in concurrent.futures.as_completed(futures):
                page_data = future.result()
                if page_data:
                    extracted_data.append(page_data)

        extracted_text = "\n".join([page["text"] for page in extracted_data])
        with open(EXTRACTED_TEXT_FILE, "w", encoding="utf-8") as f:
            f.write(extracted_text)
        print(f"\n📜 Extracted text saved to {EXTRACTED_TEXT_FILE}.")

        # Generate structured summary
        summary_generator = SummaryGenerator(extracted_text)
        summary_text = summary_generator.generate_summary()

        # Convert to HTML format
        html_summary = HTMLConverter(summary_text).convert_to_html()

        final_output = {
            "pdf_path": self.pdf_path,
            "num_pages": self.num_pages,
            "indexed_sections": self.indexed_sections,
            "status": "Done",
            "extracted_pages": extracted_data,
            "summary_text": summary_text,
            "summary_html": html_summary,
            "processing_time": round(time.time() - start_time, 2)
        }
        return final_output

class HTMLConverter:
    """Converts structured text into HTML format for better rendering on web."""
    def __init__(self, text):
        self.text = text

    def convert_to_html(self):
        """Converts summary text into structured HTML format."""
        html = ""

        for line in self.text.split("\n"):
            if line.strip().startswith("###"):
                html += f"<h3>{line.strip()[4:]}</h3>"
            elif line.strip().startswith("- "):
                html += f"<ul><li>{line.strip()[2:]}</li></ul>"
            elif line.strip():
                html += f"<p>{line.strip()}</p>"

        # html += ""
        return html

# Example usage
if __name__ == "__main__":
    pdf_processor = PDFProcessor("Infographics English.pdf")
    result = pdf_processor.process_pdf()
    print(result)
