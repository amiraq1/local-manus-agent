"use client";

import { useState, useCallback, useRef, useEffect } from "react";

/**
 * ExecutivePanel — Direct interface to the Executive Agent.
 * 
 * Sends user input to /api/executive and renders structured JSON responses
 * in a Bento Box grid layout with dark/neon aesthetics.
 */

interface ExecutiveResponse {
  status: "success" | "error" | "clarification_needed";
  action_type: string;
  thought_process: string;
  payload: Record<string, unknown>;
}

interface HistoryEntry {
  id: string;
  input: string;
  response: ExecutiveResponse;
  ts: number;
}

export default function ExecutivePanel() {
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [history, setHistory] = useState<HistoryEntry[]>([]);
  const [expanded, setExpanded] = useState(true);
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [history]);

  const send = useCallback(async () => {
    if (!input.trim() || loading) return;

    setLoading(true);
    const userInput = input.trim();
    setInput("");

    try {
      const res = await fetch("/api/executive", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: userInput }),
      });
      const data: ExecutiveResponse = await res.json();

      setHistory((prev) => [
        ...prev,
        {
          id: crypto.randomUUID(),
          input: userInput,
          response: data,
          ts: Date.now(),
        },
      ]);
    } catch (err) {
      setHistory((prev) => [
        ...prev,
        {
          id: crypto.randomUUID(),
          input: userInput,
          response: {
            status: "error",
            action_type: "analyze_input",
            thought_process: "فشل الاتصال بالخادم",
            payload: { error: String(err) },
          },
          ts: Date.now(),
        },
      ]);
    } finally {
      setLoading(false);
    }
  }, [input, loading]);

  const statusColor = (s: string) => {
    if (s === "success") return "text-emerald-400";
    if (s === "error") return "text-rose-400";
    return "text-amber-400";
  };

  const statusIcon = (s: string) => {
    if (s === "success") return "✓";
    if (s === "error") return "✗";
    return "?";
  };

  return (
    <section className="border-b border-dark-700/60">
      <button
        onClick={() => setExpanded(!expanded)}
        className="w-full px-4 py-2.5 flex items-center gap-2 text-xs font-semibold text-dark-300 uppercase tracking-wider hover:bg-dark-800/50 transition-colors"
      >
        <span className="w-5 h-5 rounded bg-gradient-to-br from-violet-500 to-fuchsia-500 flex items-center justify-center text-[10px] text-white shadow-[0_0_8px_rgba(139,92,246,0.3)]">
          E
        </span>
        <span>Executive Agent</span>
        <span className="ml-auto text-dark-500 text-[10px]">
          {expanded ? "▾" : "▸"}
        </span>
      </button>

      {expanded && (
        <div className="px-4 pb-3 space-y-3">
          {/* Input */}
          <div className="flex gap-2">
            <input
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && send()}
              placeholder="أدخل أمرك للوكيل التنفيذي..."
              className="flex-1 bg-dark-800/80 border border-dark-700/60 rounded-lg px-3 py-2 text-sm text-dark-100 placeholder:text-dark-500 focus:outline-none focus:border-violet-500/50 focus:ring-1 focus:ring-violet-500/20 transition-all"
              dir="auto"
              disabled={loading}
            />
            <button
              onClick={send}
              disabled={loading || !input.trim()}
              className="px-4 py-2 rounded-lg text-xs font-semibold bg-gradient-to-r from-violet-600 to-fuchsia-600 text-white hover:from-violet-500 hover:to-fuchsia-500 disabled:opacity-40 disabled:cursor-not-allowed transition-all shadow-[0_0_12px_rgba(139,92,246,0.15)]"
            >
              {loading ? (
                <span className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin inline-block" />
              ) : (
                "⚡ تنفيذ"
              )}
            </button>
          </div>

          {/* Response History */}
          <div className="space-y-2 max-h-[360px] overflow-y-auto scrollbar-thin">
            {history.map((entry) => (
              <div
                key={entry.id}
                className="bg-dark-800/60 border border-dark-700/40 rounded-lg overflow-hidden"
              >
                {/* Header */}
                <div className="flex items-center gap-2 px-3 py-1.5 border-b border-dark-700/30">
                  <span
                    className={`text-sm font-bold ${statusColor(
                      entry.response.status
                    )}`}
                  >
                    {statusIcon(entry.response.status)}
                  </span>
                  <span className="text-[10px] text-dark-400 font-mono">
                    {entry.response.action_type}
                  </span>
                  <span className="ml-auto text-[9px] text-dark-500">
                    {new Date(entry.ts).toLocaleTimeString("ar-SA")}
                  </span>
                </div>

                {/* Thought */}
                {entry.response.thought_process && (
                  <div className="px-3 py-1.5 text-[11px] text-dark-400 italic border-b border-dark-700/20" dir="auto">
                    💭 {entry.response.thought_process}
                  </div>
                )}

                {/* Payload */}
                <pre className="px-3 py-2 text-[11px] text-dark-200 overflow-x-auto font-mono leading-relaxed" dir="ltr">
                  {JSON.stringify(entry.response.payload, null, 2)}
                </pre>
              </div>
            ))}
            <div ref={bottomRef} />
          </div>

          {history.length === 0 && (
            <div className="text-center py-6">
              <div className="w-10 h-10 mx-auto mb-2 rounded-xl bg-gradient-to-br from-violet-500/10 to-fuchsia-500/10 border border-violet-500/20 flex items-center justify-center">
                <span className="text-lg">⚡</span>
              </div>
              <p className="text-xs text-dark-500" dir="auto">
                الوكيل التنفيذي جاهز — أدخل أمرك
              </p>
            </div>
          )}
        </div>
      )}
    </section>
  );
}
