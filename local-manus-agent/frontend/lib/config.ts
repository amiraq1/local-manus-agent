"use client";

function resolveApiUrl(): string {
  if (typeof window === "undefined") return "http://127.0.0.1:8000/api";
  if (process.env.NEXT_PUBLIC_API_URL) return process.env.NEXT_PUBLIC_API_URL;
  // Use 127.0.0.1 instead of localhost for consistency
  const hostname = window.location.hostname === "localhost" ? "127.0.0.1" : window.location.hostname;
  return `http://${hostname}:8000/api`;
}

function resolveWsUrl(): string {
  if (typeof window === "undefined") return "ws://127.0.0.1:8000/ws/agent";
  if (process.env.NEXT_PUBLIC_WS_URL) return process.env.NEXT_PUBLIC_WS_URL;
  
  const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
  // Use 127.0.0.1 instead of localhost for better cross-browser compatibility with local services
  const hostname = window.location.hostname === "localhost" ? "127.0.0.1" : window.location.hostname;
  return `${protocol}//${hostname}:8000/ws/agent`;
}

export const API = resolveApiUrl();
export const WS_URL = resolveWsUrl();
export const APP_VERSION = "1.2.0";
