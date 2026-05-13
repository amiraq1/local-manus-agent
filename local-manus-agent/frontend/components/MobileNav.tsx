"use client";

import { MessageSquare, FolderOpen, Users, Package, Brain, Settings } from "lucide-react";

export type MobileTab = "chat" | "files" | "agents" | "artifacts" | "memory" | "settings";

interface MobileNavProps {
  activeTab: MobileTab;
  onTabChange: (tab: MobileTab) => void;
}

const tabs: { id: MobileTab; icon: typeof MessageSquare; label: string }[] = [
  { id: "chat", icon: MessageSquare, label: "Chat" },
  { id: "files", icon: FolderOpen, label: "Files" },
  { id: "agents", icon: Users, label: "Agents" },
  { id: "artifacts", icon: Package, label: "Artifacts" },
  { id: "memory", icon: Brain, label: "Memory" },
  { id: "settings", icon: Settings, label: "Status" },
];

export default function MobileNav({ activeTab, onTabChange }: MobileNavProps) {
  return (
    <nav
      className="md:hidden fixed bottom-0 left-0 right-0 bg-dark-900/95 backdrop-blur-md border-t border-dark-700/60 z-50 safe-bottom"
      role="tablist"
      aria-label="Navigation"
    >
      <div className="flex items-center justify-around px-1 py-1">
        {tabs.map(({ id, icon: Icon, label }) => (
          <button
            key={id}
            role="tab"
            aria-selected={activeTab === id}
            onClick={() => onTabChange(id)}
            className={`flex flex-col items-center gap-0.5 px-2 py-1.5 rounded-lg transition-all duration-200 min-w-[48px] ${
              activeTab === id
                ? "text-primary bg-primary/10"
                : "text-dark-500 active:text-dark-300"
            }`}
            aria-label={label}
          >
            <Icon size={18} />
            <span className="text-[9px] font-medium">{label}</span>
          </button>
        ))}
      </div>
    </nav>
  );
}
