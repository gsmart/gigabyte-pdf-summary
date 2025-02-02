# Gigabyte PDF Summary

This project, **Gigabyte PDF Summary**, is designed to process and summarize **large PDF files up to 5GB**. It extracts key insights from massive research papers, reports, and books. The system consists of:
- **Front-end**: A React-based UI with Bootstrap for polished styling.
- **Back-end**: A Flask API that processes PDF files using **OCR, NLP, and AI models**.

**Upcoming Features:**
- Docker version for easy deployment.
- More AI model integrations (Mistral, T5, etc.).
  
---

## Table of Contents
- [Project Structure](#project-structure)
- [Prerequisites](#prerequisites)
- [Installation Instructions](#installation-instructions)
  - [Ollama and AI Models Setup](#ollama-and-ai-models-setup)
  - [Backend Setup](#backend-setup)
  - [Frontend Setup](#frontend-setup)
- [Running the Application](#running-the-application)
- [Usage](#usage)
- [API Endpoints](#api-endpoints)
- [Contact](#contact)

---

## Project Structure
```
gigabyte-pdf-summary/
│
├── front-end/          # React UI for file upload and summary display
│   ├── src/
│   ├── public/
│   ├── .env
│   └── package.json
│
├── back-end/           # Flask API for processing PDFs
│   ├── app.py
│   ├── pdf_processor.py
│   ├── summarize_pdf.py
│   ├── utils/          # Utility scripts
│   ├── environment.yml
│   ├── requirements.txt
│   └── uploads/        # Stores uploaded PDFs
│
└── README.md           # This README file
```

---

## Prerequisites
1. **Python**: Version 3.8+ (Conda recommended).
2. **Node.js**: Version 16+.
3. **npm**: For managing JavaScript dependencies.
4. **Ollama**: AI model manager.
5. **Mistral / T5 / DeepSeek AI models**: Used for summarization.
6. **pip & conda**: Python package managers.

---

## Installation Instructions

### Ollama and AI Models Setup

#### MacOS
```bash
brew install ollama
```

#### Ubuntu
```bash
curl -fsSL https://ollama.com/install.sh | sh
```

#### Windows
1. Download from [Ollama’s official site](https://ollama.ai/).
2. Install and follow the instructions.

##### Install AI Models
```bash
ollama pull mistral
ollama pull deepseek
ollama pull t5
```

---

### Backend Setup

1. **Install Conda** (Skip if already installed):  
   [Download Conda](https://docs.conda.io/en/latest/miniconda.html)

2. **Create a virtual environment and activate it**:
   ```bash
   conda env create -f environment.yml
   conda activate pdf-summarizer
   ```

3. **Install dependencies** (if not using `environment.yml`):
   ```bash
   pip install -r requirements.txt
   ```

4. **Run the Flask API**:
   ```bash
   python app.py
   ```

---

### Frontend Setup

1. **Navigate to `front-end`**:
   ```bash
   cd front-end
   ```

2. **Install dependencies**:
   ```bash
   npm install
   ```

3. **Run the React App**:
   ```bash
   npm start
   ```

---

## Running the Application

1. **Start the Flask Server**:
   ```bash
   cd back-end
   python app.py
   ```

2. **Start the React Client**:
   ```bash
   cd front-end
   npm start
   ```

3. Open the app at **`http://localhost:3000`**.

---

## Usage

### Uploading a PDF
1. Open the React app.
2. Drag and drop a **PDF file (up to 5GB)**.
3. The system will upload in chunks and process the document.
4. Once processing reaches **87%**, the UI will display `"Processing a document"`.
5. After 87%, the UI updates to `"Working on Summary"`.

### API Endpoints

#### **Upload a PDF**
```bash
curl --location 'http://localhost:8000/upload-pdf/' \
--header 'Accept: application/json' \
--header 'Content-Type: multipart/form-data' \
--form 'file=@"/Users/ganeshsawant/Downloads/Infographics English.pdf"'
```

#### **Chunked Upload**
```bash
curl --location 'http://localhost:8000/upload-pdf-chunk/' \
--header 'Accept: application/json' \
--header 'Content-Type: multipart/form-data' \
--form 'file=@"/path/to/chunk"' \
--form 'chunkIndex=0' \
--form 'totalChunks=10' \
--form 'filename="bigfile.pdf"'
```

#### **Get Processing Status**
```bash
curl --location 'http://localhost:8000/progress/bigfile.pdf'
```

---

## Contact

For any issues or support, email:  
📧 **gsmart07@gmail.com**  

---

🚀 Enjoy summarizing giant PDFs with **Gigabyte PDF Summary**! 🎉
