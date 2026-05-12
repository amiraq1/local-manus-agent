"use client";

import { useEffect, useState, useCallback } from "react";
import { Download, CheckCircle, XCircle, Copy, FolderOpen } from "lucide-react";

interface ModelInfo {
  id: string;
  name: string;
  provider: string;
  path: string;
  exists: boolean;
  file_size: number;
  estimated_size: string;
  status: string;
  license_note: string;
}

interface DownloadInfo {
  commands: string[];
  license_note: string;
  estimated_size: string;
  recommended_path: string;
}

const API = "http://localhost:8000/api";

export default function ModelManagerPanel() {
  const [models, setModels] = useState<ModelInfo[]>([]);
  const [downloadInfo, setDownloadInfo] = useState<DownloadInfo | null>(null);
  const [selectedModel, setSelectedModel] = useState<string | null>(null);
  const [pathInput, setPathInput] = useState("");
  const [msg, setMsg] = useState("");

  const load = useCallback(async () => {
    try {
      const r = await fetch(`${API}/models/status`);
      const data = await r.json();
      setModels(data.models || []);
    } catch { /* ignore */ }
  }, []);

  useEffect(() => { load(); }, [load]);

  const showDownload = async (modelId: string) => {
    setSelectedModel(modelId);
    try {
      const r = await fetch(`${API}/models/download-instructions?model_id=${modelId}`);
      setDownloadInfo(await r.json());
    } catch { /* ignore */ }
  };

  const copyCommands = (commands: string[]) => {
    navigator.clipboard.writeText(commands.join("\n")).then(() => setMsg("Copied!"));
    setTimeout(() => setMsg(""), 2000);
  };

  const setPath = async (modelId: string) => {
    if (!pathInput.trim()) return;
    await fetch(`${API}/models/set-path`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ model_id: modelId, path: pathInput }),
    });
    setPathInput("");
    setMsg("Path saved");
    load();
    setTimeout(() => setMsg(""), 2000);
  };

  return (
    <div className="p-3 space-y-3">
      <h3 className="text-sm font-medium text-dark-200 flex items-center gap-2">
        <Download size={14} /> Model Manager
      </h3>

      {models.map((m) => (
        <div key={m.id} className="bg-dark-800/50 rounded-lg p-3 space-y-2">
          <div className="flex items-center gap-2">
            {m.exists ? <CheckCircle size={12} className="text-green-400" /> : <XCircle size={12} className="text-dark-500" />}
            <span className="text-xs text-dark-200 font-medium">{m.name}</span>
            <span className={`text-[9px] px-1.5 py-0.5 rounded ml-auto ${
              m.status === "ready" ? "bg-green-900/30 text-green-400" : "bg-dark-700 text-dark-400"
            }`}>{m.status}</span>
          </div>

          <div className="text-[10px] text-dark-500 space-y-0.5">
            <p>Size: {m.exists ? `${(m.file_size / 1e9).toFixed(1)} GB` : m.estimated_size}</p>
            {m.path && <p className="font-mono truncate">Path: {m.path}</p>}
          </div>

          {!m.exists && m.id !== "litert-custom" && (
            <button
              onClick={() => showDownload(m.id)}
              className="text-[10px] text-primary hover:underline"
            >
              Show download instructions
            </button>
          )}

          {/* Set path input */}
          {!m.exists && (
            <div className="flex gap-1">
              <input
                type="text"
                placeholder="Set model path..."
                value={selectedModel === m.id ? pathInput : ""}
                onChange={(e) => { setSelectedModel(m.id); setPathInput(e.target.value); }}
                className="flex-1 bg-dark-900 border border-dark-600 rounded px-2 py-0.5 text-[10px] text-dark-200"
              />
              <button
                onClick={() => setPath(m.id)}
                className="px-2 py-0.5 bg-primary/20 text-primary rounded text-[10px]"
              >
                Set
              </button>
            </div>
          )}
        </div>
      ))}

      {/* Download instructions modal */}
      {downloadInfo && selectedModel && (
        <div className="bg-dark-900 border border-dark-600 rounded-lg p-3 space-y-2">
          <div className="flex items-center justify-between">
            <span className="text-xs text-dark-200 font-medium">Download Instructions</span>
            <button onClick={() => setDownloadInfo(null)} className="text-dark-400 text-xs">✕</button>
          </div>

          {downloadInfo.license_note && (
            <p className="text-[10px] text-yellow-400 bg-yellow-900/10 p-2 rounded">
              ⚠️ {downloadInfo.license_note}
            </p>
          )}

          <div className="bg-dark-950 rounded p-2 font-mono text-[10px] text-green-400 space-y-0.5">
            {downloadInfo.commands.map((cmd, i) => (
              <p key={i}>{cmd}</p>
            ))}
          </div>

          <button
            onClick={() => copyCommands(downloadInfo.commands)}
            className="flex items-center gap-1 text-[10px] text-primary hover:underline"
          >
            <Copy size={10} /> Copy commands
          </button>
        </div>
      )}

      {msg && <p className="text-[10px] text-green-400">{msg}</p>}
    </div>
  );
}
