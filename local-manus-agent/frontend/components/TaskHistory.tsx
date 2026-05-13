"use client";

import { History, CheckCircle, XCircle, Loader, Clock } from "lucide-react";
import { TaskSummary } from "@/lib/useAgent";
import { formatTime } from "@/lib/utils";

interface TaskHistoryProps {
  tasks: TaskSummary[];
  currentTaskId: string | null;
  onSelect: (taskId: string) => void;
}

export default function TaskHistory({ tasks, currentTaskId, onSelect }: TaskHistoryProps) {
  if (tasks.length === 0) return null;

  const getStatusIcon = (status: string) => {
    switch (status) {
      case "completed": return <CheckCircle size={12} className="text-emerald-400" />;
      case "failed": return <XCircle size={12} className="text-red-400" />;
      case "running": return <Loader size={12} className="text-primary animate-spin" />;
      default: return <Clock size={12} className="text-dark-500" />;
    }
  };

  return (
    <div className="border-b border-dark-700/60 max-h-[180px] overflow-y-auto" role="list" aria-label="Task history">
      <div className="panel-header flex items-center gap-2">
        <History size={14} className="text-primary" />
        <span>Task History</span>
        <span className="badge-neutral ml-auto">{tasks.length}</span>
      </div>
      <div className="p-2 space-y-0.5">
        {tasks.slice(0, 20).map((task) => (
          <button
            key={task.id}
            role="listitem"
            onClick={() => onSelect(task.id)}
            className={`w-full text-left flex items-start gap-2 px-2.5 py-2 rounded-lg text-sm transition-all duration-200 ${
              currentTaskId === task.id
                ? "bg-primary/8 border border-primary/15"
                : "hover:bg-dark-800/60 border border-transparent"
            }`}
          >
            <div className="mt-0.5 shrink-0">{getStatusIcon(task.status)}</div>
            <div className="flex-1 min-w-0">
              <p className="text-dark-200 truncate text-xs">{task.message}</p>
              <div className="flex items-center gap-2 mt-0.5">
                <span className="text-[10px] text-dark-500">{formatTime(task.created_at)}</span>
                <span className={task.mode === "safe" ? "badge-success" : "badge-warning"}>
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
