"use client";

import { useState } from "react";
import { GitBranch, Check, X, ChevronDown, ChevronRight } from "lucide-react";

export interface FileChange {
  id: string;
  task_id: string;
  path: string;
  diff: string;
  status: "pending" | "accepted" | "rejected" | "applied";
  created_at: number;
}

interface FileDiffPanelProps {
  changes: FileChange[];
  onAccept: (changeId: string) => void;
  onReject: (changeId: string) => void;
}

export default function FileDiffPanel({ changes, onAccept, onReject }: FileDiffPanelProps) {
  const [expandedId, setExpandedId] = useState<string | null>(null);

  if (changes.length === 0) return null;

  const statusBadge = (status: string) => {
    switch (status) {
      case "pending": return "badge-warning";
      case "accepted": case "applied": return "badge-success";
      case "rejected": return "badge-danger";
      default: return "badge-neutral";
    }
  };

  const renderDiff = (diff: string) => {
    if (!diff) return <p className="text-dark-500 text-xs">No changes</p>;
    const lines = diff.split("\n");
    return (
      <div className="font-mono text-[11px] leading-relaxed overflow-x-auto max-h-[200px] overflow-y-auto">
        {lines.map((line, i) => {
          let cls = "text-dark-300";
          if (line.startsWith("+") && !line.startsWith("+++")) cls = "text-emerald-400 bg-emerald-900/10";
          else if (line.startsWith("-") && !line.startsWith("---")) cls = "text-red-400 bg-red-900/10";
          else if (line.startsWith("@@")) cls = "text-cyan-400";
          else if (line.startsWith("---") || line.startsWith("+++")) cls = "text-dark-500";
          return (
            <div key={i} className={`px-2 ${cls}`}>
              {line || " "}
            </div>
          );
        })}
      </div>
    );
  };

  return (
    <div className="divider max-h-[300px] flex flex-col">
      <div className="panel-header flex items-center gap-2">
        <GitBranch size={14} className="text-primary" />
        <span>File Changes</span>
        <span className="badge-warning ml-auto">
          {changes.filter(c => c.status === "pending").length} pending
        </span>
      </div>
      <div className="flex-1 overflow-y-auto p-2 space-y-1">
        {changes.map((change) => (
          <div key={change.id} className="rounded-lg bg-dark-800/40 overflow-hidden border border-dark-700/40">
            <button
              onClick={() => setExpandedId(expandedId === change.id ? null : change.id)}
              className="w-full flex items-center gap-2 px-3 py-2 text-left hover:bg-dark-800/60 transition-colors"
              aria-expanded={expandedId === change.id}
            >
              {expandedId === change.id ? (
                <ChevronDown size={12} className="text-dark-400 shrink-0" />
              ) : (
                <ChevronRight size={12} className="text-dark-400 shrink-0" />
              )}
              <span className="text-xs text-dark-200 truncate flex-1 font-mono">{change.path}</span>
              <span className={statusBadge(change.status)}>{change.status}</span>
            </button>

            {expandedId === change.id && (
              <div className="border-t border-dark-700/40 animate-fade-in">
                <div className="bg-dark-950/50 p-1">{renderDiff(change.diff)}</div>
                {change.status === "pending" && (
                  <div className="flex gap-1.5 p-2 border-t border-dark-700/40">
                    <button
                      onClick={() => onAccept(change.id)}
                      className="flex items-center gap-1 px-3 py-1.5 rounded-lg text-xs bg-emerald-600/15 text-emerald-400 hover:bg-emerald-600/25 transition-colors"
                    >
                      <Check size={11} /> Accept
                    </button>
                    <button
                      onClick={() => onReject(change.id)}
                      className="flex items-center gap-1 px-3 py-1.5 rounded-lg text-xs bg-red-600/15 text-red-400 hover:bg-red-600/25 transition-colors"
                    >
                      <X size={11} /> Reject
                    </button>
                  </div>
                )}
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}
