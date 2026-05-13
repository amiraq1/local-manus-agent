"use client";

import { Users, CheckCircle, Loader, XCircle, MinusCircle } from "lucide-react";

export interface AgentStep {
  agent: string;
  phase: string;
  status: "running" | "completed" | "error" | "skipped";
  summary: string;
}

interface AgentsPanelProps {
  steps: AgentStep[];
}

const AGENT_COLORS: Record<string, string> = {
  MemoryAgent: "text-violet-400",
  PlannerAgent: "text-sky-400",
  SecurityAgent: "text-red-400",
  CoderAgent: "text-emerald-400",
  ReviewerAgent: "text-amber-400",
  BrowserAgent: "text-cyan-400",
  Orchestrator: "text-primary",
};

export default function AgentsPanel({ steps }: AgentsPanelProps) {
  if (steps.length === 0) return null;

  const statusIcon = (status: string) => {
    switch (status) {
      case "completed": return <CheckCircle size={12} className="text-emerald-400" />;
      case "running": return <Loader size={12} className="text-primary animate-spin" />;
      case "error": return <XCircle size={12} className="text-red-400" />;
      case "skipped": return <MinusCircle size={12} className="text-dark-500" />;
      default: return <MinusCircle size={12} className="text-dark-500" />;
    }
  };

  return (
    <div className="divider max-h-[200px] flex flex-col" role="log" aria-label="Agent activity">
      <div className="panel-header flex items-center gap-2">
        <Users size={14} className="text-primary" />
        <span>Agents</span>
        <span className="badge-neutral ml-auto">{steps.length} steps</span>
      </div>
      <div className="flex-1 overflow-y-auto p-2 space-y-0.5">
        {steps.map((step, i) => (
          <div key={i} className="flex items-center gap-2 px-2.5 py-1.5 rounded-lg bg-dark-800/30 text-xs animate-fade-in hover:bg-dark-800/50 transition-colors">
            {statusIcon(step.status)}
            <span className={`font-medium ${AGENT_COLORS[step.agent] || "text-dark-300"}`}>
              {step.agent}
            </span>
            <span className="text-dark-600">·</span>
            <span className="text-dark-400 truncate flex-1">{step.summary || step.phase}</span>
          </div>
        ))}
      </div>
    </div>
  );
}
