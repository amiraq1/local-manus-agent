"use client";

import { useEffect, useState, useCallback } from "react";
import { Container, Wifi, WifiOff, RefreshCw } from "lucide-react";
import { API } from "@/lib/config";

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
  const [visible, setVisible] = useState(true);

  const fetchStatus = useCallback(async () => {
    try {
      const res = await fetch(`${API}/sandbox/status`);
      if (res.ok) setInfo(await res.json());
      else setInfo(null);
    } catch {
      setInfo(null);
    }
  }, []);

  // Visibility-based polling — pauses when tab/panel not visible
  useEffect(() => {
    fetchStatus();
    let interval: ReturnType<typeof setInterval>;
    if (visible) {
      interval = setInterval(fetchStatus, 10000);
    }
    return () => clearInterval(interval);
  }, [fetchStatus, visible]);

  useEffect(() => {
    const handleVisibility = () => setVisible(!document.hidden);
    document.addEventListener("visibilitychange", handleVisibility);
    return () => document.removeEventListener("visibilitychange", handleVisibility);
  }, []);

  if (!info) return null;

  const statusBadge = !info.enabled
    ? "badge-neutral"
    : info.docker_available
    ? "badge-info"
    : "badge-warning";

  const statusText = !info.enabled ? "Disabled" : info.docker_available ? "Ready" : "No Docker";

  return (
    <div className="divider">
      <div className="panel-header flex items-center gap-2">
        <Container size={14} className={info.enabled ? "text-sky-400" : "text-dark-500"} />
        <span>Sandbox</span>
        <span className={`${statusBadge} ml-auto`}>{statusText}</span>
        <button onClick={fetchStatus} className="text-dark-400 hover:text-dark-200 transition-colors" aria-label="Refresh sandbox status">
          <RefreshCw size={12} />
        </button>
      </div>

      {info.enabled && (
        <div className="p-2.5 space-y-1.5 text-xs">
          <div className="flex items-center gap-2">
            {info.network_enabled ? (
              <Wifi size={11} className="text-emerald-400" />
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
        <p className="p-2.5 text-xs text-dark-500">
          Set SANDBOX_ENABLED=True in config.py to enable
        </p>
      )}
    </div>
  );
}
