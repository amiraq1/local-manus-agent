"use client";

import { useEffect, useState, useCallback } from "react";
import { Layout, Rocket, Code, FileText, Server, Terminal } from "lucide-react";
import { API } from "@/lib/config";

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
      if (r.ok) { const data = await r.json(); setTemplates(data.templates || []); }
    } catch { /* offline */ }
  }, []);

  useEffect(() => { load(); }, [load]);

  const selectTemplate = (t: Template) => {
    setSelected(t);
    const defaults: Record<string, string> = {};
    t.variables.forEach(v => {
      if (v === "primary_color") defaults[v] = "#00E5A0";
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
      if (!r.ok) throw new Error("Request failed");
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
      <h3 className="text-sm font-medium text-dark-200 flex items-center gap-2 font-display">
        <Rocket size={14} className="text-primary" /> Project Templates
      </h3>

      {!selected && (
        <div className="grid grid-cols-1 gap-2">
          {templates.map(t => {
            const Icon = CATEGORY_ICONS[t.category] || Code;
            return (
              <button key={t.id} onClick={() => selectTemplate(t)}
                className="text-left p-3 rounded-xl bg-dark-800/40 hover:bg-dark-800/60 border border-dark-700/40 hover:border-primary/25 transition-all glow-hover">
                <div className="flex items-center gap-2">
                  <Icon size={14} className="text-primary shrink-0" />
                  <span className="text-xs font-medium text-dark-200">{t.name}</span>
                  <span className="badge-neutral ml-auto">{t.file_count} files</span>
                </div>
                <p className="text-[10px] text-dark-400 mt-1">{t.description}</p>
              </button>
            );
          })}
        </div>
      )}

      {selected && (
        <div className="space-y-2.5 animate-fade-in">
          <div className="flex items-center justify-between">
            <span className="text-xs font-medium text-dark-200">{selected.name}</span>
            <button onClick={() => setSelected(null)} className="text-[10px] text-dark-400 hover:text-primary transition-colors">← Back</button>
          </div>

          {selected.variables.map(v => (
            <label key={v} className="block">
              <span className="text-[10px] text-dark-400 capitalize">{v.replace(/_/g, " ")}</span>
              <input type={v === "primary_color" ? "color" : "text"} value={vars[v] || ""}
                onChange={e => setVars({ ...vars, [v]: e.target.value })}
                className="w-full mt-0.5 bg-dark-800/60 border border-dark-700 rounded-lg px-2.5 py-1.5 text-xs text-dark-200 focus:outline-none focus:border-primary/40" />
            </label>
          ))}

          <button onClick={generate} disabled={generating || !taskId}
            className="w-full btn-primary text-xs">
            {generating ? "Generating..." : "Generate Project"}
          </button>

          {!taskId && <p className="text-[10px] text-amber-400">Send a message first to create a task</p>}
          {result && <p className={`text-[10px] ${result.startsWith("✓") ? "text-emerald-400" : "text-red-400"}`}>{result}</p>}
        </div>
      )}
    </div>
  );
}
