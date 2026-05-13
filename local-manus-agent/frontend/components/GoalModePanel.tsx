"use client";

import { useState } from "react";
import { Target, Rocket, Download, CheckCircle, Loader } from "lucide-react";
import { API } from "@/lib/config";
import { formatSize } from "@/lib/utils";

interface GoalResult {
  task_id: string;
  summary: string;
  template: string;
  files_count: number;
  preview_url: string | null;
  export: { filename: string; size: number } | null;
}

export default function GoalModePanel() {
  const [goal, setGoal] = useState("");
  const [running, setRunning] = useState(false);
  const [result, setResult] = useState<GoalResult | null>(null);
  const [error, setError] = useState("");
  const [phase, setPhase] = useState("");

  const runGoal = async () => {
    if (!goal.trim()) return;
    setRunning(true);
    setResult(null);
    setError("");
    setPhase("Analyzing...");

    try {
      const r = await fetch(`${API}/goals/run`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: goal, mode: "autonomous" }),
      });
      if (!r.ok) throw new Error("Request failed");
      const data = await r.json();

      if (data.type === "goal_completed") {
        setResult(data);
      } else if (data.error) {
        setError(data.error);
      } else {
        setResult(data);
      }
      setPhase("");
    } catch {
      setError("Connection failed");
      setPhase("");
    }
    setRunning(false);
  };

  return (
    <div className="p-4 space-y-4">
      <div className="flex items-center gap-2">
        <Target size={16} className="text-primary" />
        <h3 className="text-sm font-semibold text-dark-200 font-display">Goal Mode</h3>
      </div>

      <p className="text-xs text-dark-400 leading-relaxed">
        Describe what you want to build. The agent will analyze, generate, review, and export automatically.
      </p>

      <textarea
        value={goal}
        onChange={(e) => setGoal(e.target.value)}
        placeholder="e.g. Build a landing page for Aroma Cafe with warm brown colors"
        className="w-full h-20 input-field resize-none text-sm"
        disabled={running}
        aria-label="Goal description"
      />

      <button
        onClick={runGoal}
        disabled={running || !goal.trim()}
        className="w-full btn-primary flex items-center justify-center gap-2"
      >
        {running ? <Loader size={14} className="animate-spin" /> : <Rocket size={14} />}
        {running ? phase || "Running..." : "Run Goal"}
      </button>

      {error && <p className="text-xs text-red-400">{error}</p>}

      {result && (
        <div className="bg-dark-800/40 rounded-xl p-4 space-y-3 border border-dark-700/40 animate-fade-in">
          <div className="flex items-center gap-2">
            <CheckCircle size={14} className="text-emerald-400" />
            <span className="text-xs text-emerald-400 font-semibold">Goal Completed</span>
          </div>

          <p className="text-xs text-dark-300 leading-relaxed">{result.summary}</p>

          <div className="flex flex-wrap gap-2">
            <span className="badge-neutral">Template: {result.template}</span>
            <span className="badge-neutral">Files: {result.files_count}</span>
          </div>

          {result.preview_url && (
            <a href={result.preview_url} target="_blank" rel="noopener noreferrer"
              className="block text-xs text-primary hover:underline">
              🌐 Preview: {result.preview_url}
            </a>
          )}

          {result.export && result.task_id && (
            <a href={`${API}/tasks/${result.task_id}/export/download`}
              className="flex items-center gap-1 text-xs text-emerald-400 hover:underline">
              <Download size={11} /> Download ZIP ({formatSize(result.export.size)})
            </a>
          )}
        </div>
      )}
    </div>
  );
}
