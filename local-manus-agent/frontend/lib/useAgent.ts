"use client";

import { useState, useCallback, useRef, useEffect } from "react";
import { Message } from "@/components/ChatPanel";
import { PlanStep } from "@/components/PlanPanel";
import { FileItem } from "@/components/FileExplorer";
import { ToolLogEntry } from "@/components/ToolLog";
import { BrowserState } from "@/components/BrowserPanel";
import { FileChange } from "@/components/FileDiffPanel";

const WS_URL = "ws://localhost:8000/ws/agent";
const API_URL = "http://localhost:8000/api";

export interface PendingApproval {
  approval_id: number;
  command: string;
  task_id: string;
}

export interface TaskSummary {
  id: string;
  message: string;
  status: string;
  mode: string;
  created_at: number;
  completed_at: number | null;
  summary: string | null;
}

export function useAgent() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [plan, setPlan] = useState<PlanStep[]>([]);
  const [toolLogs, setToolLogs] = useState<ToolLogEntry[]>([]);
  const [files, setFiles] = useState<FileItem[]>([]);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const [isRunning, setIsRunning] = useState(false);
  const [mode, setMode] = useState<"safe" | "autonomous">("safe");
  const [pendingApproval, setPendingApproval] = useState<PendingApproval | null>(null);
  const [taskHistory, setTaskHistory] = useState<TaskSummary[]>([]);
  const [currentTaskId, setCurrentTaskId] = useState<string | null>(null);
  const [browserState, setBrowserState] = useState<BrowserState>({
    active: false,
    url: null,
    title: null,
    lastScreenshot: null,
    lastAction: null,
  });
  const [fileChanges, setFileChanges] = useState<FileChange[]>([]);
  const wsRef = useRef<WebSocket | null>(null);

  const connectWs = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN) return;

    const ws = new WebSocket(WS_URL);

    ws.onopen = () => {
      console.log("WebSocket connected");
    };

    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      handleWsMessage(data);
    };

    ws.onclose = () => {
      console.log("WebSocket disconnected");
      setTimeout(connectWs, 3000);
    };

    ws.onerror = (err) => {
      console.error("WebSocket error:", err);
    };

    wsRef.current = ws;
  }, []);

  const handleWsMessage = useCallback((data: Record<string, unknown>) => {
    switch (data.type) {
      case "task_started":
        setIsRunning(true);
        setCurrentTaskId(data.task_id as string);
        break;

      case "agent_event": {
        const event = data.event as Record<string, unknown>;
        const phase = event.phase as string;

        const msg: Message = {
          id: `${Date.now()}-${Math.random()}`,
          role: "agent",
          content: event.content as string,
          phase,
          timestamp: Date.now(),
        };
        setMessages((prev) => [...prev, msg]);

        // Handle plan
        if (phase === "plan_ready" && event.plan) {
          const steps = (event.plan as Array<Record<string, string>>).map((s) => ({
            description: s.description,
            tool: s.tool,
            status: "pending" as const,
          }));
          setPlan(steps);
        }

        // Update plan step status
        if (phase === "executing" && typeof event.step_index === "number") {
          setPlan((prev) =>
            prev.map((s, i) => ({
              ...s,
              status:
                i === (event.step_index as number)
                  ? "running"
                  : i < (event.step_index as number)
                  ? "done"
                  : s.status,
            }))
          );
        }

        if (phase === "observation") {
          setPlan((prev) => {
            const lastRunning = prev.findIndex((s) => s.status === "running");
            if (lastRunning >= 0) {
              const result = event.result as Record<string, unknown>;
              const newPlan = [...prev];
              newPlan[lastRunning] = {
                ...newPlan[lastRunning],
                status: result?.success ? "done" : "error",
              };
              return newPlan;
            }
            return prev;
          });
        }

        // Handle tool log
        if (event.tool_log) {
          const log = event.tool_log as ToolLogEntry;
          setToolLogs((prev) => [...prev, { ...log, timestamp: Date.now() }]);
        }

        // Check for preview URL
        if (phase === "observation") {
          const result = event.result as Record<string, unknown> | undefined;
          if (result?.result) {
            const toolResult = result.result as Record<string, unknown>;
            if (toolResult.url && typeof toolResult.url === "string") {
              setPreviewUrl(toolResult.url);
            }
          }
        }

        // Track browser state from tool logs
        if (event.tool_log) {
          const log = event.tool_log as Record<string, unknown>;
          const tool = log.tool as string;
          if (tool?.startsWith("browser_")) {
            const result = (event.result as Record<string, unknown>)?.result as Record<string, unknown> | undefined;
            if (tool === "browser_open_url") {
              setBrowserState((prev) => ({
                ...prev,
                active: true,
                url: result?.url as string || prev.url,
                title: result?.title as string || prev.title,
                lastAction: "open_url",
              }));
            } else if (tool === "browser_get_title") {
              setBrowserState((prev) => ({
                ...prev,
                title: result?.title as string || prev.title,
                lastAction: "get_title",
              }));
            } else if (tool === "browser_screenshot") {
              setBrowserState((prev) => ({
                ...prev,
                lastScreenshot: result?.path as string || prev.lastScreenshot,
                lastAction: "screenshot",
              }));
            } else if (tool === "browser_close") {
              setBrowserState({
                active: false,
                url: null,
                title: null,
                lastScreenshot: null,
                lastAction: null,
              });
            } else {
              setBrowserState((prev) => ({ ...prev, lastAction: tool.replace("browser_", "") }));
            }
          }
        }

        break;
      }

      case "approval_request": {
        setPendingApproval({
          approval_id: data.approval_id as number,
          command: data.command as string,
          task_id: data.task_id as string,
        });
        break;
      }

      case "task_completed":
        setIsRunning(false);
        refreshFiles();
        loadTaskHistory();
        // Load file changes for the completed task
        fetch(`${API_URL}/changes`)
          .then((r) => r.json())
          .then((d) => setFileChanges(d.changes || []))
          .catch(() => {});
        break;

      case "error":
        setIsRunning(false);
        setMessages((prev) => [
          ...prev,
          {
            id: `err-${Date.now()}`,
            role: "agent",
            content: `Error: ${data.message}`,
            phase: "error",
            timestamp: Date.now(),
          },
        ]);
        break;
    }
  }, []);

  const sendTask = useCallback(
    (message: string) => {
      setMessages((prev) => [
        ...prev,
        {
          id: `user-${Date.now()}`,
          role: "user",
          content: message,
          timestamp: Date.now(),
        },
      ]);

      setPlan([]);
      setToolLogs([]);
      setPendingApproval(null);

      if (!wsRef.current || wsRef.current.readyState !== WebSocket.OPEN) {
        connectWs();
        setTimeout(() => {
          wsRef.current?.send(
            JSON.stringify({ type: "task", content: message, mode })
          );
        }, 500);
      } else {
        wsRef.current.send(
          JSON.stringify({ type: "task", content: message, mode })
        );
      }
    },
    [connectWs, mode]
  );

  const approveCommand = useCallback(() => {
    if (!pendingApproval) return;
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(
        JSON.stringify({ type: "approve", approval_id: pendingApproval.approval_id })
      );
    }
    setPendingApproval(null);
  }, [pendingApproval]);

  const rejectCommand = useCallback(() => {
    if (!pendingApproval) return;
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(
        JSON.stringify({ type: "reject", approval_id: pendingApproval.approval_id })
      );
    }
    setPendingApproval(null);
  }, [pendingApproval]);

  const refreshFiles = useCallback(async () => {
    try {
      const res = await fetch(`${API_URL}/files`);
      const data = await res.json();
      setFiles(data.files || []);
    } catch {
      // Backend might not be running
    }
  }, []);

  const loadTaskHistory = useCallback(async () => {
    try {
      const res = await fetch(`${API_URL}/tasks`);
      const data = await res.json();
      setTaskHistory(data.tasks || []);
    } catch {
      // Backend might not be running
    }
  }, []);

  const loadTask = useCallback(async (taskId: string) => {
    try {
      const res = await fetch(`${API_URL}/tasks/${taskId}`);
      const data = await res.json();
      if (data.error) return;

      setCurrentTaskId(taskId);

      // Restore messages
      const msgs: Message[] = (data.messages || []).map((m: Record<string, unknown>, i: number) => ({
        id: `hist-${i}`,
        role: m.role as string,
        content: m.content as string,
        phase: m.phase as string | undefined,
        timestamp: (m.created_at as number) * 1000,
      }));
      setMessages(msgs);

      // Restore plan
      const steps: PlanStep[] = (data.plan_steps || []).map((s: Record<string, unknown>) => ({
        description: s.description as string,
        tool: s.tool as string,
        status: s.status as "pending" | "running" | "done" | "error",
      }));
      setPlan(steps);

      // Restore tool logs
      const logs: ToolLogEntry[] = (data.tool_logs || []).map((l: Record<string, unknown>) => ({
        step: l.step_index as number,
        tool: l.tool as string,
        params: JSON.parse((l.params as string) || "{}"),
        success: l.success === 1,
      }));
      setToolLogs(logs);
    } catch {
      // ignore
    }
  }, []);

  const switchMode = useCallback((newMode: "safe" | "autonomous") => {
    setMode(newMode);
    fetch(`${API_URL}/mode`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ mode: newMode }),
    }).catch(() => {});
  }, []);

  // Connect on mount
  useEffect(() => {
    connectWs();
    refreshFiles();
    loadTaskHistory();
    return () => {
      wsRef.current?.close();
    };
  }, [connectWs, refreshFiles, loadTaskHistory]);

  const closeBrowser = useCallback(async () => {
    try {
      await fetch(`${API_URL}/browser/close`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ task_id: currentTaskId || "default" }),
      });
      setBrowserState({
        active: false,
        url: null,
        title: null,
        lastScreenshot: null,
        lastAction: null,
      });
    } catch {
      // ignore
    }
  }, [currentTaskId]);

  const loadFileChanges = useCallback(async () => {
    try {
      const url = currentTaskId
        ? `${API_URL}/tasks/${currentTaskId}/changes`
        : `${API_URL}/changes`;
      const res = await fetch(url);
      const data = await res.json();
      setFileChanges(data.changes || []);
    } catch {
      // ignore
    }
  }, [currentTaskId]);

  const acceptChange = useCallback(async (changeId: string) => {
    try {
      await fetch(`${API_URL}/changes/${changeId}/accept`, { method: "POST" });
      setFileChanges((prev) =>
        prev.map((c) => (c.id === changeId ? { ...c, status: "applied" as const } : c))
      );
    } catch {
      // ignore
    }
  }, []);

  const rejectChange = useCallback(async (changeId: string) => {
    try {
      await fetch(`${API_URL}/changes/${changeId}/reject`, { method: "POST" });
      setFileChanges((prev) =>
        prev.map((c) => (c.id === changeId ? { ...c, status: "rejected" as const } : c))
      );
    } catch {
      // ignore
    }
  }, []);

  return {
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
    sendTask,
    approveCommand,
    rejectCommand,
    refreshFiles,
    loadTaskHistory,
    loadTask,
    switchMode,
    closeBrowser,
    loadFileChanges,
    acceptChange,
    rejectChange,
  };
}
