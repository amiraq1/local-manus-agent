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
    <div className="border-t border-dark-700 max-h-[250px] overflow-y-auto">
      <div className="panel-header">Execution Plan</div>
      <div className="p-3 space-y-2">
        {plan.map((step, i) => (
          <div key={i} className="flex items-start gap-2 text-sm">
            <div className="mt-0.5">
              {step.status === "done" && (
                <CheckCircle size={14} className="text-green-400" />
              )}
              {step.status === "running" && (
                <Loader size={14} className="text-primary animate-spin" />
              )}
              {step.status === "error" && (
                <Circle size={14} className="text-red-400" />
              )}
              {step.status === "pending" && (
                <Circle size={14} className="text-dark-500" />
              )}
            </div>
            <div className="flex-1">
              <p className="text-dark-200">{step.description}</p>
              <p className="text-xs text-dark-500 mt-0.5">{step.tool}</p>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
