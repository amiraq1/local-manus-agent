"use client";

import { useState, useRef, useEffect } from "react";
import { Send } from "lucide-react";

export interface Message {
  id: string;
  role: "user" | "agent";
  content: string;
  phase?: string;
  timestamp: number;
}

interface ChatPanelProps {
  messages: Message[];
  isRunning: boolean;
  onSend: (message: string) => void;
}

const PHASE_COLORS: Record<string, string> = {
  thinking: "text-amber-400",
  planning: "text-sky-400",
  executing: "text-violet-400",
  observation: "text-cyan-400",
  reviewing: "text-orange-400",
  fixing: "text-red-400",
  completed: "text-emerald-400",
  error: "text-red-500",
};

const PHASE_LABELS: Record<string, string> = {
  thinking: "🧠 Thinking",
  planning: "📋 Planning",
  plan_ready: "✅ Plan Ready",
  executing: "⚡ Executing",
  observation: "👁 Observing",
  reviewing: "🔍 Reviewing",
  fixing: "🔧 Fixing",
  completed: "✅ Done",
  error: "❌ Error",
};

export default function ChatPanel({ messages, isRunning, onSend }: ChatPanelProps) {
  const [input, setInput] = useState("");
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || isRunning) return;
    onSend(input.trim());
    setInput("");
  };

  return (
    <div className="flex-1 flex flex-col min-h-0">
      <div className="panel-header">Chat</div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-4 space-y-3" role="log" aria-live="polite" aria-label="Chat messages">
        {messages.length === 0 && (
          <div className="text-center mt-12 animate-fade-in">
            <div className="w-16 h-16 mx-auto mb-4 rounded-2xl bg-gradient-to-br from-primary/20 to-emerald-400/10 flex items-center justify-center">
              <span className="text-2xl">🤖</span>
            </div>
            <p className="text-base font-display font-semibold text-dark-200 mb-1">Welcome to Manus Agent</p>
            <p className="text-sm text-dark-500">Describe a task and the agent will execute it locally.</p>
          </div>
        )}

        {messages.map((msg) => (
          <div
            key={msg.id}
            className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"} animate-fade-in`}
          >
            <div
              className={`max-w-[85%] rounded-xl px-3.5 py-2.5 text-sm ${
                msg.role === "user"
                  ? "bg-primary/10 border border-primary/20 text-dark-100"
                  : "bg-dark-800/60 border border-dark-700/40 text-dark-200"
              }`}
            >
              {msg.phase && (
                <span className={`text-xs font-medium ${PHASE_COLORS[msg.phase] || "text-dark-300"} block mb-1`}>
                  {PHASE_LABELS[msg.phase] || ""}
                </span>
              )}
              <p className="whitespace-pre-wrap leading-relaxed">{msg.content}</p>
            </div>
          </div>
        ))}
        <div ref={messagesEndRef} />
      </div>

      {/* Input */}
      <form onSubmit={handleSubmit} className="p-3 border-t border-dark-700/60">
        <div className="flex gap-2">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Describe your task..."
            className="input-field text-sm"
            disabled={isRunning}
            aria-label="Task description"
          />
          <button
            type="submit"
            disabled={isRunning || !input.trim()}
            className="btn-primary px-3.5"
            aria-label="Send message"
          >
            <Send size={18} />
          </button>
        </div>
      </form>
    </div>
  );
}
