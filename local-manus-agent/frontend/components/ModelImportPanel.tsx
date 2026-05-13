"use client";

import { useState, useRef } from "react";
import { Upload, X, CheckCircle, AlertTriangle, Play, MousePointerClick } from "lucide-react";
import { API } from "@/lib/config";
import { formatSize } from "@/lib/utils";

const CHUNK_SIZE = 50 * 1024 * 1024; // 50MB

export default function ModelImportPanel() {
  const [file, setFile] = useState<File | null>(null);
  const [modelName, setModelName] = useState("");
  const [uploading, setUploading] = useState(false);
  const [progress, setProgress] = useState(0);
  const [chunksUploaded, setChunksUploaded] = useState(0);
  const [totalChunks, setTotalChunks] = useState(0);
  const [result, setResult] = useState<{ name: string; size: number; sha256: string; path: string; model_id: string } | null>(null);
  const [error, setError] = useState("");
  const [cancelled, setCancelled] = useState(false);
  const [selectMsg, setSelectMsg] = useState("");
  const fileRef = useRef<HTMLInputElement>(null);
  const importIdRef = useRef<string>("");

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
    setCancelled(false);
    setChunksUploaded(0);

    try {
      const startRes = await fetch(`${API}/models/import/start`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ filename: file.name, size: file.size, model_name: modelName }),
      });
      const startData = await startRes.json();
      if (!startData.accepted) { setError(startData.error || "Import rejected"); setUploading(false); return; }

      const importId = startData.import_id;
      importIdRef.current = importId;
      const chunks = startData.total_chunks;
      setTotalChunks(chunks);

      for (let i = 0; i < chunks; i++) {
        if (cancelled) {
          await fetch(`${API}/models/import/${importId}`, { method: "DELETE" });
          setUploading(false);
          return;
        }

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
        setChunksUploaded(i + 1);
        setProgress(Math.round(((i + 1) / chunks) * 100));
      }

      const finishRes = await fetch(`${API}/models/import/finish`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ import_id: importId }),
      });
      const finishData = await finishRes.json();
      if (finishData.success) {
        setResult({ name: finishData.name, size: finishData.size, sha256: finishData.sha256, path: finishData.path, model_id: finishData.model_id });
      } else {
        setError(finishData.error || "Finish failed");
      }
    } catch {
      setError("Upload failed");
    }
    setUploading(false);
  };

  const handleCancel = async () => {
    setCancelled(true);
    if (importIdRef.current) {
      await fetch(`${API}/models/import/${importIdRef.current}`, { method: "DELETE" });
    }
    setUploading(false);
    setProgress(0);
    setChunksUploaded(0);
  };

  const handleSelectModel = async () => {
    if (!result) return;
    try {
      await fetch(`${API}/models/set-path`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ model_id: "litert-custom", path: result.path }),
      });
      setSelectMsg("Model selected as active");
      setTimeout(() => setSelectMsg(""), 3000);
    } catch {
      setSelectMsg("Failed to select model");
    }
  };

  const handleTestModel = async () => {
    if (!result) return;
    try {
      const res = await fetch(`${API}/llm/litert/test-cli`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ prompt: "Hello" }),
      });
      const data = await res.json();
      setSelectMsg(data.success ? `Test OK: "${data.output?.slice(0, 60)}..."` : `Test failed: ${data.error}`);
      setTimeout(() => setSelectMsg(""), 5000);
    } catch {
      setSelectMsg("Test request failed");
    }
  };

  return (
    <div className="p-3 space-y-3 divider">
      <h4 className="text-xs font-medium text-dark-200 flex items-center gap-2 font-display">
        <Upload size={13} className="text-primary" /> Import .litertlm Model
      </h4>

      <p className="text-[10px] text-dark-500 leading-relaxed">
        Models are not bundled with Local Manus Agent. Select a .litertlm file from your device to import it.
      </p>

      {/* Cloudflare Tunnel warning */}
      <div className="flex items-start gap-1.5 text-[9px] text-amber-400/90 bg-amber-900/10 border border-amber-700/20 rounded p-2">
        <AlertTriangle size={10} className="shrink-0 mt-0.5" />
        <span>For large models like Gemma E2B, open the site locally via <span className="font-mono">http://localhost:3000</span> instead of Cloudflare Tunnel.</span>
      </div>

      {/* File picker */}
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
          <div className="flex items-center justify-between">
            <p className="text-[10px] text-dark-400">{chunksUploaded}/{totalChunks} chunks — {progress}%</p>
            <button onClick={handleCancel} className="flex items-center gap-1 text-[10px] text-red-400 hover:text-red-300">
              <X size={10} /> Cancel
            </button>
          </div>
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
          <div className="text-[10px] text-dark-300 space-y-0.5">
            <p><span className="text-dark-500">Name:</span> {result.name}</p>
            <p><span className="text-dark-500">Size:</span> {formatSize(result.size)}</p>
            <p className="font-mono truncate"><span className="text-dark-500">Path:</span> {result.path}</p>
            <p className="font-mono truncate"><span className="text-dark-500">SHA256:</span> {result.sha256}</p>
          </div>
          <div className="flex gap-2 pt-1">
            <button onClick={handleSelectModel} className="flex items-center gap-1 px-2 py-1 rounded bg-primary/20 text-primary text-[10px] hover:bg-primary/30 transition-colors">
              <MousePointerClick size={10} /> Select Model
            </button>
            <button onClick={handleTestModel} className="flex items-center gap-1 px-2 py-1 rounded bg-dark-700 text-dark-200 text-[10px] hover:bg-dark-600 transition-colors">
              <Play size={10} /> Test Model
            </button>
          </div>
          {selectMsg && <p className="text-[10px] text-green-400">{selectMsg}</p>}
        </div>
      )}

      <div className="flex items-start gap-1.5 text-[9px] text-dark-500">
        <AlertTriangle size={10} className="shrink-0 mt-0.5 text-amber-500" />
        <span>Importing a model does not install the LiteRT-LM runtime. If SDK is missing, the file is stored but cannot run yet.</span>
      </div>
    </div>
  );
}
