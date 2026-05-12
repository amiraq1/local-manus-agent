"use client";

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
import SandboxStatus from "@/components/SandboxStatus";
import LLMStatusPanel from "@/components/LLMStatusPanel";
import ArtifactsPanel from "@/components/ArtifactsPanel";
import MemoryPanel from "@/components/MemoryPanel";
import AgentsPanel from "@/components/AgentsPanel";
import { useAgent } from "@/lib/useAgent";

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

  return (
    <div className="h-screen flex flex-col">
      {/* Header */}
      <header className="border-b border-dark-700 px-6 py-3 flex items-center gap-3">
        <div className="w-8 h-8 bg-primary rounded-lg flex items-center justify-center">
          <span className="text-white font-bold text-sm">M</span>
        </div>
        <h1 className="text-lg font-semibold text-dark-100">Local Manus Agent</h1>
        <span className="text-xs text-dark-500 ml-2">v2.2</span>

        <div className="ml-auto flex items-center gap-4">
          <ModeSwitch mode={mode} onSwitch={switchMode} />
          {isRunning && (
            <span className="flex items-center gap-2 text-sm text-primary">
              <span className="w-2 h-2 bg-primary rounded-full animate-pulse" />
              Working...
            </span>
          )}
        </div>
      </header>

      {/* Main Layout */}
      <div className="flex-1 flex overflow-hidden">
        {/* Left: History + Chat + Plan */}
        <div className="w-[440px] flex flex-col border-r border-dark-700">
          <TaskHistory
            tasks={taskHistory}
            currentTaskId={currentTaskId}
            onSelect={loadTask}
          />
          <ChatPanel messages={messages} isRunning={isRunning} onSend={sendTask} />
          <PlanPanel plan={plan} />
          <AgentsPanel steps={agentSteps} />
        </div>

        {/* Center: Preview + Diff */}
        <div className="flex-1 flex flex-col">
          <PreviewPanel url={previewUrl} />
          <FileDiffPanel
            changes={fileChanges}
            onAccept={acceptChange}
            onReject={rejectChange}
          />
        </div>

        {/* Right: Files + Browser + Sandbox + Tool Log */}
        <div className="w-[320px] flex flex-col border-l border-dark-700">
          <FileExplorer files={files} onRefresh={refreshFiles} />
          <BrowserPanel state={browserState} onClose={closeBrowser} />
          <ArtifactsPanel taskId={currentTaskId} />
          <MemoryPanel taskId={currentTaskId} />
          <SandboxStatus />
          <LLMStatusPanel />
          <ToolLog logs={toolLogs} />
        </div>
      </div>

      {/* Approval Dialog */}
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
