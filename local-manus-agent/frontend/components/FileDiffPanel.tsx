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

  const statusColor = (status: string) => {
    switch (status) {
      case "pending": return "text-yellow-400 bg-yellow-900/20";
      case "accepted": case "applied": return "text-green-400 bg-green-900/20";
      case "rejected": return "text-red-400 bg-red-900/20";
      default: return "text-dark-400 bg-dark-800";
    }
  };

  const renderDiff = (diff: string) => {
    if (!diff) return <p className="text-dark-500 text-xs">No changes</p>;
    const lines = diff.split("\n");
    return (
      <div className="font-mono text-[11px] leading-relaxed overflow-x-auto max-h-[200px] overflow-y-auto">
        {lines.map((line, i) => {
          let cls = "text-dark-300";
          if (line.startsWith("+") && !line.startsWith("+++")) cls = "text-green-400 bg-green-900/10";
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
    <div className="border-t border-dark-700 max-h-[300px] flex flex-col">
      <div className="panel-header flex items-center gap-2">
        <GitBranch size={14} />
        <span>File Changes</span>
        <span className="text-xs text-dark-500 ml-auto">
          {changes.filter(c => c.status === "pending").length} pending
        </span>
      </div>
      <div className="flex-1 overflow-y-auto p-2 space-y-1">
        {changes.map((change) => (
          <div key={change.id} className="rounded bg-dark-800/50 overflow-hidden">
            {/* Header */}
            <button
              onClick={() => setExpandedId(expandedId === change.id ? null : change.id)}
              className="w-full flex items-center gap-2 px-2 py-1.5 text-left hover:bg-dark-800"
            >
              {expandedId === change.id ? (
                <ChevronDown size={12} className="text-dark-400 shrink-0" />
              ) : (
                <ChevronRight size={12} className="text-dark-400 shrink-0" />
              )}
              <span className="text-xs text-dark-200 truncate flex-1">{change.path}</span>
              <span className={`text-[10px] px-1.5 py-0.5 rounded ${statusColor(change.status)}`}>
                {change.status}
              </span>
            </button>

            {/* Expanded diff + actions */}
            {expandedId === change.id && (
              <div className="border-t border-dark-700">
                <div className="bg-dark-950 p-1">
                  {renderDiff(change.diff)}
                </div>
                {change.status === "pending" && (
                  <div className="flex gap-1 p-2 border-t border-dark-700">
                    <button
                      onClick={() => onAccept(change.id)}
                      className="flex items-center gap-1 px-2 py-1 rounded text-xs bg-green-600/20 text-green-400 hover:bg-green-600/30"
                    >
                      <Check size={11} /> Accept
                    </button>
                    <button
                      onClick={() => onReject(change.id)}
                      className="flex items-center gap-1 px-2 py-1 rounded text-xs bg-red-600/20 text-red-400 hover:bg-red-600/30"
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
