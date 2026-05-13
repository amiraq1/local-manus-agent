"use client";

import { File, Folder, RefreshCw } from "lucide-react";
import { formatSize } from "@/lib/utils";

export interface FileItem {
  path: string;
  type: "file" | "directory";
  size: number;
}

interface FileExplorerProps {
  files: FileItem[];
  onRefresh: () => void;
}

export default function FileExplorer({ files, onRefresh }: FileExplorerProps) {
  return (
    <div className="flex-1 flex flex-col min-h-0">
      <div className="panel-header flex items-center justify-between">
        <span>Project Files</span>
        <button
          onClick={onRefresh}
          className="text-dark-400 hover:text-primary transition-colors"
          aria-label="Refresh files"
        >
          <RefreshCw size={14} />
        </button>
      </div>
      <div className="flex-1 overflow-y-auto p-2">
        {files.length === 0 ? (
          <div className="text-center mt-6 animate-fade-in">
            <Folder size={32} className="mx-auto mb-2 text-dark-600" />
            <p className="text-dark-500 text-sm">No files yet</p>
          </div>
        ) : (
          <div className="space-y-0.5">
            {files.map((file) => (
              <div
                key={file.path}
                className="flex items-center gap-2 px-2.5 py-1.5 rounded-lg hover:bg-dark-800/60 text-sm cursor-default transition-colors group"
              >
                {file.type === "directory" ? (
                  <Folder size={14} className="text-amber-400 shrink-0" />
                ) : (
                  <File size={14} className="text-dark-400 shrink-0" />
                )}
                <span className="text-dark-200 truncate flex-1 text-xs">{file.path}</span>
                <span className="text-dark-500 text-[10px] shrink-0 opacity-0 group-hover:opacity-100 transition-opacity">
                  {formatSize(file.size)}
                </span>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
