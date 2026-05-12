"use client";

import { useEffect, useState, useCallback } from "react";
import { Layout, Rocket, Code, FileText, Server, Terminal } from "lucide-react";

interface Template {
  id: string;
  name: string;
  description: string;
  category: string;
  variables: string[];
  file_count: number;
}

interface TemplatesPanelProps {
  taskId: string | null;
  onGenerated?: () => void;
}

const API = "http://localhost:8000/api";

const CATEGORY_ICONS: Record<string, typeof Layout> = {
  web: Layout, backend: Server, tool: Terminal, docs: FileText,
};

export default function TemplatesPanel({ taskId, onGenerated }: TemplatesPanelProps) {
  const [templates, setTemplates] = useState<Template[]>([]);
  const [selected, setSelected] = useState<Template | null>(null);
  const [vars, setVars] = useState<Record<string, string>>({});
  const [generating, setGenerating] = useState(false);
  const [result, setResult] = useState<string | null>(null);

  const load = useCallback(async () => {
    try {
      const r = await fetch(`${API}/templates`);
      const data = await r.json();
      setTemplates(data.templates || []);
    } catch { /* ignore */ }
  }, []);

  useEffect(() => { load(); }, [load]);

  const selectTemplate = (t: Template) => {
    setSelected(t);
    const defaults: Record<string, string> = {};
    t.variables.forEach(v => {
      if (v === "primary_color") defaults[v] = "#6366f1";
      else if (v === "project_name") defaults[v] = "My Project";
      else if (v === "description") defaults[v] = "";
      else defaults[v] = "";
    });
    setVars(defaults);
    setResult(null);
  };

  const generate = async () => {
    if (!selected || !taskId) return;
    setGenerating(true);
    setResult(null);
    try {
      const r = await fetch(`${API}/tasks/${taskId}/templates/${selected.id}/generate`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ variables: vars }),
      });
      const data = await r.json();
      if (data.success) {
        setResult(`✓ Generated ${data.total_files} files`);
        onGenerated?.();
      } else {
        setResult(`✗ ${data.error || data.errors?.join(", ") || "Failed"}`);
      }
    } catch { setResult("✗ Connection failed"); }
    setGenerating(false);
  };

  return (
    <div className="p-3 space-y-3">
      <h3 className="text-sm font-medium text-dark-200 flex items-center gap-2">
        <Rocket size={14} /> Project Templates
      </h3>

      {/* Template list */}
      {!selected && (
        <div className="grid grid-cols-1 gap-2">
          {templates.map(t => {
            const Icon = CATEGORY_ICONS[t.category] || Code;
            return (
              <button key={t.id} onClick={() => selectTemplate(t)}
                className="text-left p-3 rounded-lg bg-dark-800/50 hover:bg-dark-800 border border-dark-700 hover:border-primary/30 transition-colors">
                <div className="flex items-center gap-2">
                  <Icon size={14} className="text-primary shrink-0" />
                  <span className="text-xs font-medium text-dark-200">{t.name}</span>
                  <span className="text-[9px] text-dark-500 ml-auto">{t.file_count} files</span>
                </div>
                <p className="text-[10px] text-dark-400 mt-1">{t.description}</p>
              </button>
            );
          })}
        </div>
      )}

      {/* Selected template form */}
      {selected && (
        <div className="space-y-2">
          <div className="flex items-center justify-between">
            <span className="text-xs font-medium text-dark-200">{selected.name}</span>
            <button onClick={() => setSelected(null)} className="text-[10px] text-dark-400 hover:text-dark-200">← Back</button>
          </div>

          {selected.variables.map(v => (
            <label key={v} className="block">
              <span className="text-[10px] text-dark-400 capitalize">{v.replace("_", " ")}</span>
              <input type={v === "primary_color" ? "color" : "text"} value={vars[v] || ""}
                onChange={e => setVars({ ...vars, [v]: e.target.value })}
                className="w-full mt-0.5 bg-dark-800 border border-dark-600 rounded px-2 py-1 text-xs text-dark-200" />
            </label>
          ))}

          <button onClick={generate} disabled={generating || !taskId}
            className="w-full px-3 py-1.5 rounded bg-primary text-white text-xs font-medium disabled:opacity-50">
            {generating ? "Generating..." : "Generate Project"}
          </button>

          {!taskId && <p className="text-[10px] text-yellow-400">Send a message first to create a task</p>}
          {result && <p className={`text-[10px] ${result.startsWith("✓") ? "text-green-400" : "text-red-400"}`}>{result}</p>}
        </div>
      )}
    </div>
  );
}
