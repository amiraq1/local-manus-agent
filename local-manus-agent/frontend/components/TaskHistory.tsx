"use client";

import { History, CheckCircle, XCircle, Loader, Clock } from "lucide-react";
import { TaskSummary } from "@/lib/useAgent";

interface TaskHistoryProps {
  tasks: TaskSummary[];
  currentTaskId: string | null;
  onSelect: (taskId: string) => void;
}

export default function TaskHistory({ tasks, currentTaskId, onSelect }: TaskHistoryProps) {
  if (tasks.length === 0) return null;

  const getStatusIcon = (status: string) => {
    switch (status) {
      case "completed":
        return <CheckCircle size={12} className="text-green-400" />;
      case "failed":
        return <XCircle size={12} className="text-red-400" />;
      case "running":
        return <Loader size={12} className="text-primary animate-spin" />;
      default:
        return <Clock size={12} className="text-dark-500" />;
    }
  };

  const formatTime = (timestamp: number) => {
    const date = new Date(timestamp * 1000);
    const now = new Date();
    const diff = now.getTime() - date.getTime();

    if (diff < 60000) return "just now";
    if (diff < 3600000) return `${Math.floor(diff / 60000)}m ago`;
    if (diff < 86400000) return `${Math.floor(diff / 3600000)}h ago`;
    return date.toLocaleDateString();
  };

  return (
    <div className="border-b border-dark-700 max-h-[180px] overflow-y-auto">
      <div className="panel-header flex items-center gap-2">
        <History size={14} />
        <span>Task History</span>
        <span className="text-xs text-dark-500 ml-auto">{tasks.length}</span>
      </div>
      <div className="p-2 space-y-0.5">
        {tasks.slice(0, 20).map((task) => (
          <button
            key={task.id}
            onClick={() => onSelect(task.id)}
            className={`w-full text-left flex items-start gap-2 px-2 py-1.5 rounded text-sm transition-colors ${
              currentTaskId === task.id
                ? "bg-primary/10 border border-primary/20"
                : "hover:bg-dark-800"
            }`}
          >
            <div className="mt-0.5 shrink-0">{getStatusIcon(task.status)}</div>
            <div className="flex-1 min-w-0">
              <p className="text-dark-200 truncate text-xs">{task.message}</p>
              <div className="flex items-center gap-2 mt-0.5">
                <span className="text-[10px] text-dark-500">{formatTime(task.created_at)}</span>
                <span className={`text-[10px] px-1 rounded ${
                  task.mode === "safe" ? "bg-green-900/30 text-green-400" : "bg-orange-900/30 text-orange-400"
                }`}>
                  {task.mode}
                </span>
              </div>
            </div>
          </button>
        ))}
      </div>
    </div>
  );
}
