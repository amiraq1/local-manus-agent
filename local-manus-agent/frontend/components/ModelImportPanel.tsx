"use client";

import { useState, useRef } from "react";
import { Upload, X, CheckCircle, AlertTriangle } from "lucide-react";

const API = "http://localhost:8000/api";
const CHUNK_SIZE = 50 * 1024 * 1024; // 50MB

export default function ModelImportPanel() {
  const [file, setFile] = useState<File | null>(null);
  const [modelName, setModelName] = useState("");
  const [uploading, setUploading] = useState(false);
  const [progress, setProgress] = useState(0);
  const [result, setResult] = useState<{ name: string; size: number; sha256: string; path: string } | null>(null);
  const [error, setError] = useState("");
  const fileRef = useRef<HTMLInputElement>(null);

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const f = e.target.files?.[0];
    if (!f) return;
    if (!f.name.endsWith(".litertlm")) {
      setError("Only .litertlm files are accepted");
      return;
    }
    setFile(f);
    setModelName(f.name.replace(".litertlm", ""));
    setError("");
    setResult(null);
  };

  const handleImport = async () => {
    if (!file) return;
    setUploading(true);
    setError("");
    setProgress(0);

    try {
      // 1. Start import
      const startRes = await fetch(`${API}/models/import/start`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ filename: file.name, size: file.size, model_name: modelName }),
      });
      const startData = await startRes.json();
      if (!startData.accepted) {
        setError(startData.error || "Import rejected");
        setUploading(false);
        return;
      }

      const importId = startData.import_id;
      const totalChunks = startData.total_chunks;

      // 2. Upload chunks
      for (let i = 0; i < totalChunks; i++) {
        const start = i * CHUNK_SIZE;
        const end = Math.min(start + CHUNK_SIZE, file.size);
        const chunk = file.slice(start, end);

        const formData = new FormData();
        formData.append("import_id", importId);
        formData.append("chunk_index", String(i));
        formData.append("chunk", chunk);

        const chunkRes = await fetch(`${API}/models/import/chunk`, { method: "POST", body: formData });
        const chunkData = await chunkRes.json();
        if (!chunkData.success) {
          setError(chunkData.error || `Chunk ${i} failed`);
          await fetch(`${API}/models/import/${importId}`, { method: "DELETE" });
          setUploading(false);
          return;
        }
        setProgress(Math.round(((i + 1) / totalChunks) * 100));
      }

      // 3. Finish
      const finishRes = await fetch(`${API}/models/import/finish`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ import_id: importId }),
      });
      const finishData = await finishRes.json();
      if (finishData.success) {
        setResult({ name: finishData.name, size: finishData.size, sha256: finishData.sha256, path: finishData.path });
      } else {
        setError(finishData.error || "Finish failed");
      }
    } catch (e) {
      setError("Upload failed");
    }
    setUploading(false);
  };

  const formatSize = (bytes: number) => {
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(0)} KB`;
    if (bytes < 1024 * 1024 * 1024) return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
    return `${(bytes / (1024 * 1024 * 1024)).toFixed(2)} GB`;
  };

  return (
    <div className="p-3 space-y-3 border-t border-dark-700">
      <h4 className="text-xs font-medium text-dark-200 flex items-center gap-2">
        <Upload size={13} /> Import .litertlm Model
      </h4>

      <p className="text-[10px] text-dark-500">
        Models are not bundled with Local Manus Agent. Select a .litertlm file from your device to import it.
      </p>

      {/* File picker */}
      <input ref={fileRef} type="file" accept=".litertlm" onChange={handleFileSelect} className="hidden" />
      <button
        onClick={() => fileRef.current?.click()}
        disabled={uploading}
        className="w-full px-3 py-2 rounded border border-dashed border-dark-600 text-xs text-dark-400 hover:border-primary hover:text-primary transition-colors disabled:opacity-50"
      >
        {file ? `${file.name} (${formatSize(file.size)})` : "Choose .litertlm file..."}
      </button>

      {/* Model name */}
      {file && !result && (
        <input
          type="text"
          value={modelName}
          onChange={(e) => setModelName(e.target.value)}
          placeholder="Model name"
          className="w-full bg-dark-800 border border-dark-600 rounded px-2 py-1 text-xs text-dark-200"
        />
      )}

      {/* Progress */}
      {uploading && (
        <div className="space-y-1">
          <div className="w-full h-2 bg-dark-800 rounded overflow-hidden">
            <div className="h-full bg-primary transition-all" style={{ width: `${progress}%` }} />
          </div>
          <p className="text-[10px] text-dark-400 text-center">{progress}%</p>
        </div>
      )}

      {/* Import button */}
      {file && !result && !uploading && (
        <button onClick={handleImport} className="w-full px-3 py-1.5 rounded bg-primary text-white text-xs font-medium">
          Import Model
        </button>
      )}

      {/* Error */}
      {error && <p className="text-[10px] text-red-400">{error}</p>}

      {/* Result */}
      {result && (
        <div className="bg-green-900/10 border border-green-700/30 rounded p-2 space-y-1">
          <div className="flex items-center gap-1.5">
            <CheckCircle size={12} className="text-green-400" />
            <span className="text-xs text-green-400 font-medium">Model Imported</span>
          </div>
          <p className="text-[10px] text-dark-300">{result.name} ({formatSize(result.size)})</p>
          <p className="text-[9px] text-dark-500 font-mono truncate">SHA256: {result.sha256.slice(0, 16)}...</p>
        </div>
      )}

      {/* SDK warning */}
      <div className="flex items-start gap-1.5 text-[9px] text-dark-500">
        <AlertTriangle size={10} className="shrink-0 mt-0.5 text-yellow-500" />
        <span>Importing a model does not install the LiteRT-LM runtime. If SDK is missing, the file is stored but cannot run yet.</span>
      </div>
    </div>
  );
}
