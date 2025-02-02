import React, { useState } from "react";
import axios from "axios";
import { useDropzone } from "react-dropzone";
import "bootstrap/dist/css/bootstrap.min.css";

const CHUNK_SIZE = 5 * 1024 * 1024; // 5MB per chunk

const App = () => {
  const [selectedFile, setSelectedFile] = useState(null);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [processing, setProcessing] = useState(false);
  const [summaryHtml, setSummaryHtml] = useState("");

  const { getRootProps, getInputProps } = useDropzone({
    accept: { "application/pdf": [".pdf"] },
    maxSize: 5 * 1024 * 1024 * 1024, // 5GB
    onDrop: (acceptedFiles) => {
      setSelectedFile(acceptedFiles[0]);
    },
  });

  const uploadFileInChunks = async () => {
    if (!selectedFile) {
      alert("Please select a PDF file to upload.");
      return;
    }

    setProcessing(true);
    setUploadProgress(0);
    setSummaryHtml("");

    const totalChunks = Math.ceil(selectedFile.size / CHUNK_SIZE);
    let uploadedChunks = 0;

    for (let chunkIndex = 0; chunkIndex < totalChunks; chunkIndex++) {
      const start = chunkIndex * CHUNK_SIZE;
      const end = Math.min(start + CHUNK_SIZE, selectedFile.size);
      const chunk = selectedFile.slice(start, end);

      const formData = new FormData();
      formData.append("file", chunk);
      formData.append("chunkIndex", chunkIndex);
      formData.append("totalChunks", totalChunks);
      formData.append("filename", selectedFile.name);

      try {
        const response = await axios.post(
          "http://localhost:8000/upload-pdf-chunk",
          formData,
          { headers: { "Content-Type": "multipart/form-data" } }
        );

        uploadedChunks++;
        const progress = Math.round((uploadedChunks / totalChunks) * 100);
        setUploadProgress(progress);

        if (uploadedChunks === totalChunks) {
          setSummaryHtml(response.data.summary_html || "<p>No summary generated.</p>");
          setProcessing(false);
        }
      } catch (error) {
        console.error("Upload failed:", error);
        alert("Upload failed. Try again.");
        setProcessing(false);
        return;
      }
    }
  };

  const getProgressMessage = () => {
    if (uploadProgress < 87) return "📄 Processing document...";
    return "📝 Working on summary...";
  };

  return (
    <div className="container text-center my-5">
      <h1 className="mb-4 fw-bold">
        📜 <span className="text-primary">Gigabyte PDF Summary</span>
      </h1>

      {/* Drag & Drop Upload Box */}
      <div
        {...getRootProps()}
        className="border border-primary border-2 p-4 w-50 mx-auto rounded-3 shadow-sm bg-light text-center cursor-pointer"
      >
        <input {...getInputProps()} />
        <p className="m-0">
          {selectedFile ? `✅ ${selectedFile.name}` : "Drag & drop or click to upload a PDF (Up to 5GB)"}
        </p>
      </div>

      {/* Upload Button */}
      <button
        onClick={uploadFileInChunks}
        className="btn btn-primary mt-4"
        disabled={processing}
      >
        {processing ? "⏳ Processing..." : "📤 Upload & Process PDF"}
      </button>

      {/* Upload Progress Bar & Status */}
      {processing && (
        <div className="mt-3">
          <p className="fw-bold">{getProgressMessage()}</p>
          <div className="progress w-50 mx-auto">
            <div
              className="progress-bar progress-bar-striped progress-bar-animated"
              role="progressbar"
              style={{ width: `${uploadProgress}%` }}
            >
              {uploadProgress}%
            </div>
          </div>
        </div>
      )}

      {/* Summary Output */}
      {summaryHtml && (
        <div className="card mt-5 w-75 mx-auto shadow">
          <div className="card-header bg-primary text-white fw-bold">📖 PDF Summary</div>
          <div className="card-body text-start" dangerouslySetInnerHTML={{ __html: formatSummary(summaryHtml) }} />
        </div>
      )}
    </div>
  );
};

// 📝 Function to format summary text for better readability
const formatSummary = (html) => {
  return html
    .replace(/\*\*(.*?)\*\*/g, '<h5 class="fw-bold mt-3">$1</h5>') // Bold **Headings**
    .replace(/\n/g, "<br>"); // Line breaks
};

export default App;
