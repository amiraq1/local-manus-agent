"use client";

import { Globe, ExternalLink } from "lucide-react";

interface PreviewPanelProps {
  url: string | null;
}

import { useProfileConfig } from "@/lib/platform";

export default function PreviewPanel({ url }: PreviewPanelProps) {
  const profileConfig = useProfileConfig();
  const hasSandbox = profileConfig.supportsSandbox;
  
  return (
    <div className="flex-1 flex flex-col min-h-0">
      <div className="panel-header flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Globe size={14} className="text-primary" />
          <span>Preview</span>
        </div>
        {url && (
          <a
            href={url}
            target="_blank"
            rel="noopener noreferrer"
            className="text-dark-400 hover:text-primary transition-colors flex items-center gap-1 text-xs normal-case"
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
            {...(hasSandbox ? { sandbox: "allow-scripts allow-forms allow-same-origin" } : {})}
          />
        ) : (
          <div className="text-center text-dark-500">
            <Globe size={48} className="mx-auto mb-3 opacity-20" />
            <p className="text-sm font-display">Preview will appear here</p>
            <p className="text-xs mt-1">The agent will start a preview server when needed</p>
          </div>
        )}
      </div>
    </div>
  );
}
