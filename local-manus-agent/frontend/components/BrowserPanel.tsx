"use client";

import { Globe, Camera, X } from "lucide-react";

export interface BrowserState {
  active: boolean;
  url: string | null;
  title: string | null;
  lastScreenshot: string | null;
  lastAction: string | null;
}

interface BrowserPanelProps {
  state: BrowserState;
  onClose: () => void;
}

export default function BrowserPanel({ state, onClose }: BrowserPanelProps) {
  return (
    <div className="divider">
      <div className="panel-header flex items-center gap-2">
        <Globe size={14} className={state.active ? "text-emerald-400" : "text-dark-500"} />
        <span>Browser</span>
        <span className={state.active ? "badge-success" : "badge-neutral"}>
          {state.active ? "Active" : "Inactive"}
        </span>
        {state.active && (
          <button
            onClick={onClose}
            className="ml-auto text-dark-400 hover:text-red-400 transition-colors"
            title="Close browser session"
            aria-label="Close browser session"
          >
            <X size={14} />
          </button>
        )}
      </div>

      <div className="p-3 space-y-2">
        {state.url && (
          <div className="flex items-center gap-2">
            <span className="text-[10px] text-dark-500 uppercase w-10 shrink-0 tracking-wider">URL</span>
            <span className="text-xs text-dark-300 truncate flex-1 font-mono">{state.url}</span>
          </div>
        )}

        {state.title && (
          <div className="flex items-center gap-2">
            <span className="text-[10px] text-dark-500 uppercase w-10 shrink-0 tracking-wider">Title</span>
            <span className="text-xs text-dark-200 truncate flex-1">{state.title}</span>
          </div>
        )}

        {state.lastScreenshot && (
          <div className="flex items-center gap-2">
            <Camera size={12} className="text-dark-500 shrink-0" />
            <span className="text-xs text-dark-400 truncate">{state.lastScreenshot}</span>
          </div>
        )}

        {state.lastAction && (
          <div className="flex items-center gap-2">
            <span className="text-[10px] text-dark-500 uppercase w-10 shrink-0 tracking-wider">Last</span>
            <span className="text-xs text-dark-400">{state.lastAction}</span>
          </div>
        )}

        {!state.active && !state.url && (
          <p className="text-xs text-dark-500 text-center py-2">
            Browser will activate when the agent needs to test pages
          </p>
        )}
      </div>
    </div>
  );
}
