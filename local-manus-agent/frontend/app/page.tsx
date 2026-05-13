"use client";

import { useState, Suspense } from "react";
import dynamic from "next/dynamic";
import ChatPanel from "@/components/ChatPanel";
import PlanPanel from "@/components/PlanPanel";
import FileExplorer from "@/components/FileExplorer";
import PreviewPanel from "@/components/PreviewPanel";
import ToolLog from "@/components/ToolLog";
import TaskHistory from "@/components/TaskHistory";
import ApprovalDialog from "@/components/ApprovalDialog";
import ModeSwitch from "@/components/ModeSwitch";
import SandboxStatus from "@/components/SandboxStatus";
import LLMStatusPanel from "@/components/LLMStatusPanel";
import ArtifactsPanel from "@/components/ArtifactsPanel";
import MemoryPanel from "@/components/MemoryPanel";
import AgentsPanel from "@/components/AgentsPanel";
import ExportPanel from "@/components/ExportPanel";
import MobileNav, { MobileTab } from "@/components/MobileNav";
import GoalModePanel from "@/components/GoalModePanel";
import ErrorBoundary from "@/components/ErrorBoundary";
import { ToastProvider } from "@/components/Toast";
import { useAgent } from "@/lib/useAgent";
import { APP_VERSION } from "@/lib/config";
import { useProfileConfig } from "@/lib/platform";

function PanelLoader() {
  return (
    <div className="p-6 space-y-3">
      <div className="skeleton h-4 w-32" />
      <div className="skeleton h-3 w-48" />
      <div className="skeleton h-3 w-40" />
    </div>
  );
}

// Lazy-load heavy panels using next/dynamic to avoid SSR hydration errors
const SettingsFullPanel = dynamic(() => import("@/components/SettingsFullPanel"), { ssr: false, loading: () => <PanelLoader /> });
const TemplatesPanel = dynamic(() => import("@/components/TemplatesPanel"), { ssr: false, loading: () => <PanelLoader /> });
const BrowserPanel = dynamic(() => import("@/components/BrowserPanel"), { ssr: false, loading: () => <PanelLoader /> });
const FileDiffPanel = dynamic(() => import("@/components/FileDiffPanel"), { ssr: false, loading: () => <PanelLoader /> });


export default function Home() {
  const {
    messages,
    plan,
    toolLogs,
    files,
    previewUrl,
    isRunning,
    mode,
    pendingApproval,
    taskHistory,
    currentTaskId,
    browserState,
    fileChanges,
    agentSteps,
    sendTask,
    approveCommand,
    rejectCommand,
    refreshFiles,
    loadTask,
    switchMode,
    closeBrowser,
    acceptChange,
    rejectChange,
  } = useAgent();

  const [mobileTab, setMobileTab] = useState<MobileTab>("chat");
  const profileConfig = useProfileConfig();

  return (
    <ToastProvider>
      <div className="h-screen flex flex-col">
        {/* Header */}
        <header className="border-b border-dark-700/60 px-4 md:px-6 py-2.5 md:py-3 flex items-center gap-3">
          <div className="w-8 h-8 bg-gradient-to-br from-primary to-emerald-400 rounded-lg flex items-center justify-center shrink-0 shadow-[0_0_12px_rgba(0,229,160,0.2)]">
            <span className="text-dark-950 font-bold text-sm font-display">M</span>
          </div>
          <div className="flex flex-col">
            <h1 className="text-sm md:text-base font-semibold text-dark-50 font-display tracking-tight">
              Local Manus Agent
            </h1>
            <span className="text-[9px] text-dark-500 font-mono hidden sm:block">v{APP_VERSION}</span>
          </div>

          <div className="ml-auto flex items-center gap-3">
            <ModeSwitch mode={mode} onSwitch={switchMode} />
            {isRunning && (
              <span className="flex items-center gap-2 text-xs text-primary">
                <span className="w-2 h-2 bg-primary rounded-full animate-glow-pulse" />
                <span className="hidden sm:inline font-medium">Working...</span>
              </span>
            )}
          </div>
        </header>

        {/* Desktop Layout (md+) */}
        <div className="flex-1 hidden md:flex overflow-hidden">
          {/* Left */}
          <div className="w-[440px] flex flex-col border-r border-dark-700/60">
            <ErrorBoundary>
              <TaskHistory tasks={taskHistory} currentTaskId={currentTaskId} onSelect={loadTask} />
              <ChatPanel messages={messages} isRunning={isRunning} onSend={sendTask} />
              <PlanPanel plan={plan} />
              <AgentsPanel steps={agentSteps} />
            </ErrorBoundary>
          </div>

          {/* Center */}
          <div className="flex-1 flex flex-col">
            <ErrorBoundary>
              <PreviewPanel url={previewUrl} />
              <FileDiffPanel changes={fileChanges} onAccept={acceptChange} onReject={rejectChange} />
            </ErrorBoundary>
          </div>

          {/* Right */}
          <div className="w-[320px] flex flex-col border-l border-dark-700/60 overflow-y-auto">
            <ErrorBoundary>
              <FileExplorer files={files} onRefresh={refreshFiles} />
              {profileConfig.supportsPlaywright && (
                <BrowserPanel state={browserState} onClose={closeBrowser} />
              )}
              <ArtifactsPanel taskId={currentTaskId} />
              <MemoryPanel taskId={currentTaskId} />
              <SandboxStatus />
              <LLMStatusPanel />
              <ToolLog logs={toolLogs} />
            </ErrorBoundary>
          </div>
        </div>

        {/* Mobile Layout (< md) */}
        <div className="flex-1 md:hidden flex flex-col overflow-hidden pb-14">
          <ErrorBoundary>
            {mobileTab === "chat" && (
              <div className="flex-1 flex flex-col">
                <GoalModePanel />
                <ChatPanel messages={messages} isRunning={isRunning} onSend={sendTask} />
                <PlanPanel plan={plan} />
              </div>
            )}
            {mobileTab === "files" && (
              <div className="flex-1 flex flex-col overflow-y-auto">
                <FileExplorer files={files} onRefresh={refreshFiles} />
                <TemplatesPanel taskId={currentTaskId} onGenerated={refreshFiles} />
                <PreviewPanel url={previewUrl} />
                <FileDiffPanel changes={fileChanges} onAccept={acceptChange} onReject={rejectChange} />
              </div>
            )}
            {mobileTab === "agents" && (
              <div className="flex-1 flex flex-col overflow-y-auto">
                <AgentsPanel steps={agentSteps} />
                <ToolLog logs={toolLogs} />
                <BrowserPanel state={browserState} onClose={closeBrowser} />
              </div>
            )}
            {mobileTab === "artifacts" && (
              <div className="flex-1 overflow-y-auto">
                <ArtifactsPanel taskId={currentTaskId} />
                <ExportPanel taskId={currentTaskId} />
                <TaskHistory tasks={taskHistory} currentTaskId={currentTaskId} onSelect={loadTask} />
              </div>
            )}
            {mobileTab === "memory" && (
              <div className="flex-1 overflow-y-auto">
                <MemoryPanel taskId={currentTaskId} />
              </div>
            )}
            {mobileTab === "settings" && (
              <div className="flex-1 overflow-y-auto">
                <SettingsFullPanel />
              </div>
            )}
          </ErrorBoundary>
        </div>

        {/* Mobile Bottom Nav */}
        <MobileNav activeTab={mobileTab} onTabChange={setMobileTab} />

        {/* Approval Dialog */}
        {pendingApproval && (
          <ApprovalDialog
            command={pendingApproval.command}
            onApprove={approveCommand}
            onReject={rejectCommand}
          />
        )}
      </div>
    </ToastProvider>
  );
}
