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

  const getPhaseColor = (phase?: string) => {
    switch (phase) {
      case "thinking":
        return "text-yellow-400";
      case "planning":
        return "text-blue-400";
      case "executing":
        return "text-purple-400";
      case "observation":
        return "text-cyan-400";
      case "reviewing":
        return "text-orange-400";
      case "fixing":
        return "text-red-400";
      case "completed":
        return "text-green-400";
      case "error":
        return "text-red-500";
      default:
        return "text-dark-300";
    }
  };

  const getPhaseLabel = (phase?: string) => {
    switch (phase) {
      case "thinking":
        return "🧠 Thinking";
      case "planning":
        return "📋 Planning";
      case "plan_ready":
        return "✅ Plan Ready";
      case "executing":
        return "⚡ Executing";
      case "observation":
        return "👁 Observing";
      case "reviewing":
        return "🔍 Reviewing";
      case "fixing":
        return "🔧 Fixing";
      case "completed":
        return "✅ Done";
      case "error":
        return "❌ Error";
      default:
        return "";
    }
  };

  return (
    <div className="flex-1 flex flex-col min-h-0">
      <div className="panel-header">Chat</div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-4 space-y-3">
        {messages.length === 0 && (
          <div className="text-center text-dark-500 mt-8">
            <p className="text-lg mb-2">👋 Welcome to Local Manus Agent</p>
            <p className="text-sm">Describe a task and the agent will execute it locally.</p>
          </div>
        )}

        {messages.map((msg) => (
          <div
            key={msg.id}
            className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"}`}
          >
            <div
              className={`max-w-[85%] rounded-lg px-3 py-2 text-sm ${
                msg.role === "user"
                  ? "bg-primary/20 text-dark-100"
                  : "bg-dark-800 text-dark-200"
              }`}
            >
              {msg.phase && (
                <span className={`text-xs font-medium ${getPhaseColor(msg.phase)} block mb-1`}>
                  {getPhaseLabel(msg.phase)}
                </span>
              )}
              <p className="whitespace-pre-wrap">{msg.content}</p>
            </div>
          </div>
        ))}
        <div ref={messagesEndRef} />
      </div>

      {/* Input */}
      <form onSubmit={handleSubmit} className="p-3 border-t border-dark-700">
        <div className="flex gap-2">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Describe your task..."
            className="input-field text-sm"
            disabled={isRunning}
          />
          <button
            type="submit"
            disabled={isRunning || !input.trim()}
            className="btn-primary px-3"
            aria-label="Send message"
          >
            <Send size={18} />
          </button>
        </div>
      </form>
    </div>
  );
}
