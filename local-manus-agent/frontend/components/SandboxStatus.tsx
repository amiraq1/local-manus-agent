"use client";

import { useEffect, useState, useCallback } from "react";
import { Container, Wifi, WifiOff, RefreshCw } from "lucide-react";

interface SandboxInfo {
  enabled: boolean;
  docker_available?: boolean;
  image_available?: boolean;
  image?: string;
  network_enabled?: boolean;
  memory_limit?: string;
  cpu_limit?: number;
  timeout?: number;
  active_containers?: number;
  last_command?: string | null;
  message?: string;
}

export default function SandboxStatus() {
  const [info, setInfo] = useState<SandboxInfo | null>(null);

  const fetchStatus = useCallback(async () => {
    try {
      const res = await fetch("http://localhost:8000/api/sandbox/status");
      const data = await res.json();
      setInfo(data);
    } catch {
      setInfo(null);
    }
  }, []);

  useEffect(() => {
    fetchStatus();
    const interval = setInterval(fetchStatus, 10000);
    return () => clearInterval(interval);
  }, [fetchStatus]);

  if (!info) return null;

  return (
    <div className="border-t border-dark-700">
      <div className="panel-header flex items-center gap-2">
        <Container size={14} className={info.enabled ? "text-blue-400" : "text-dark-500"} />
        <span>Sandbox</span>
        <span className={`text-[10px] px-1.5 py-0.5 rounded ml-auto ${
          info.enabled && info.docker_available
            ? "bg-blue-900/30 text-blue-400"
            : info.enabled
            ? "bg-yellow-900/30 text-yellow-400"
            : "bg-dark-800 text-dark-500"
        }`}>
          {!info.enabled ? "Disabled" : info.docker_available ? "Ready" : "No Docker"}
        </span>
        <button onClick={fetchStatus} className="text-dark-400 hover:text-dark-200" aria-label="Refresh">
          <RefreshCw size={12} />
        </button>
      </div>

      {info.enabled && (
        <div className="p-2 space-y-1 text-xs">
          <div className="flex items-center gap-2">
            {info.network_enabled ? (
              <Wifi size={11} className="text-green-400" />
            ) : (
              <WifiOff size={11} className="text-red-400" />
            )}
            <span className="text-dark-400">
              Network: {info.network_enabled ? "Enabled" : "Disabled"}
            </span>
          </div>

          <div className="flex justify-between text-dark-500">
            <span>Image: {info.image_available ? "✓" : "✗"} {info.image?.split(":")[0]}</span>
          </div>

          <div className="flex justify-between text-dark-500">
            <span>Mem: {info.memory_limit}</span>
            <span>CPU: {info.cpu_limit}</span>
            <span>Timeout: {info.timeout}s</span>
          </div>

          {(info.active_containers ?? 0) > 0 && (
            <div className="text-dark-400">
              Active: {info.active_containers} container(s)
            </div>
          )}

          {info.last_command && (
            <div className="text-dark-500 truncate font-mono">
              Last: {info.last_command}
            </div>
          )}
        </div>
      )}

      {!info.enabled && (
        <p className="p-2 text-xs text-dark-500">
          Set SANDBOX_ENABLED=True in config.py to enable
        </p>
      )}
    </div>
  );
}
