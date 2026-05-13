"use client";

import { useEffect, useState, useCallback } from "react";
import { Brain, Search, RefreshCw, FileText } from "lucide-react";
import { API } from "@/lib/config";

interface MemoryEntry {
  id: string;
  type: string;
  content: string;
  created_at: number;
}

interface IndexEntry {
  path: string;
  language: string;
  summary: string;
  symbols: string[];
}

interface MemoryPanelProps {
  taskId: string | null;
}

export default function MemoryPanel({ taskId }: MemoryPanelProps) {
  const [memories, setMemories] = useState<MemoryEntry[]>([]);
  const [indexEntries, setIndexEntries] = useState<IndexEntry[]>([]);
  const [searchQuery, setSearchQuery] = useState("");
  const [searchResults, setSearchResults] = useState<Array<{ path: string; score: number; snippet: string }>>([]);
  const [tab, setTab] = useState<"memory" | "index" | "search">("index");

  const loadData = useCallback(async () => {
    if (!taskId) return;
    try {
      const [memRes, idxRes] = await Promise.all([
        fetch(`${API}/tasks/${taskId}/memory`),
        fetch(`${API}/tasks/${taskId}/index`),
      ]);
      if (memRes.ok) { const d = await memRes.json(); setMemories(d.memories || []); }
      if (idxRes.ok) { const d = await idxRes.json(); setIndexEntries(d.index || []); }
    } catch { /* offline */ }
  }, [taskId]);

  useEffect(() => { loadData(); }, [loadData]);

  const handleReindex = async () => {
    if (!taskId) return;
    await fetch(`${API}/tasks/${taskId}/index`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ force: true }),
    });
    loadData();
  };

  const handleSearch = async () => {
    if (!taskId || !searchQuery.trim()) return;
    try {
      const res = await fetch(`${API}/tasks/${taskId}/search`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ query: searchQuery }),
      });
      if (res.ok) {
        const data = await res.json();
        setSearchResults(data.results || []);
        setTab("search");
      }
    } catch { /* offline */ }
  };

  if (!taskId) return null;

  const tabs: { id: typeof tab; label: string }[] = [
    { id: "index", label: "Index" },
    { id: "memory", label: "Memory" },
    { id: "search", label: "Search" },
  ];

  return (
    <div className="divider max-h-[250px] flex flex-col">
      <div className="panel-header flex items-center gap-2">
        <Brain size={14} className="text-violet-400" />
        <span>Memory & RAG</span>
        <div className="ml-auto flex items-center gap-1" role="tablist" aria-label="Memory tabs">
          {tabs.map((t) => (
            <button
              key={t.id}
              role="tab"
              aria-selected={tab === t.id}
              onClick={() => setTab(t.id)}
              className={`text-[10px] px-2 py-0.5 rounded-md transition-colors normal-case ${
                tab === t.id ? "bg-primary/15 text-primary" : "text-dark-500 hover:text-dark-300"
              }`}
            >
              {t.label}
            </button>
          ))}
          <button onClick={handleReindex} className="text-dark-400 hover:text-dark-200 ml-1 transition-colors" title="Re-index" aria-label="Re-index files">
            <RefreshCw size={11} />
          </button>
        </div>
      </div>

      <div className="flex-1 overflow-y-auto p-2" role="tabpanel">
        {tab === "index" && (
          <div className="space-y-1">
            {indexEntries.length === 0 && <p className="text-xs text-dark-500 text-center py-4">No files indexed</p>}
            {indexEntries.map((e, i) => (
              <div key={i} className="text-xs px-2.5 py-1.5 rounded-lg bg-dark-800/40 hover:bg-dark-800/60 transition-colors">
                <div className="flex items-center gap-1.5">
                  <FileText size={10} className="text-dark-400" />
                  <span className="text-dark-200 truncate">{e.path}</span>
                  <span className="badge-neutral ml-auto">{e.language}</span>
                </div>
                {e.summary && <p className="text-[10px] text-dark-500 mt-0.5 truncate">{e.summary}</p>}
              </div>
            ))}
          </div>
        )}

        {tab === "memory" && (
          <div className="space-y-1">
            {memories.length === 0 && <p className="text-xs text-dark-500 text-center py-4">No memories stored</p>}
            {memories.map((m) => (
              <div key={m.id} className="text-xs px-2.5 py-1.5 rounded-lg bg-dark-800/40">
                <span className="badge-info">{m.type}</span>
                <p className="text-dark-300 mt-1 line-clamp-2">{m.content}</p>
              </div>
            ))}
          </div>
        )}

        {tab === "search" && (
          <div className="space-y-2">
            <div className="flex gap-1.5">
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                onKeyDown={(e) => e.key === "Enter" && handleSearch()}
                placeholder="Search files..."
                className="flex-1 bg-dark-800/60 border border-dark-700 rounded-lg px-2.5 py-1.5 text-xs text-dark-200 placeholder-dark-500 focus:outline-none focus:border-primary/40"
                aria-label="Search query"
              />
              <button onClick={handleSearch} className="px-2.5 py-1.5 bg-primary/15 text-primary rounded-lg text-xs hover:bg-primary/20 transition-colors" aria-label="Search">
                <Search size={11} />
              </button>
            </div>
            {searchResults.map((r, i) => (
              <div key={i} className="text-xs px-2.5 py-1.5 rounded-lg bg-dark-800/40">
                <div className="flex items-center gap-1.5">
                  <span className="text-dark-200">{r.path}</span>
                  <span className="text-[9px] text-dark-500 ml-auto">score: {r.score.toFixed(1)}</span>
                </div>
                {r.snippet && <pre className="text-[10px] text-dark-400 mt-1 overflow-hidden max-h-[40px] font-mono">{r.snippet}</pre>}
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
