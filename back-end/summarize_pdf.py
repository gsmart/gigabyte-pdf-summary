import subprocess
import requests
import PyPDF2
import pytesseract
from pdf2image import convert_from_path
import os
import time
import re
import nltk
import argparse
import concurrent.futures
from nltk.tokenize import sent_tokenize
from utils.ChartExtractor import ChartExtractor
from utils.text_refiner import TextRefiner  # Importing text refinement class
from utils.SummaryGenerator import SummaryGenerator

# Download NLTK tokenization data
nltk.download('punkt')

# Constants
OLLAMA_API_URL = "http://localhost:11434/api/generate"
MODEL_NAME = "deepseek-r1:1.5b"
MAX_WORKERS = 8  # Optimized threading for fast processing
EXTRACTED_TEXT_DIR = "extracted_text"
os.makedirs(EXTRACTED_TEXT_DIR, exist_ok=True)  # Ensure directory exists

def get_timestamped_filename():
    """Generates a unique timestamped filename for extracted text."""
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    return os.path.join(EXTRACTED_TEXT_DIR, f"extracted_{timestamp}.txt")

def extract_text_from_pdf_page(pdf_path, page_number):
    """Extracts text from a specific page of a PDF file using OCR if needed."""
    print(f"\n📄 Extracting text from page {page_number}...")
    text = ""
    with open(pdf_path, 'rb') as f:
        reader = PyPDF2.PdfReader(f)
        num_pages = len(reader.pages)
        if page_number < 1 or page_number > num_pages:
            print(f"❌ Page {page_number} is out of range. PDF has {num_pages} pages.")
            return text
        page = reader.pages[page_number - 1]
        extracted_text = page.extract_text()
        if extracted_text:
            text += extracted_text
            print(f"✅ Extracted text from page {page_number}")
        else:
            print(f"⚠️ No extractable text on page {page_number}, attempting OCR...")
            text += extract_text_from_images(pdf_path, page_number)

    # Refine extracted text using TextRefiner
    refiner = TextRefiner(text)
    return refiner.refine_text()

def extract_text_from_images(pdf_path, page_number):
    """Extracts text from images using OCR."""
    images = convert_from_path(pdf_path, first_page=page_number, last_page=page_number)
    text = ""
    for image in images:
        extracted_text = pytesseract.image_to_string(image)
        cleaned_text = TextRefiner(extracted_text).refine_text()  # Clean extracted text
        if cleaned_text.strip():
            text += cleaned_text + " "
            print(f"✅ Extracted text from image-based content on page {page_number}")
    return text

def extract_indexed_sections(pdf_path):
    """Extracts section titles and page numbers from index."""
    print("\n📑 Extracting index sections...")
    index_text = extract_text_from_pdf_page(pdf_path, 3)  # Assuming index is on Page 3
    sections = {}
    
    matches = re.findall(r'(\d+)\.\s*(.+?)\s+(\d+)', index_text)  # Matches "1. Section Title 03"
    
    for match in matches:
        section_number, section_title, page_number = match
        sections[int(page_number)] = section_title.strip()
    
    print(f"✅ Found {len(sections)} indexed sections.")
    return sections

def process_page(pdf_path, page_number):
    """Processes a single page: extracts text and detects charts."""
    print(f"\n📄 Processing Page {page_number}...")

    # Extract text from PDF using OCR if needed
    page_text = extract_text_from_pdf_page(pdf_path, page_number)

    # Initialize ChartExtractor
    chart_extractor = ChartExtractor(pdf_path)
    charts_data = chart_extractor.extract_charts_from_page(page_number)

    # Combine extracted text and chart data
    if charts_data and isinstance(charts_data, dict):
        page_text += f"\n=== Charts and Data from Page {page_number} ===\n"
        if "chart_text" in charts_data:
            page_text += f"\nExtracted Text from Charts:\n{charts_data['chart_text']}\n"
        if "chart_numbers" in charts_data:
            page_text += f"\nExtracted Numerical Data:\n{charts_data['chart_numbers']}\n"

    if not page_text.strip():
        print(f"\n🚫 No meaningful text extracted from page {page_number}. Skipping...")
        return None

    return f"\n=== Page {page_number} ===\n{page_text}"

def generate_summary(text_file):
    """Summarizes the extracted text file using Ollama API with structured sections."""
    print("\n⏳ Generating structured summary...")

    with open(text_file, "r", encoding="utf-8") as f:
        extracted_content = f.read()

    generator = SummaryGenerator(extracted_content)
    final_summary = generator.generate_summary()

    print("\n✅ Summary generated successfully.\n")
    return final_summary

def main():
    parser = argparse.ArgumentParser(description="Extract and summarize PDF content using Ollama API.")
    parser.add_argument("--mode", choices=["api", "cli"], required=True, help="Choose API or CLI mode")
    args = parser.parse_args()
    pdf_path = "Infographics English.pdf"

    start_time = time.time()
    indexed_sections = extract_indexed_sections(pdf_path)
    extracted_texts = {}

    # Extract text from all pages in parallel (ensuring ordered sequence)
    with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = {executor.submit(process_page, pdf_path, page): page for page in range(1, len(PyPDF2.PdfReader(open(pdf_path, 'rb')).pages) + 1)}
        for future in concurrent.futures.as_completed(futures):
            page = futures[future]  # Get corresponding page number
            page_text = future.result()
            if page_text:
                extracted_texts[page] = page_text  # Store in dict to preserve order

    # Sort extracted text by page order
    sorted_text = "\n".join([extracted_texts[p] for p in sorted(extracted_texts.keys())])

    # ✅ Save extracted text to a **timestamped file**
    extracted_text_file = get_timestamped_filename()
    with open(extracted_text_file, "w", encoding="utf-8") as f:
        f.write(sorted_text)

    print(f"\n📜 Extracted text saved to {extracted_text_file}.")

    # ✅ **Generate Summary using the newly saved extracted text file**
    final_summary = generate_summary(extracted_text_file)

    print(f"\n======= Broad Summary =======\n")
    print(final_summary)  # 🔥 Ensure Summary Appears on Command Line!
    
    print(f"\n✅ Process completed in {round(time.time() - start_time, 2)} seconds.")

if __name__ == "__main__":
    main()
