"use client";

import { useEffect, useState, useCallback } from "react";
import { Cpu, CheckCircle, XCircle, AlertTriangle, RefreshCw } from "lucide-react";

interface LLMStatus {
  configured_provider: string;
  active_provider: string | null;
  model: string | null;
  available: boolean;
  fallback_used: boolean;
  fallback_allowed: boolean;
  error: string | null;
}

const API = "http://localhost:8000/api";

export default function LLMStatusPanel() {
  const [status, setStatus] = useState<LLMStatus | null>(null);
  const [testing, setTesting] = useState(false);
  const [testResult, setTestResult] = useState<string | null>(null);

  const load = useCallback(async () => {
    try {
      const res = await fetch(`${API}/llm/status`);
      setStatus(await res.json());
    } catch { /* ignore */ }
  }, []);

  useEffect(() => { load(); }, [load]);

  const handleTest = async () => {
    setTesting(true);
    setTestResult(null);
    try {
      const res = await fetch(`${API}/llm/test`, { method: "POST" });
      const data = await res.json();
      setTestResult(data.success ? `✓ ${data.response}` : `✗ ${data.error}`);
    } catch (e) {
      setTestResult("✗ Connection failed");
    }
    setTesting(false);
  };

  if (!status) return null;

  return (
    <div className="border-t border-dark-700">
      <div className="panel-header flex items-center gap-2">
        <Cpu size={14} className={status.available ? "text-green-400" : "text-yellow-400"} />
        <span>LLM</span>
        <span className="text-[10px] text-dark-500 ml-auto">{status.active_provider || "none"}</span>
        <button onClick={load} className="text-dark-400 hover:text-dark-200" aria-label="Refresh">
          <RefreshCw size={11} />
        </button>
      </div>
      <div className="p-2 space-y-1 text-xs">
        <div className="flex items-center gap-2">
          {status.available ? (
            <CheckCircle size={11} className="text-green-400" />
          ) : (
            <XCircle size={11} className="text-red-400" />
          )}
          <span className="text-dark-300">
            {status.active_provider || status.configured_provider}
            {status.model ? ` (${status.model})` : ""}
          </span>
        </div>

        {status.fallback_used && (
          <div className="flex items-center gap-2">
            <AlertTriangle size={11} className="text-yellow-400" />
            <span className="text-yellow-400">Fallback active</span>
          </div>
        )}

        {status.error && (
          <p className="text-red-400 text-[10px] truncate">{status.error}</p>
        )}

        <button
          onClick={handleTest}
          disabled={testing}
          className="w-full mt-1 px-2 py-1 rounded bg-dark-800 text-dark-300 hover:bg-dark-700 text-[10px] disabled:opacity-50"
        >
          {testing ? "Testing..." : "Test Model"}
        </button>

        {testResult && (
          <p className={`text-[10px] truncate ${testResult.startsWith("✓") ? "text-green-400" : "text-red-400"}`}>
            {testResult}
          </p>
        )}
      </div>
    </div>
  );
}
