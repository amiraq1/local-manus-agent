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
    <div className="border-t border-dark-700 max-h-[250px] flex flex-col">
      <div className="panel-header flex items-center gap-2">
        <Terminal size={14} />
        <span>Tool Log</span>
        {logs.length > 0 && (
          <span className="text-xs text-dark-500 ml-auto">{logs.length} calls</span>
        )}
      </div>
      <div className="flex-1 overflow-y-auto p-2">
        {logs.length === 0 ? (
          <p className="text-dark-500 text-sm text-center mt-2">No tool calls yet</p>
        ) : (
          <div className="space-y-1">
            {logs.map((log, i) => (
              <div
                key={i}
                className="flex items-start gap-2 px-2 py-1 rounded bg-dark-800/50 text-xs"
              >
                {log.success ? (
                  <CheckCircle size={12} className="text-green-400 mt-0.5 shrink-0" />
                ) : (
                  <XCircle size={12} className="text-red-400 mt-0.5 shrink-0" />
                )}
                <div className="flex-1 min-w-0">
                  <span className="text-primary font-mono">{log.tool}</span>
                  {log.params && Object.keys(log.params).length > 0 && (
                    <p className="text-dark-500 truncate mt-0.5">
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
