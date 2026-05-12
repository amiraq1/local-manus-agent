"use client";

import { useState } from "react";
import { Target, Rocket, Download, CheckCircle, Loader } from "lucide-react";

const API = "http://localhost:8000/api";

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
      const data = await r.json();

      if (data.type === "goal_completed") {
        setResult(data);
        setPhase("");
      } else if (data.error) {
        setError(data.error);
        setPhase("");
      } else {
        setResult(data);
        setPhase("");
      }
    } catch {
      setError("Connection failed");
      setPhase("");
    }
    setRunning(false);
  };

  const formatSize = (bytes: number) => {
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
  };

  return (
    <div className="p-4 space-y-4">
      <div className="flex items-center gap-2">
        <Target size={16} className="text-primary" />
        <h3 className="text-sm font-semibold text-dark-200">Goal Mode</h3>
      </div>

      <p className="text-xs text-dark-400">
        Describe what you want to build. The agent will analyze, generate, review, and export automatically.
      </p>

      <textarea
        value={goal}
        onChange={(e) => setGoal(e.target.value)}
        placeholder="e.g. Build a landing page for Aroma Cafe with warm brown colors"
        className="w-full h-20 bg-dark-800 border border-dark-600 rounded-lg px-3 py-2 text-sm text-dark-200 placeholder-dark-500 resize-none focus:outline-none focus:border-primary"
        disabled={running}
      />

      <button
        onClick={runGoal}
        disabled={running || !goal.trim()}
        className="w-full flex items-center justify-center gap-2 px-4 py-2 rounded-lg bg-primary text-white font-medium text-sm disabled:opacity-50"
      >
        {running ? <Loader size={14} className="animate-spin" /> : <Rocket size={14} />}
        {running ? phase || "Running..." : "Run Goal"}
      </button>

      {error && <p className="text-xs text-red-400">{error}</p>}

      {result && (
        <div className="bg-dark-800/50 rounded-lg p-3 space-y-2">
          <div className="flex items-center gap-2">
            <CheckCircle size={14} className="text-green-400" />
            <span className="text-xs text-green-400 font-medium">Goal Completed</span>
          </div>

          <p className="text-xs text-dark-300">{result.summary}</p>

          <div className="flex flex-wrap gap-2 text-[10px]">
            <span className="px-2 py-0.5 bg-dark-700 rounded text-dark-300">
              Template: {result.template}
            </span>
            <span className="px-2 py-0.5 bg-dark-700 rounded text-dark-300">
              Files: {result.files_count}
            </span>
          </div>

          {result.preview_url && (
            <a href={result.preview_url} target="_blank" rel="noopener noreferrer"
              className="block text-xs text-primary hover:underline">
              🌐 Preview: {result.preview_url}
            </a>
          )}

          {result.export && result.task_id && (
            <a href={`${API}/tasks/${result.task_id}/export/download`}
              className="flex items-center gap-1 text-xs text-green-400 hover:underline">
              <Download size={11} /> Download ZIP ({formatSize(result.export.size)})
            </a>
          )}
        </div>
      )}
    </div>
  );
}
