"use client";

import { useEffect, useRef } from "react";
import { ShieldAlert, Check, X } from "lucide-react";

interface ApprovalDialogProps {
  command: string;
  onApprove: () => void;
  onReject: () => void;
}

export default function ApprovalDialog({ command, onApprove, onReject }: ApprovalDialogProps) {
  const dialogRef = useRef<HTMLDivElement>(null);

  // Focus trap + Escape key
  useEffect(() => {
    const handleKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") onReject();
      if (e.key === "Tab" && dialogRef.current) {
        const focusable = dialogRef.current.querySelectorAll<HTMLElement>(
          'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
        );
        const first = focusable[0];
        const last = focusable[focusable.length - 1];
        if (e.shiftKey && document.activeElement === first) {
          e.preventDefault();
          last?.focus();
        } else if (!e.shiftKey && document.activeElement === last) {
          e.preventDefault();
          first?.focus();
        }
      }
    };
    document.addEventListener("keydown", handleKey);
    // Focus first button
    const timer = setTimeout(() => {
      dialogRef.current?.querySelector<HTMLElement>("button")?.focus();
    }, 50);
    return () => {
      document.removeEventListener("keydown", handleKey);
      clearTimeout(timer);
    };
  }, [onReject]);

  return (
    <div
      className="fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center z-50"
      role="dialog"
      aria-modal="true"
      aria-labelledby="approval-title"
      aria-describedby="approval-desc"
    >
      <div
        ref={dialogRef}
        className="bg-dark-900 border border-dark-600 rounded-xl p-6 max-w-lg w-full mx-4 shadow-2xl animate-scale-in"
      >
        {/* Header */}
        <div className="flex items-center gap-3 mb-4">
          <div className="w-10 h-10 bg-amber-500/15 rounded-lg flex items-center justify-center">
            <ShieldAlert size={22} className="text-amber-400" />
          </div>
          <div>
            <h3 id="approval-title" className="text-lg font-semibold text-dark-50 font-display">
              Command Approval Required
            </h3>
            <p id="approval-desc" className="text-sm text-dark-400">
              The agent wants to execute a shell command
            </p>
          </div>
        </div>

        {/* Command */}
        <div className="bg-dark-950 border border-dark-700 rounded-lg p-4 mb-6">
          <p className="text-xs text-dark-500 mb-1.5 font-display uppercase tracking-wider">Command:</p>
          <code className="text-sm text-primary font-mono break-all leading-relaxed">{command}</code>
        </div>

        {/* Warning */}
        <p className="text-xs text-dark-400 mb-5 leading-relaxed">
          Review this command carefully. In Safe Mode, all shell commands require your approval before execution.
        </p>

        {/* Actions */}
        <div className="flex gap-3">
          <button
            onClick={onReject}
            className="flex-1 flex items-center justify-center gap-2 px-4 py-2.5 rounded-lg
              border border-dark-600 text-dark-200 hover:bg-dark-800 transition-all duration-200"
          >
            <X size={16} />
            Reject
          </button>
          <button
            onClick={onApprove}
            className="flex-1 flex items-center justify-center gap-2 px-4 py-2.5 rounded-lg
              bg-emerald-600 hover:bg-emerald-700 text-white font-medium transition-all duration-200
              shadow-[0_0_12px_rgba(16,185,129,0.2)]"
          >
            <Check size={16} />
            Approve
          </button>
        </div>
      </div>
    </div>
  );
}
