"use client";

import { useEffect, useState, useCallback } from "react";
import { Cpu, CheckCircle, XCircle, AlertTriangle, RefreshCw } from "lucide-react";

interface LLMStatus {
  configured_provider: string;
  active_provider: string | null;
  model: string | null;
  available: boolean;
  fallback_used: boolean;
  error: string | null;
}

interface Preset {
  id: string;
  name: string;
  provider: string;
  description: string;
  active: boolean;
  model_available: boolean;
  model_path?: string;
  download_instructions?: string;
}

const API = "http://localhost:8000/api";

export default function LLMStatusPanel() {
  const [status, setStatus] = useState<LLMStatus | null>(null);
  const [presets, setPresets] = useState<Preset[]>([]);
  const [activePreset, setActivePreset] = useState("");
  const [testing, setTesting] = useState(false);
  const [testResult, setTestResult] = useState<string | null>(null);
  const [selectMsg, setSelectMsg] = useState<string | null>(null);

  const load = useCallback(async () => {
    try {
      const [sRes, pRes] = await Promise.all([
        fetch(`${API}/llm/status`),
        fetch(`${API}/llm/presets`),
      ]);
      setStatus(await sRes.json());
      const pData = await pRes.json();
      setPresets(pData.presets || []);
      setActivePreset(pData.active || "");
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
    } catch {
      setTestResult("✗ Connection failed");
    }
    setTesting(false);
  };

  const handleSelect = async (presetId: string) => {
    setSelectMsg(null);
    try {
      const res = await fetch(`${API}/llm/select-preset`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ preset: presetId }),
      });
      const data = await res.json();
      if (data.success) {
        setSelectMsg(`✓ Switched to ${presetId}`);
        load();
      } else {
        setSelectMsg(data.error || data.message || data.hint || "Failed");
      }
    } catch {
      setSelectMsg("Connection failed");
    }
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
      <div className="p-2 space-y-2 text-xs">
        {/* Status */}
        <div className="flex items-center gap-2">
          {status.available ? <CheckCircle size={11} className="text-green-400" /> : <XCircle size={11} className="text-red-400" />}
          <span className="text-dark-300">{status.active_provider}{status.model ? ` (${status.model})` : ""}</span>
        </div>
        {status.fallback_used && (
          <div className="flex items-center gap-1 text-yellow-400">
            <AlertTriangle size={10} /> <span>Fallback active</span>
          </div>
        )}

        {/* Preset selector */}
        <div className="space-y-1 pt-1 border-t border-dark-700">
          <p className="text-[10px] text-dark-500">Model Preset:</p>
          {presets.map((p) => (
            <button
              key={p.id}
              onClick={() => handleSelect(p.id)}
              className={`w-full text-left px-2 py-1 rounded text-[11px] flex items-center gap-1.5 ${
                p.id === activePreset ? "bg-primary/10 border border-primary/30 text-primary" : "bg-dark-800 text-dark-300 hover:bg-dark-700"
              }`}
            >
              <span className={`w-1.5 h-1.5 rounded-full ${p.model_available ? "bg-green-400" : "bg-dark-500"}`} />
              <span className="flex-1 truncate">{p.name}</span>
              {p.id === activePreset && <span className="text-[9px]">active</span>}
            </button>
          ))}
        </div>

        {selectMsg && (
          <p className={`text-[10px] ${selectMsg.startsWith("✓") ? "text-green-400" : "text-yellow-400"}`}>
            {selectMsg}
          </p>
        )}

        {/* Test */}
        <button
          onClick={handleTest}
          disabled={testing}
          className="w-full px-2 py-1 rounded bg-dark-800 text-dark-300 hover:bg-dark-700 text-[10px] disabled:opacity-50"
        >
          {testing ? "Testing..." : "Test Model"}
        </button>
        {testResult && (
          <p className={`text-[10px] truncate ${testResult.startsWith("✓") ? "text-green-400" : "text-red-400"}`}>
            {testResult}
          </p>
        )}

        {/* Diagnose LiteRT */}
        <button
          onClick={async () => {
            try {
              const r = await fetch(`${API}/llm/litert/diagnostics`);
              const d = await r.json();
              const lines = [
                `SDK: ${d.sdk_installed ? "✓ " + d.sdk_module : "✗ not installed"}`,
                `Model: ${d.model_path_exists ? "✓ " + d.model_path : "✗ not found"}`,
                `Runtime: ${d.runtime_available ? "✓ ready" : "✗ " + d.status}`,
                d.message,
                ...(d.suggestions || []).map((s: string) => "• " + s),
              ];
              alert(lines.join("\n"));
            } catch { alert("Diagnostics failed"); }
          }}
          className="w-full px-2 py-1 rounded bg-dark-800 text-dark-300 hover:bg-dark-700 text-[10px]"
        >
          Diagnose LiteRT
        </button>
      </div>
    </div>
  );
}
