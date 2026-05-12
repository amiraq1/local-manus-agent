"use client";

import { ShieldAlert, Check, X } from "lucide-react";

interface ApprovalDialogProps {
  command: string;
  onApprove: () => void;
  onReject: () => void;
}

export default function ApprovalDialog({ command, onApprove, onReject }: ApprovalDialogProps) {
  return (
    <div className="fixed inset-0 bg-black/60 flex items-center justify-center z-50">
      <div className="bg-dark-900 border border-dark-600 rounded-xl p-6 max-w-lg w-full mx-4 shadow-2xl">
        {/* Header */}
        <div className="flex items-center gap-3 mb-4">
          <div className="w-10 h-10 bg-yellow-500/20 rounded-lg flex items-center justify-center">
            <ShieldAlert size={22} className="text-yellow-400" />
          </div>
          <div>
            <h3 className="text-lg font-semibold text-dark-100">Command Approval Required</h3>
            <p className="text-sm text-dark-400">The agent wants to execute a shell command</p>
          </div>
        </div>

        {/* Command */}
        <div className="bg-dark-950 border border-dark-700 rounded-lg p-4 mb-6">
          <p className="text-xs text-dark-500 mb-1">Command:</p>
          <code className="text-sm text-green-400 font-mono break-all">{command}</code>
        </div>

        {/* Warning */}
        <p className="text-xs text-dark-400 mb-4">
          Review this command carefully. In Safe Mode, all shell commands require your approval before execution.
        </p>

        {/* Actions */}
        <div className="flex gap-3">
          <button
            onClick={onReject}
            className="flex-1 flex items-center justify-center gap-2 px-4 py-2.5 rounded-lg
              border border-dark-600 text-dark-200 hover:bg-dark-800 transition-colors"
          >
            <X size={16} />
            Reject
          </button>
          <button
            onClick={onApprove}
            className="flex-1 flex items-center justify-center gap-2 px-4 py-2.5 rounded-lg
              bg-green-600 hover:bg-green-700 text-white font-medium transition-colors"
          >
            <Check size={16} />
            Approve
          </button>
        </div>
      </div>
    </div>
  );
}
