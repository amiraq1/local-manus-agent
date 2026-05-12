"use client";

import { File, Folder, RefreshCw } from "lucide-react";

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
  const formatSize = (bytes: number) => {
    if (bytes === 0) return "";
    if (bytes < 1024) return `${bytes}B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)}KB`;
    return `${(bytes / (1024 * 1024)).toFixed(1)}MB`;
  };

  return (
    <div className="flex-1 flex flex-col min-h-0">
      <div className="panel-header flex items-center justify-between">
        <span>Project Files</span>
        <button
          onClick={onRefresh}
          className="text-dark-400 hover:text-dark-200 transition-colors"
          aria-label="Refresh files"
        >
          <RefreshCw size={14} />
        </button>
      </div>
      <div className="flex-1 overflow-y-auto p-2">
        {files.length === 0 ? (
          <p className="text-dark-500 text-sm text-center mt-4">No files yet</p>
        ) : (
          <div className="space-y-0.5">
            {files.map((file) => (
              <div
                key={file.path}
                className="flex items-center gap-2 px-2 py-1 rounded hover:bg-dark-800 text-sm cursor-default"
              >
                {file.type === "directory" ? (
                  <Folder size={14} className="text-yellow-400 shrink-0" />
                ) : (
                  <File size={14} className="text-dark-400 shrink-0" />
                )}
                <span className="text-dark-200 truncate flex-1">{file.path}</span>
                <span className="text-dark-500 text-xs shrink-0">
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
