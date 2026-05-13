"use client";

// Define the runtime profiles
export type DeploymentProfile = "desktop" | "termux" | "low-memory" | "dev" | "production";

export interface ProfileConfig {
  animationLevel: "none" | "reduced" | "full";
  pollingIntervalMs: number;
  websocketRetryStrategy: "aggressive" | "exponential" | "fixed";
  loggingVerbosity: "error" | "warn" | "info" | "debug";
  cacheSizeMb: number;
  supportsPlaywright: boolean;
  supportsSandbox: boolean;
}

export function isAndroid(): boolean {
  if (typeof window === "undefined") return false;
  return /android/i.test(navigator.userAgent);
}

export function isTermux(): boolean {
  if (typeof window === "undefined") return false;
  // A robust check for Termux in a browser context:
  // If we are on Android and the hostname is localhost or 127.0.0.1, it's highly likely Termux.
  const isLocal = window.location.hostname === "localhost" || window.location.hostname === "127.0.0.1";
  return isAndroid() && isLocal;
}

export function isLowMemory(): boolean {
  if (typeof window === "undefined") return false;
  // Use Device Memory API if available (returns RAM in GB)
  if ("deviceMemory" in navigator) {
    return (navigator as any).deviceMemory <= 4;
  }
  // Fallback heuristic: Treat Android as potentially low memory
  return isAndroid();
}

export function getDeploymentProfile(): DeploymentProfile {
  if (process.env.NODE_ENV === "development") {
    if (isTermux()) return "termux";
    return "dev";
  }
  
  if (isTermux()) return "termux";
  if (isLowMemory()) return "low-memory";
  
  return "production";
}

export function getProfileConfig(): ProfileConfig {
  const profile = getDeploymentProfile();

  switch (profile) {
    case "termux":
      return {
        animationLevel: "none",
        pollingIntervalMs: 5000,
        websocketRetryStrategy: "fixed",
        loggingVerbosity: "error",
        cacheSizeMb: 10,
        // Auto-disable unsupported features on Termux
        supportsPlaywright: false, 
        supportsSandbox: false, 
      };
    case "low-memory":
      return {
        animationLevel: "reduced",
        pollingIntervalMs: 3000,
        websocketRetryStrategy: "exponential",
        loggingVerbosity: "warn",
        cacheSizeMb: 25,
        supportsPlaywright: true,
        supportsSandbox: true,
      };
    case "dev":
      return {
        animationLevel: "full",
        pollingIntervalMs: 1000,
        websocketRetryStrategy: "aggressive",
        loggingVerbosity: "debug",
        cacheSizeMb: 100,
        supportsPlaywright: true,
        supportsSandbox: true,
      };
    case "production":
    case "desktop":
    default:
      return {
        animationLevel: "full",
        pollingIntervalMs: 2000,
        websocketRetryStrategy: "exponential",
        loggingVerbosity: "info",
        cacheSizeMb: 100,
        supportsPlaywright: true,
        supportsSandbox: true,
      };
  }
}

export function supportsPlaywright(): boolean {
  return getProfileConfig().supportsPlaywright;
}

export function supportsSandbox(): boolean {
  return getProfileConfig().supportsSandbox;
}

import { useState, useEffect } from "react";

export function useProfileConfig(): ProfileConfig {
  const [config, setConfig] = useState<ProfileConfig>({
    animationLevel: "full",
    pollingIntervalMs: 2000,
    websocketRetryStrategy: "exponential",
    loggingVerbosity: "info",
    cacheSizeMb: 100,
    supportsPlaywright: true,
    supportsSandbox: true,
  });

  useEffect(() => {
    setConfig(getProfileConfig());
  }, []);

  return config;
}
