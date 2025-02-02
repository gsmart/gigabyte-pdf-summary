from fastapi import FastAPI, UploadFile, File, Form
from fastapi.responses import JSONResponse, StreamingResponse
import shutil
import os
import asyncio
import time
from pdf_processor import PDFProcessor
from fastapi.middleware.cors import CORSMiddleware
from typing import AsyncGenerator

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Change this to specific origins for security
    allow_credentials=True,
    allow_methods=["*"],  # Allow all HTTP methods
    allow_headers=["*"],  # Allow all headers
)

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)  # Ensure directory exists

progress_tracker = {}

def generate_timestamped_filename(original_filename):
    """Generates a unique filename using a timestamp."""
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    return f"uploaded_{timestamp}.pdf"

@app.post("/upload-pdf/")
async def upload_pdf(file: UploadFile = File(...)):
    """
    Handles file upload and starts **instant PDF processing**.
    """
    os.makedirs(UPLOAD_DIR, exist_ok=True)

    new_filename = generate_timestamped_filename(file.filename)
    file_path = os.path.join(UPLOAD_DIR, new_filename)

    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    processor = PDFProcessor(file_path)
    result = processor.process_pdf()

    return result  # Directly return the processed result for instant response


@app.post("/upload-pdf-stream/")
async def upload_pdf_stream(file: UploadFile = File(...)):
    """
    Streams upload progress and starts processing while sending real-time updates.
    """
    new_filename = generate_timestamped_filename(file.filename)
    file_path = os.path.join(UPLOAD_DIR, new_filename)

    progress_tracker[new_filename] = {"progress": 0, "status": "Uploading", "summary": ""}

    async def write_file():
        with open(file_path, "wb") as buffer:
            while chunk := await file.read(1024 * 1024):  # Read in 1MB chunks
                buffer.write(chunk)
                progress_tracker[new_filename]["progress"] += len(chunk)
                yield f"data: Uploading... {progress_tracker[new_filename]['progress']} bytes\n\n"

        progress_tracker[new_filename]["status"] = "Processing"
        yield f"data: Upload complete! Processing started...\n\n"

        async for update in run_processing(file_path, new_filename):
            yield update

    return StreamingResponse(write_file(), media_type="text/event-stream")


async def run_processing(file_path: str, filename: str) -> AsyncGenerator[str, None]:
    """
    Runs the PDF processing step-by-step and **streams updates to the client**.
    """
    progress_tracker[filename]["status"] = "Extracting index"
    yield f"data: {filename} - Extracting index section...\n\n"
    await asyncio.sleep(1)

    progress_tracker[filename]["status"] = "Extracting pages"
    yield f"data: {filename} - Extracting pages...\n\n"
    extracted_data = await asyncio.to_thread(process_pdf, file_path)
    await asyncio.sleep(1)

    progress_tracker[filename]["status"] = "Summarizing content"
    yield f"data: {filename} - Summarizing content...\n\n"
    summary = await asyncio.to_thread(generate_summary, extracted_data)

    progress_tracker[filename]["status"] = "Complete"
    progress_tracker[filename]["summary"] = summary
    yield f"data: {filename} - Processing complete!\n\n"
    yield f"data: SUMMARY: {summary}\n\n"


@app.post("/upload-pdf-chunk/")
async def upload_pdf_chunk(
    file: UploadFile = File(...),
    chunkIndex: int = Form(...),
    totalChunks: int = Form(...),
    filename: str = Form(...),
):
    """
    Chunked file upload for large PDFs (5GB+).
    Chunks are **appended** to reconstruct the original file.
    Processing starts **only after the final chunk**.
    """
    # Generate timestamped filename on the first chunk
    if chunkIndex == 0:
        new_filename = generate_timestamped_filename(filename)
    else:
        new_filename = filename

    file_path = os.path.join(UPLOAD_DIR, new_filename)

    # Append chunk data to the file
    with open(file_path, "ab") as buffer:
        shutil.copyfileobj(file.file, buffer)

    if new_filename not in progress_tracker:
        progress_tracker[new_filename] = {
            "uploaded_chunks": 0,
            "total_chunks": totalChunks,
            "progress_percent": 0,
            "status": "Uploading...",
            "summary": "",
        }

    progress_tracker[new_filename]["uploaded_chunks"] += 1
    progress_tracker[new_filename]["progress_percent"] = int(
        (progress_tracker[new_filename]["uploaded_chunks"] / totalChunks) * 100
    )

    # ✅ Process file after **final chunk** is received
    if chunkIndex == totalChunks - 1:
        processor = PDFProcessor(file_path)
        result = processor.process_pdf()

        progress_tracker[new_filename]["status"] = "Complete"
        progress_tracker[new_filename]["summary"] = result["summary_html"]

        return JSONResponse(content={"filename": new_filename, **result})

    return JSONResponse(
        content={"message": f"Chunk {chunkIndex + 1}/{totalChunks} received", "filename": new_filename}
    )


@app.get("/progress/{filename}")
def get_progress(filename: str):
    """Returns processing progress for a specific file."""
    return progress_tracker.get(
        filename, {"progress_percent": 0, "status": "Not Found", "summary": ""}
    )
