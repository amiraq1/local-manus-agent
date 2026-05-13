"use client";

import { useEffect, useState, useCallback } from "react";
import { Package, Image, Globe, FileText, Download, Trash2 } from "lucide-react";
import { API } from "@/lib/config";
import { formatSize } from "@/lib/utils";
import ConfirmDialog from "@/components/ConfirmDialog";

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

export default function ArtifactsPanel({ taskId }: ArtifactsPanelProps) {
  const [artifacts, setArtifacts] = useState<Artifact[]>([]);
  const [deleteTarget, setDeleteTarget] = useState<Artifact | null>(null);

  const load = useCallback(async () => {
    if (!taskId) return;
    try {
      const res = await fetch(`${API}/tasks/${taskId}/artifacts`);
      if (!res.ok) return;
      const data = await res.json();
      setArtifacts(data.artifacts || []);
    } catch { /* backend offline */ }
  }, [taskId]);

  useEffect(() => { load(); }, [load]);

  if (!taskId || artifacts.length === 0) return null;

  const typeIcon = (type: string) => {
    switch (type) {
      case "screenshot": return <Image size={12} className="text-violet-400" />;
      case "preview": return <Globe size={12} className="text-cyan-400" />;
      case "report": return <FileText size={12} className="text-amber-400" />;
      default: return <Package size={12} className="text-dark-400" />;
    }
  };

  const handleDelete = async () => {
    if (!deleteTarget) return;
    try {
      const res = await fetch(`${API}/artifacts/${deleteTarget.id}`, { method: "DELETE" });
      if (res.ok) {
        setArtifacts((prev) => prev.filter((a) => a.id !== deleteTarget.id));
      }
    } catch { /* ignore */ }
    setDeleteTarget(null);
  };

  return (
    <>
      <div className="divider max-h-[200px] flex flex-col">
        <div className="panel-header flex items-center gap-2">
          <Package size={14} className="text-primary" />
          <span>Artifacts</span>
          <span className="badge-neutral ml-auto">{artifacts.length}</span>
        </div>
        <div className="flex-1 overflow-y-auto p-2 space-y-0.5">
          {artifacts.map((a) => (
            <div key={a.id} className="flex items-center gap-2 px-2 py-1.5 rounded-lg hover:bg-dark-800/60 text-xs transition-colors group">
              {typeIcon(a.type)}
              <span className="text-dark-200 truncate flex-1">{a.name}</span>
              <span className="text-dark-500 shrink-0">{formatSize(a.size)}</span>
              <a
                href={`${API}/artifacts/${a.id}/download`}
                className="text-dark-400 hover:text-primary shrink-0 opacity-0 group-hover:opacity-100 transition-opacity"
                title="Download"
              >
                <Download size={11} />
              </a>
              <button
                onClick={() => setDeleteTarget(a)}
                className="text-dark-400 hover:text-red-400 shrink-0 opacity-0 group-hover:opacity-100 transition-opacity"
                title="Delete"
                aria-label={`Delete ${a.name}`}
              >
                <Trash2 size={11} />
              </button>
            </div>
          ))}
        </div>
      </div>

      {deleteTarget && (
        <ConfirmDialog
          title="Delete Artifact"
          message={`Are you sure you want to delete "${deleteTarget.name}"? This action cannot be undone.`}
          confirmLabel="Delete"
          onConfirm={handleDelete}
          onCancel={() => setDeleteTarget(null)}
        />
      )}
    </>
  );
}
