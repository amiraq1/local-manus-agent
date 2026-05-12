"use client";

import { useEffect, useState, useCallback } from "react";
import { Shield, AlertTriangle } from "lucide-react";

interface SecurityEvent {
  id: string;
  task_id: string | null;
  event_type: string;
  severity: string;
  action: string;
  target: string | null;
  decision: string;
  reason: string;
  created_at: number;
}

const API = "http://localhost:8000/api";

export default function SecurityPanel() {
  const [events, setEvents] = useState<SecurityEvent[]>([]);

  const load = useCallback(async () => {
    try {
      const r = await fetch(`${API}/security/events?limit=20`);
      const data = await r.json();
      setEvents(data.events || []);
    } catch { /* ignore */ }
  }, []);

  useEffect(() => { load(); const i = setInterval(load, 15000); return () => clearInterval(i); }, [load]);

  const severityColor = (s: string) => {
    switch (s) {
      case "critical": return "text-red-500";
      case "high": return "text-orange-400";
      case "medium": return "text-yellow-400";
      default: return "text-dark-400";
    }
  };

  const decisionIcon = (d: string) => {
    if (d === "deny") return "🚫";
    if (d === "require_approval") return "⚠️";
    return "✓";
  };

  return (
    <div className="p-3 space-y-2">
      <div className="flex items-center gap-2 mb-2">
        <Shield size={14} className="text-red-400" />
        <span className="text-sm font-medium text-dark-200">Security Events</span>
        <span className="text-[10px] text-dark-500 ml-auto">{events.length}</span>
      </div>

      {events.length === 0 && (
        <p className="text-xs text-dark-500 text-center py-4">No security events recorded</p>
      )}

      <div className="space-y-1 max-h-[300px] overflow-y-auto">
        {events.map((e) => (
          <div key={e.id} className="text-xs px-2 py-1.5 rounded bg-dark-800/50 space-y-0.5">
            <div className="flex items-center gap-1.5">
              <span>{decisionIcon(e.decision)}</span>
              <span className={`font-medium ${severityColor(e.severity)}`}>{e.severity}</span>
              <span className="text-dark-400">·</span>
              <span className="text-dark-300">{e.event_type}</span>
              <span className="text-dark-500 ml-auto text-[9px]">{e.action}</span>
            </div>
            {e.target && <p className="text-dark-500 truncate font-mono text-[10px]">{e.target}</p>}
            {e.reason && <p className="text-dark-400 text-[10px]">{e.reason}</p>}
          </div>
        ))}
      </div>
    </div>
  );
}
