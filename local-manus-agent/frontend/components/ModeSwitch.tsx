"use client";

import { Shield, Zap } from "lucide-react";

interface ModeSwitchProps {
  mode: "safe" | "autonomous";
  onSwitch: (mode: "safe" | "autonomous") => void;
}

export default function ModeSwitch({ mode, onSwitch }: ModeSwitchProps) {
  return (
    <div className="flex items-center gap-1 bg-dark-800 rounded-lg p-1">
      <button
        onClick={() => onSwitch("safe")}
        className={`flex items-center gap-1.5 px-3 py-1.5 rounded-md text-xs font-medium transition-colors ${
          mode === "safe"
            ? "bg-green-600/20 text-green-400 border border-green-600/30"
            : "text-dark-400 hover:text-dark-200"
        }`}
        title="Safe Mode: Commands require approval"
      >
        <Shield size={13} />
        Safe
      </button>
      <button
        onClick={() => onSwitch("autonomous")}
        className={`flex items-center gap-1.5 px-3 py-1.5 rounded-md text-xs font-medium transition-colors ${
          mode === "autonomous"
            ? "bg-orange-600/20 text-orange-400 border border-orange-600/30"
            : "text-dark-400 hover:text-dark-200"
        }`}
        title="Autonomous Mode: Commands execute without approval"
      >
        <Zap size={13} />
        Auto
      </button>
    </div>
  );
}
