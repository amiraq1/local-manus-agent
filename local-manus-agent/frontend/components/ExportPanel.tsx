"use client";

import { useState, useCallback } from "react";
import { Archive, Download, Loader } from "lucide-react";
import { API } from "@/lib/config";
import { formatSize } from "@/lib/utils";

interface ExportPanelProps {
  taskId: string | null;
}

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
      if (!r.ok) throw new Error("Export failed");
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

  return (
    <div className="flex items-center gap-2 px-3 py-2.5 divider">
      <button
        onClick={handleExport}
        disabled={exporting}
        className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-dark-800/60 hover:bg-dark-800 text-xs text-dark-200 disabled:opacity-50 transition-colors"
      >
        {exporting ? <Loader size={12} className="animate-spin" /> : <Archive size={12} />}
        {exporting ? "Exporting..." : "Export ZIP"}
      </button>

      {result && (
        <a
          href={`${API}/tasks/${taskId}/export/download`}
          className="flex items-center gap-1 px-2.5 py-1 rounded-lg bg-emerald-900/15 text-emerald-400 text-[10px] hover:bg-emerald-900/25 transition-colors"
        >
          <Download size={10} />
          {result.filename} ({formatSize(result.size)})
        </a>
      )}

      {error && <span className="text-[10px] text-red-400">{error}</span>}
    </div>
  );
}
