"use client";

import { useState } from "react";
import ChatPanel from "@/components/ChatPanel";
import PlanPanel from "@/components/PlanPanel";
import FileExplorer from "@/components/FileExplorer";
import PreviewPanel from "@/components/PreviewPanel";
import ToolLog from "@/components/ToolLog";
import TaskHistory from "@/components/TaskHistory";
import ApprovalDialog from "@/components/ApprovalDialog";
import ModeSwitch from "@/components/ModeSwitch";
import BrowserPanel from "@/components/BrowserPanel";
import FileDiffPanel from "@/components/FileDiffPanel";
import TemplatesPanel from "@/components/TemplatesPanel";
import SandboxStatus from "@/components/SandboxStatus";
import LLMStatusPanel from "@/components/LLMStatusPanel";
import ArtifactsPanel from "@/components/ArtifactsPanel";
import MemoryPanel from "@/components/MemoryPanel";
import AgentsPanel from "@/components/AgentsPanel";
import ExportPanel from "@/components/ExportPanel";
import MobileNav, { MobileTab } from "@/components/MobileNav";
import GoalModePanel from "@/components/GoalModePanel";
import SettingsPanel from "@/components/SettingsPanel";
import SecurityPanel from "@/components/SecurityPanel";
import ModelManagerPanel from "@/components/ModelManagerPanel";
import SettingsFullPanel from "@/components/SettingsFullPanel";
import { useAgent } from "@/lib/useAgent";

export default function HomeClient() {
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

  return (
    <div className="h-screen flex flex-col">
      {/* Header */}
      <header className="border-b border-dark-700 px-4 md:px-6 py-2 md:py-3 flex items-center gap-2 md:gap-3">
        <div className="w-7 h-7 md:w-8 md:h-8 bg-primary rounded-lg flex items-center justify-center shrink-0">
          <span className="text-white font-bold text-xs md:text-sm">M</span>
        </div>
        <h1 className="text-sm md:text-lg font-semibold text-dark-100 truncate">Local Manus Agent</h1>

        <div className="ml-auto flex items-center gap-2 md:gap-4">
          <ModeSwitch mode={mode} onSwitch={switchMode} />
          {isRunning && (
            <span className="flex items-center gap-1.5 text-xs md:text-sm text-primary">
              <span className="w-2 h-2 bg-primary rounded-full animate-pulse" />
              <span className="hidden sm:inline">Working...</span>
            </span>
          )}
        </div>
      </header>

      {/* Desktop Layout (md+) */}
      <div className="flex-1 hidden md:flex overflow-hidden">
        <div className="w-[440px] flex flex-col border-r border-dark-700">
          <TaskHistory tasks={taskHistory} currentTaskId={currentTaskId} onSelect={loadTask} />
          <ChatPanel messages={messages} isRunning={isRunning} onSend={sendTask} />
          <PlanPanel plan={plan} />
          <AgentsPanel steps={agentSteps} />
        </div>
        <div className="flex-1 flex flex-col">
          <PreviewPanel url={previewUrl} />
          <FileDiffPanel changes={fileChanges} onAccept={acceptChange} onReject={rejectChange} />
        </div>
        <div className="w-[320px] flex flex-col border-l border-dark-700 overflow-y-auto">
          <FileExplorer files={files} onRefresh={refreshFiles} />
          <BrowserPanel state={browserState} onClose={closeBrowser} />
          <ArtifactsPanel taskId={currentTaskId} />
          <MemoryPanel taskId={currentTaskId} />
          <SandboxStatus />
          <LLMStatusPanel />
          <ToolLog logs={toolLogs} />
        </div>
      </div>

      {/* Mobile Layout (< md) */}
      <div className="flex-1 md:hidden flex flex-col overflow-hidden pb-14">
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
      </div>

      <MobileNav activeTab={mobileTab} onTabChange={setMobileTab} />

      {pendingApproval && (
        <ApprovalDialog
          command={pendingApproval.command}
          onApprove={approveCommand}
          onReject={rejectCommand}
        />
      )}
    </div>
  );
}
