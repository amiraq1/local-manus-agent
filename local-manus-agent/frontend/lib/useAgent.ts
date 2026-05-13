"use client";

import { useState, useCallback, useRef, useEffect } from "react";
import { Message } from "@/components/ChatPanel";
import { PlanStep } from "@/components/PlanPanel";
import { FileItem } from "@/components/FileExplorer";
import { ToolLogEntry } from "@/components/ToolLog";
import { BrowserState } from "@/components/BrowserPanel";
import { FileChange } from "@/components/FileDiffPanel";
import { API, WS_URL } from "@/lib/config";
import { getProfileConfig } from "@/lib/platform";

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
  const [agentSteps, setAgentSteps] = useState<Array<{agent: string; phase: string; status: "running" | "completed" | "error" | "skipped"; summary: string}>>([]);

  const wsRef = useRef<WebSocket | null>(null);
  const messageQueueRef = useRef<string[]>([]);
  const connectingRef = useRef(false);
  const isUnmountedRef = useRef(false);
  const retryCountRef = useRef(0);
  const profileConfig = getProfileConfig();

  // FIX #1: Use refs for callbacks called inside WS handler to avoid stale closures
  const refreshFilesRef = useRef<() => void>(() => {});
  const loadTaskHistoryRef = useRef<() => void>(() => {});

  const refreshFiles = useCallback(async () => {
    try {
      const res = await fetch(`${API}/files`);
      if (!res.ok) return;
      const data = await res.json();
      setFiles(data.files || []);
    } catch {
      // Backend might not be running
    }
  }, []);

  const loadTaskHistory = useCallback(async () => {
    try {
      const res = await fetch(`${API}/tasks`);
      if (!res.ok) return;
      const data = await res.json();
      setTaskHistory(data.tasks || []);
    } catch {
      // Backend might not be running
    }
  }, []);

  // Keep refs current
  refreshFilesRef.current = refreshFiles;
  loadTaskHistoryRef.current = loadTaskHistory;

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

        // Track agent steps from multi-agent events
        if ((event as Record<string, unknown>).event_type === "agent_step" || (event as Record<string, unknown>).agent) {
          const agent = (event as Record<string, unknown>).agent as string;
          const status = (event as Record<string, unknown>).status as string;
          if (agent && status) {
            setAgentSteps((prev) => [...prev, {
              agent,
              phase: phase,
              status: status as "running" | "completed" | "error" | "skipped",
              summary: (event.content as string) || "",
            }]);
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
        // FIX #1: Use refs instead of direct calls — avoids stale closure
        refreshFilesRef.current();
        loadTaskHistoryRef.current();
        // Load file changes for the completed task
        fetch(`${API}/changes`)
          .then((r) => { if (r.ok) return r.json(); throw new Error(); })
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

  // FIX #2: WebSocket connection with message queue — no more setTimeout race condition
  const connectWs = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN) return;
    if (connectingRef.current) return;
    connectingRef.current = true;

    const ws = new WebSocket(WS_URL);

    ws.onopen = () => {
      connectingRef.current = false;
      retryCountRef.current = 0; // Reset retry count on success
      // Flush queued messages
      while (messageQueueRef.current.length > 0) {
        const msg = messageQueueRef.current.shift()!;
        ws.send(msg);
      }
    };

    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      handleWsMessage(data);
    };

    ws.onclose = () => {
      connectingRef.current = false;
      if (!isUnmountedRef.current) {
        let delay = profileConfig.pollingIntervalMs;
        if (profileConfig.websocketRetryStrategy === "exponential") {
          delay = Math.min(delay * Math.pow(2, retryCountRef.current), 30000);
        }
        retryCountRef.current++;
        setTimeout(connectWs, delay);
      }
    };

    ws.onerror = () => {
      connectingRef.current = false;
    };

    wsRef.current = ws;
  }, [handleWsMessage]);

  /** Queue-safe send — buffers if WS not open, flushes on connect */
  const wsSend = useCallback((payload: object) => {
    const msg = JSON.stringify(payload);
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(msg);
    } else {
      messageQueueRef.current.push(msg);
      connectWs();
    }
  }, [connectWs]);

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
      setAgentSteps([]);

      wsSend({ type: "task", content: message, mode });
    },
    [wsSend, mode]
  );

  const approveCommand = useCallback(() => {
    if (!pendingApproval) return;
    wsSend({ type: "approve", approval_id: pendingApproval.approval_id });
    setPendingApproval(null);
  }, [pendingApproval, wsSend]);

  const rejectCommand = useCallback(() => {
    if (!pendingApproval) return;
    wsSend({ type: "reject", approval_id: pendingApproval.approval_id });
    setPendingApproval(null);
  }, [pendingApproval, wsSend]);

  const loadTask = useCallback(async (taskId: string) => {
    try {
      const res = await fetch(`${API}/tasks/${taskId}`);
      if (!res.ok) return;
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
    fetch(`${API}/mode`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ mode: newMode }),
    }).catch(() => {});
  }, []);

  // Connect on mount
  useEffect(() => {
    isUnmountedRef.current = false;
    connectWs();
    refreshFiles();
    loadTaskHistory();
    return () => {
      isUnmountedRef.current = true;
      if (wsRef.current) {
        wsRef.current.onclose = null;
        wsRef.current.onerror = null;
        wsRef.current.close();
      }
    };
  }, [connectWs, refreshFiles, loadTaskHistory]);

  const closeBrowser = useCallback(async () => {
    try {
      await fetch(`${API}/browser/close`, {
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


  const acceptChange = useCallback(async (changeId: string) => {
    try {
      const res = await fetch(`${API}/changes/${changeId}/accept`, { method: "POST" });
      if (!res.ok) throw new Error("Failed to accept change");
      setFileChanges((prev) =>
        prev.map((c) => (c.id === changeId ? { ...c, status: "applied" as const } : c))
      );
    } catch {
      // FIX: Don't update state on failure
    }
  }, []);

  const rejectChange = useCallback(async (changeId: string) => {
    try {
      const res = await fetch(`${API}/changes/${changeId}/reject`, { method: "POST" });
      if (!res.ok) throw new Error("Failed to reject change");
      setFileChanges((prev) =>
        prev.map((c) => (c.id === changeId ? { ...c, status: "rejected" as const } : c))
      );
    } catch {
      // FIX: Don't update state on failure
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
    agentSteps,
    sendTask,
    approveCommand,
    rejectCommand,
    refreshFiles,
    loadTaskHistory,
    loadTask,
    switchMode,
    closeBrowser,
    acceptChange,
    rejectChange,
  };
}
