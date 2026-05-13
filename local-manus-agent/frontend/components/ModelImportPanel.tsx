"use client";

import { useState, useRef } from "react";
import { Upload, CheckCircle, AlertTriangle } from "lucide-react";
import { API } from "@/lib/config";
import { formatSize } from "@/lib/utils";

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
    if (!f.name.endsWith(".litertlm")) { setError("Only .litertlm files are accepted"); return; }
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
      const startRes = await fetch(`${API}/models/import/start`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ filename: file.name, size: file.size, model_name: modelName }),
      });
      const startData = await startRes.json();
      if (!startData.accepted) { setError(startData.error || "Import rejected"); setUploading(false); return; }

      const importId = startData.import_id;
      const totalChunks = startData.total_chunks;

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
    } catch {
      setError("Upload failed");
    }
    setUploading(false);
  };

  return (
    <div className="p-3 space-y-3 divider">
      <h4 className="text-xs font-medium text-dark-200 flex items-center gap-2 font-display">
        <Upload size={13} className="text-primary" /> Import .litertlm Model
      </h4>

      <p className="text-[10px] text-dark-500 leading-relaxed">
        Models are not bundled with Local Manus Agent. Select a .litertlm file from your device to import it.
      </p>

      <input ref={fileRef} type="file" accept=".litertlm" onChange={handleFileSelect} className="hidden" />
      <button
        onClick={() => fileRef.current?.click()}
        disabled={uploading}
        className="w-full px-3 py-2.5 rounded-lg border border-dashed border-dark-600 text-xs text-dark-400
          hover:border-primary hover:text-primary transition-all disabled:opacity-50"
      >
        {file ? `${file.name} (${formatSize(file.size)})` : "Choose .litertlm file..."}
      </button>

      {file && !result && (
        <input type="text" value={modelName} onChange={(e) => setModelName(e.target.value)} placeholder="Model name"
          className="w-full bg-dark-800/60 border border-dark-700 rounded-lg px-2.5 py-1.5 text-xs text-dark-200 focus:outline-none focus:border-primary/40" />
      )}

      {uploading && (
        <div className="space-y-1.5">
          <div className="w-full h-2 bg-dark-800 rounded-full overflow-hidden">
            <div className="h-full bg-gradient-to-r from-primary to-emerald-300 transition-all duration-300 rounded-full" style={{ width: `${progress}%` }} />
          </div>
          <p className="text-[10px] text-dark-400 text-center">{progress}%</p>
        </div>
      )}

      {file && !result && !uploading && (
        <button onClick={handleImport} className="w-full btn-primary text-xs">Import Model</button>
      )}

      {error && <p className="text-[10px] text-red-400">{error}</p>}

      {result && (
        <div className="bg-emerald-900/10 border border-emerald-700/20 rounded-xl p-3 space-y-1.5 animate-fade-in">
          <div className="flex items-center gap-1.5">
            <CheckCircle size={12} className="text-emerald-400" />
            <span className="text-xs text-emerald-400 font-semibold">Model Imported</span>
          </div>
          <p className="text-[10px] text-dark-300">{result.name} ({formatSize(result.size)})</p>
          <p className="text-[9px] text-dark-500 font-mono truncate">SHA256: {result.sha256.slice(0, 16)}...</p>
        </div>
      )}

      <div className="flex items-start gap-1.5 text-[9px] text-dark-500">
        <AlertTriangle size={10} className="shrink-0 mt-0.5 text-amber-500" />
        <span>Importing a model does not install the LiteRT-LM runtime. If SDK is missing, the file is stored but cannot run yet.</span>
      </div>
    </div>
  );
}
