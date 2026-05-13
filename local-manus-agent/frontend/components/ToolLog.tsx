"use client";

import { Terminal, CheckCircle, XCircle } from "lucide-react";

export interface ToolLogEntry {
  step: number | string;
  tool: string;
  params: Record<string, unknown>;
  success: boolean;
  timestamp?: number;
}

interface ToolLogProps {
  logs: ToolLogEntry[];
}

export default function ToolLog({ logs }: ToolLogProps) {
  return (
    <div className="divider max-h-[250px] flex flex-col">
      <div className="panel-header flex items-center gap-2">
        <Terminal size={14} className="text-primary" />
        <span>Tool Log</span>
        {logs.length > 0 && (
          <span className="badge-neutral ml-auto">{logs.length} calls</span>
        )}
      </div>
      <div className="flex-1 overflow-y-auto p-2" role="log" aria-label="Tool execution log">
        {logs.length === 0 ? (
          <div className="text-center mt-4 animate-fade-in">
            <Terminal size={24} className="mx-auto mb-2 text-dark-600" />
            <p className="text-dark-500 text-sm">No tool calls yet</p>
          </div>
        ) : (
          <div className="space-y-1">
            {logs.map((log, i) => (
              <div
                key={i}
                className="flex items-start gap-2 px-2.5 py-1.5 rounded-lg bg-dark-800/30 text-xs animate-fade-in hover:bg-dark-800/50 transition-colors"
              >
                {log.success ? (
                  <CheckCircle size={12} className="text-emerald-400 mt-0.5 shrink-0" />
                ) : (
                  <XCircle size={12} className="text-red-400 mt-0.5 shrink-0" />
                )}
                <div className="flex-1 min-w-0">
                  <span className="text-primary font-mono">{log.tool}</span>
                  {log.params && Object.keys(log.params).length > 0 && (
                    <p className="text-dark-500 truncate mt-0.5 font-mono">
                      {JSON.stringify(log.params).slice(0, 80)}
                    </p>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
