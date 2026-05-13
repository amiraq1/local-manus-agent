"use client";

function resolveApiUrl(): string {
  if (typeof window === "undefined") return "http://localhost:8000/api";
  if (process.env.NEXT_PUBLIC_API_URL) return process.env.NEXT_PUBLIC_API_URL;
  return `http://${window.location.hostname}:8000/api`;
}

function resolveWsUrl(): string {
  if (typeof window === "undefined") return "ws://localhost:8000/ws/agent";
  if (process.env.NEXT_PUBLIC_WS_URL) return process.env.NEXT_PUBLIC_WS_URL;
  
  const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
  return `${protocol}//${window.location.hostname}:8000/ws/agent`;
}

export const API = resolveApiUrl();
export const WS_URL = resolveWsUrl();
export const APP_VERSION = "1.2.0";
