"use client";

import { useState, useCallback } from "react";
import { Archive, Download, Loader } from "lucide-react";

interface ExportPanelProps {
  taskId: string | null;
}

const API = "http://localhost:8000/api";

export default function ExportPanel({ taskId }: ExportPanelProps) {
  const [exporting, setExporting] = useState(false);
  const [result, setResult] = useState<{ filename: string; size: number } | null>(null);
  const [error, setError] = useState("");

  const handleExport = useCallback(async () => {
    if (!taskId) return;
    setExporting(true);
    setError("");
    setResult(null);
    try {
      const r = await fetch(`${API}/tasks/${taskId}/export`, { method: "POST" });
      const data = await r.json();
      if (data.success) {
        setResult({ filename: data.filename, size: data.size });
      } else {
        setError(data.error || "Export failed");
      }
    } catch {
      setError("Connection failed");
    }
    setExporting(false);
  }, [taskId]);

  if (!taskId) return null;

  const formatSize = (bytes: number) => {
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
  };

  return (
    <div className="flex items-center gap-2 px-3 py-2 border-t border-dark-700">
      <button
        onClick={handleExport}
        disabled={exporting}
        className="flex items-center gap-1.5 px-3 py-1.5 rounded bg-dark-800 hover:bg-dark-700 text-xs text-dark-200 disabled:opacity-50"
      >
        {exporting ? <Loader size={12} className="animate-spin" /> : <Archive size={12} />}
        {exporting ? "Exporting..." : "Export ZIP"}
      </button>

      {result && (
        <a
          href={`${API}/tasks/${taskId}/export/download`}
          className="flex items-center gap-1 px-2 py-1 rounded bg-green-900/20 text-green-400 text-[10px] hover:bg-green-900/30"
        >
          <Download size={10} />
          {result.filename} ({formatSize(result.size)})
        </a>
      )}

      {error && <span className="text-[10px] text-red-400">{error}</span>}
    </div>
  );
}
