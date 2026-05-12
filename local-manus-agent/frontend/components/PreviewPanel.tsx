"use client";

import { Globe, ExternalLink } from "lucide-react";

interface PreviewPanelProps {
  url: string | null;
}

export default function PreviewPanel({ url }: PreviewPanelProps) {
  return (
    <div className="flex-1 flex flex-col min-h-0">
      <div className="panel-header flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Globe size={14} />
          <span>Preview</span>
        </div>
        {url && (
          <a
            href={url}
            target="_blank"
            rel="noopener noreferrer"
            className="text-dark-400 hover:text-dark-200 transition-colors flex items-center gap-1 text-xs"
          >
            Open <ExternalLink size={12} />
          </a>
        )}
      </div>
      <div className="flex-1 bg-dark-950 flex items-center justify-center">
        {url ? (
          <iframe
            src={url}
            className="w-full h-full border-0"
            title="Preview"
            sandbox="allow-scripts allow-same-origin allow-forms"
          />
        ) : (
          <div className="text-center text-dark-500">
            <Globe size={48} className="mx-auto mb-3 opacity-30" />
            <p className="text-sm">Preview will appear here</p>
            <p className="text-xs mt-1">The agent will start a preview server when needed</p>
          </div>
        )}
      </div>
    </div>
  );
}
