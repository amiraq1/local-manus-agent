"use client";

import { useEffect, useState, useCallback } from "react";
import { Download, CheckCircle, XCircle, Copy } from "lucide-react";
import { API } from "@/lib/config";
import { formatSize } from "@/lib/utils";

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

export default function ModelManagerPanel() {
  const [models, setModels] = useState<ModelInfo[]>([]);
  const [downloadInfo, setDownloadInfo] = useState<DownloadInfo | null>(null);
  const [selectedModel, setSelectedModel] = useState<string | null>(null);
  const [pathInput, setPathInput] = useState("");
  const [msg, setMsg] = useState("");

  const load = useCallback(async () => {
    try {
      const r = await fetch(`${API}/models/status`);
      if (r.ok) { const data = await r.json(); setModels(data.models || []); }
    } catch { /* offline */ }
  }, []);

  useEffect(() => { load(); }, [load]);

  const showDownload = async (modelId: string) => {
    setSelectedModel(modelId);
    try {
      const r = await fetch(`${API}/models/download-instructions?model_id=${modelId}`);
      if (r.ok) setDownloadInfo(await r.json());
    } catch { /* offline */ }
  };

  const copyCommands = (commands: string[]) => {
    navigator.clipboard.writeText(commands.join("\n")).then(() => setMsg("Copied!"));
    setTimeout(() => setMsg(""), 2000);
  };

  const setPath = async (modelId: string) => {
    if (!pathInput.trim()) return;
    try {
      await fetch(`${API}/models/set-path`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ model_id: modelId, path: pathInput }),
      });
      setPathInput("");
      setMsg("Path saved");
      load();
    } catch { /* ignore */ }
    setTimeout(() => setMsg(""), 2000);
  };

  return (
    <div className="p-3 space-y-3">
      <h3 className="text-sm font-medium text-dark-200 flex items-center gap-2 font-display">
        <Download size={14} className="text-primary" /> Model Manager
      </h3>

      {models.map((m) => (
        <div key={m.id} className="bg-dark-800/40 rounded-xl p-3 space-y-2 border border-dark-700/40">
          <div className="flex items-center gap-2">
            {m.exists ? <CheckCircle size={12} className="text-emerald-400" /> : <XCircle size={12} className="text-dark-500" />}
            <span className="text-xs text-dark-200 font-medium">{m.name}</span>
            <span className={`ml-auto ${m.status === "ready" ? "badge-success" : "badge-neutral"}`}>{m.status}</span>
          </div>

          <div className="text-[10px] text-dark-500 space-y-0.5">
            <p>Size: {m.exists ? formatSize(m.file_size) : m.estimated_size}</p>
            {m.path && <p className="font-mono truncate">Path: {m.path}</p>}
          </div>

          {!m.exists && m.id !== "litert-custom" && (
            <button onClick={() => showDownload(m.id)} className="text-[10px] text-primary hover:underline">
              Show download instructions
            </button>
          )}

          {!m.exists && (
            <div className="flex gap-1.5">
              <input
                type="text"
                placeholder="Set model path..."
                value={selectedModel === m.id ? pathInput : ""}
                onChange={(e) => { setSelectedModel(m.id); setPathInput(e.target.value); }}
                className="flex-1 bg-dark-900/60 border border-dark-700 rounded-lg px-2.5 py-1 text-[10px] text-dark-200 focus:outline-none focus:border-primary/40"
              />
              <button onClick={() => setPath(m.id)} className="px-2.5 py-1 bg-primary/15 text-primary rounded-lg text-[10px] hover:bg-primary/20 transition-colors">
                Set
              </button>
            </div>
          )}
        </div>
      ))}

      {downloadInfo && selectedModel && (
        <div className="bg-dark-900/80 border border-dark-600 rounded-xl p-3 space-y-2 animate-scale-in">
          <div className="flex items-center justify-between">
            <span className="text-xs text-dark-200 font-medium font-display">Download Instructions</span>
            <button onClick={() => setDownloadInfo(null)} className="text-dark-400 text-xs hover:text-dark-200 transition-colors">✕</button>
          </div>

          {downloadInfo.license_note && (
            <p className="text-[10px] text-amber-400 bg-amber-900/10 p-2 rounded-lg border border-amber-700/20">
              ⚠️ {downloadInfo.license_note}
            </p>
          )}

          <div className="bg-dark-950/60 rounded-lg p-2.5 font-mono text-[10px] text-primary space-y-0.5">
            {downloadInfo.commands.map((cmd, i) => (<p key={i}>{cmd}</p>))}
          </div>

          <button onClick={() => copyCommands(downloadInfo.commands)}
            className="flex items-center gap-1 text-[10px] text-primary hover:underline">
            <Copy size={10} /> Copy commands
          </button>
        </div>
      )}

      {msg && <p className="text-[10px] text-emerald-400">{msg}</p>}
    </div>
  );
}
