"use client";

import { CheckCircle, Circle, Loader } from "lucide-react";

export interface PlanStep {
  description: string;
  tool: string;
  status: "pending" | "running" | "done" | "error";
}

interface PlanPanelProps {
  plan: PlanStep[];
}

export default function PlanPanel({ plan }: PlanPanelProps) {
  if (plan.length === 0) return null;

  return (
    <div className="divider max-h-[250px] overflow-y-auto" role="list" aria-label="Execution plan">
      <div className="panel-header">Execution Plan</div>
      <div className="p-3 space-y-2">
        {plan.map((step, i) => (
          <div key={i} className="flex items-start gap-2.5 text-sm animate-fade-in" role="listitem">
            <div className="mt-0.5">
              {step.status === "done" && <CheckCircle size={14} className="text-emerald-400" />}
              {step.status === "running" && <Loader size={14} className="text-primary animate-spin" />}
              {step.status === "error" && <Circle size={14} className="text-red-400" />}
              {step.status === "pending" && <Circle size={14} className="text-dark-600" />}
            </div>
            <div className="flex-1">
              <p className="text-dark-200 text-xs leading-relaxed">{step.description}</p>
              <p className="text-[10px] text-dark-500 mt-0.5 font-mono">{step.tool}</p>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
