"use client";

import { useEffect, useState, useCallback } from "react";
import { ExternalLink } from "lucide-react";
import { API } from "@/lib/config";

interface PlatformStatus {
  platform_mode: string;
  is_termux: boolean;
  docker_available: boolean;
  ollama_available: boolean;
  browser_mode: string;
  limitations: string[];
}

export default function SettingsPanel() {
  const [platform, setPlatform] = useState<PlatformStatus | null>(null);

  const load = useCallback(async () => {
    try {
      const r = await fetch(`${API}/platform/status`);
      if (r.ok) setPlatform(await r.json());
    } catch { /* offline */ }
  }, []);

  useEffect(() => { load(); }, [load]);

  return (
    <div className="p-4 space-y-4 overflow-y-auto">
      {/* Termux Banner */}
      {platform?.is_termux && (
        <div className="bg-amber-900/15 border border-amber-700/25 rounded-xl p-3">
          <p className="text-amber-400 text-sm font-semibold font-display">📱 Running in Termux Lite Mode</p>
          <ul className="mt-2 text-xs text-amber-300/80 space-y-1">
            {platform.limitations.map((l, i) => (
              <li key={i}>• {l}</li>
            ))}
          </ul>
          <p className="mt-2 text-[10px] text-dark-400">
            Tip: <code className="text-amber-400">export OLLAMA_BASE_URL=http://&lt;pc-ip&gt;:11434</code>
          </p>
        </div>
      )}

      {/* Platform Info */}
      <div className="panel p-3 space-y-2">
        <h3 className="text-sm font-medium text-dark-200 font-display">Platform</h3>
        {platform && (
          <div className="grid grid-cols-2 gap-2 text-xs">
            <div className="text-dark-400">Mode</div>
            <div className="text-dark-200">{platform.platform_mode}</div>
            <div className="text-dark-400">Docker</div>
            <div className={platform.docker_available ? "text-emerald-400" : "text-dark-500"}>
              {platform.docker_available ? "Available" : "Not available"}
            </div>
            <div className="text-dark-400">Ollama</div>
            <div className={platform.ollama_available ? "text-emerald-400" : "text-dark-500"}>
              {platform.ollama_available ? "Available" : "Not available"}
            </div>
            <div className="text-dark-400">Browser</div>
            <div className="text-dark-200">{platform.browser_mode}</div>
          </div>
        )}
      </div>

      {/* Links */}
      <div className="panel p-3 space-y-2">
        <h3 className="text-sm font-medium text-dark-200 font-display">Links</h3>
        <div className="space-y-1.5">
          {[
            { label: "API Docs", url: `${API.replace("/api", "")}/docs` },
            { label: "GitHub", url: "https://github.com/amiraq1/local-manus-agent" },
            { label: "Releases", url: "https://github.com/amiraq1/local-manus-agent/releases" },
          ].map(({ label, url }) => (
            <a
              key={label}
              href={url}
              target="_blank"
              rel="noopener noreferrer"
              className="flex items-center gap-2 text-xs text-dark-400 hover:text-primary transition-colors"
            >
              <ExternalLink size={11} /> {label}
            </a>
          ))}
        </div>
      </div>
    </div>
  );
}
