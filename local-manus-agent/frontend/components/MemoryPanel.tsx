"use client";

import { useEffect, useState, useCallback } from "react";
import { Brain, Search, RefreshCw, FileText } from "lucide-react";

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

const API = "http://localhost:8000/api";

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
      const memData = await memRes.json();
      const idxData = await idxRes.json();
      setMemories(memData.memories || []);
      setIndexEntries(idxData.index || []);
    } catch { /* ignore */ }
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
      const data = await res.json();
      setSearchResults(data.results || []);
      setTab("search");
    } catch { /* ignore */ }
  };

  if (!taskId) return null;

  return (
    <div className="border-t border-dark-700 max-h-[250px] flex flex-col">
      <div className="panel-header flex items-center gap-2">
        <Brain size={14} className="text-purple-400" />
        <span>Memory & RAG</span>
        <div className="ml-auto flex items-center gap-1">
          <button
            onClick={() => setTab("index")}
            className={`text-[10px] px-1.5 py-0.5 rounded ${tab === "index" ? "bg-primary/20 text-primary" : "text-dark-500"}`}
          >Index</button>
          <button
            onClick={() => setTab("memory")}
            className={`text-[10px] px-1.5 py-0.5 rounded ${tab === "memory" ? "bg-primary/20 text-primary" : "text-dark-500"}`}
          >Memory</button>
          <button
            onClick={() => setTab("search")}
            className={`text-[10px] px-1.5 py-0.5 rounded ${tab === "search" ? "bg-primary/20 text-primary" : "text-dark-500"}`}
          >Search</button>
          <button onClick={handleReindex} className="text-dark-400 hover:text-dark-200 ml-1" title="Re-index" aria-label="Re-index">
            <RefreshCw size={11} />
          </button>
        </div>
      </div>

      <div className="flex-1 overflow-y-auto p-2">
        {tab === "index" && (
          <div className="space-y-1">
            {indexEntries.length === 0 && <p className="text-xs text-dark-500 text-center">No files indexed</p>}
            {indexEntries.map((e, i) => (
              <div key={i} className="text-xs px-2 py-1 rounded bg-dark-800/50">
                <div className="flex items-center gap-1">
                  <FileText size={10} className="text-dark-400" />
                  <span className="text-dark-200 truncate">{e.path}</span>
                  <span className="text-[9px] text-dark-500 ml-auto">{e.language}</span>
                </div>
                {e.summary && <p className="text-[10px] text-dark-500 mt-0.5 truncate">{e.summary}</p>}
              </div>
            ))}
          </div>
        )}

        {tab === "memory" && (
          <div className="space-y-1">
            {memories.length === 0 && <p className="text-xs text-dark-500 text-center">No memories stored</p>}
            {memories.map((m) => (
              <div key={m.id} className="text-xs px-2 py-1 rounded bg-dark-800/50">
                <span className="text-[9px] text-purple-400">{m.type}</span>
                <p className="text-dark-300 mt-0.5 line-clamp-2">{m.content}</p>
              </div>
            ))}
          </div>
        )}

        {tab === "search" && (
          <div className="space-y-2">
            <div className="flex gap-1">
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                onKeyDown={(e) => e.key === "Enter" && handleSearch()}
                placeholder="Search files..."
                className="flex-1 bg-dark-800 border border-dark-600 rounded px-2 py-1 text-xs text-dark-200 placeholder-dark-500"
              />
              <button onClick={handleSearch} className="px-2 py-1 bg-primary/20 text-primary rounded text-xs" aria-label="Search">
                <Search size={11} />
              </button>
            </div>
            {searchResults.map((r, i) => (
              <div key={i} className="text-xs px-2 py-1 rounded bg-dark-800/50">
                <div className="flex items-center gap-1">
                  <span className="text-dark-200">{r.path}</span>
                  <span className="text-[9px] text-dark-500 ml-auto">score: {r.score.toFixed(1)}</span>
                </div>
                {r.snippet && <pre className="text-[10px] text-dark-400 mt-0.5 overflow-hidden max-h-[40px]">{r.snippet}</pre>}
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
