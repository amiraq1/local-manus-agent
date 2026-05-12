"use client";

import { useEffect, useState, useCallback } from "react";
import { Package, Image, Globe, FileText, Download, Trash2 } from "lucide-react";

interface Artifact {
  id: string;
  task_id: string;
  type: string;
  name: string;
  path: string;
  mime_type: string | null;
  size: number;
  created_at: number;
}

interface ArtifactsPanelProps {
  taskId: string | null;
}

const API = "http://localhost:8000/api";

export default function ArtifactsPanel({ taskId }: ArtifactsPanelProps) {
  const [artifacts, setArtifacts] = useState<Artifact[]>([]);

  const load = useCallback(async () => {
    if (!taskId) return;
    try {
      const res = await fetch(`${API}/tasks/${taskId}/artifacts`);
      const data = await res.json();
      setArtifacts(data.artifacts || []);
    } catch { /* ignore */ }
  }, [taskId]);

  useEffect(() => { load(); }, [load]);

  if (!taskId || artifacts.length === 0) return null;

  const typeIcon = (type: string) => {
    switch (type) {
      case "screenshot": return <Image size={12} className="text-purple-400" />;
      case "preview": return <Globe size={12} className="text-cyan-400" />;
      case "report": return <FileText size={12} className="text-yellow-400" />;
      default: return <Package size={12} className="text-dark-400" />;
    }
  };

  const formatSize = (bytes: number) => {
    if (bytes < 1024) return `${bytes}B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)}KB`;
    return `${(bytes / (1024 * 1024)).toFixed(1)}MB`;
  };

  const handleDelete = async (id: string) => {
    await fetch(`${API}/artifacts/${id}`, { method: "DELETE" });
    setArtifacts((prev) => prev.filter((a) => a.id !== id));
  };

  return (
    <div className="border-t border-dark-700 max-h-[200px] flex flex-col">
      <div className="panel-header flex items-center gap-2">
        <Package size={14} />
        <span>Artifacts</span>
        <span className="text-xs text-dark-500 ml-auto">{artifacts.length}</span>
      </div>
      <div className="flex-1 overflow-y-auto p-2 space-y-0.5">
        {artifacts.map((a) => (
          <div key={a.id} className="flex items-center gap-2 px-2 py-1 rounded hover:bg-dark-800 text-xs">
            {typeIcon(a.type)}
            <span className="text-dark-200 truncate flex-1">{a.name}</span>
            <span className="text-dark-500 shrink-0">{formatSize(a.size)}</span>
            <a
              href={`${API}/artifacts/${a.id}/download`}
              className="text-dark-400 hover:text-primary shrink-0"
              title="Download"
            >
              <Download size={11} />
            </a>
            <button
              onClick={() => handleDelete(a.id)}
              className="text-dark-400 hover:text-red-400 shrink-0"
              title="Delete"
              aria-label={`Delete ${a.name}`}
            >
              <Trash2 size={11} />
            </button>
          </div>
        ))}
      </div>
    </div>
  );
}
