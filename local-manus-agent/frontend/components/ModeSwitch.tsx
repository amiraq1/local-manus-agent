"use client";

import { Shield, Zap } from "lucide-react";

interface ModeSwitchProps {
  mode: "safe" | "autonomous";
  onSwitch: (mode: "safe" | "autonomous") => void;
}

export default function ModeSwitch({ mode, onSwitch }: ModeSwitchProps) {
  return (
    <div className="flex items-center gap-0.5 bg-dark-800/60 rounded-lg p-0.5 border border-dark-700/40" role="radiogroup" aria-label="Execution mode">
      <button
        role="radio"
        aria-checked={mode === "safe"}
        onClick={() => onSwitch("safe")}
        className={`flex items-center gap-1.5 px-3 py-1.5 rounded-md text-xs font-medium transition-all duration-200 ${
          mode === "safe"
            ? "bg-emerald-500/15 text-emerald-400 border border-emerald-500/25 shadow-[0_0_8px_rgba(16,185,129,0.1)]"
            : "text-dark-400 hover:text-dark-200 border border-transparent"
        }`}
        title="Safe Mode: Commands require approval"
      >
        <Shield size={13} />
        Safe
      </button>
      <button
        role="radio"
        aria-checked={mode === "autonomous"}
        onClick={() => onSwitch("autonomous")}
        className={`flex items-center gap-1.5 px-3 py-1.5 rounded-md text-xs font-medium transition-all duration-200 ${
          mode === "autonomous"
            ? "bg-amber-500/15 text-amber-400 border border-amber-500/25 shadow-[0_0_8px_rgba(245,158,11,0.1)]"
            : "text-dark-400 hover:text-dark-200 border border-transparent"
        }`}
        title="Autonomous Mode: Commands execute without approval"
      >
        <Zap size={13} />
        Auto
      </button>
    </div>
  );
}
