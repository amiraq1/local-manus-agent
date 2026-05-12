"use client";

import { useEffect, useState, useCallback } from "react";
import { Save, RotateCcw, AlertTriangle } from "lucide-react";
import ModelManagerPanel from "./ModelManagerPanel";
import ModelImportPanel from "./ModelImportPanel";

type Tab = "general" | "models" | "security" | "sandbox" | "browser" | "memory" | "termux" | "about";

const API = "http://localhost:8000/api";

export default function SettingsFullPanel() {
  const [settings, setSettings] = useState<Record<string, any> | null>(null);
  const [tab, setTab] = useState<Tab>("general");
  const [dirty, setDirty] = useState(false);
  const [saving, setSaving] = useState(false);
  const [msg, setMsg] = useState("");
  const [errors, setErrors] = useState<string[]>([]);

  const load = useCallback(async () => {
    try {
      const r = await fetch(`${API}/settings`);
      setSettings(await r.json());
      setDirty(false);
    } catch { /* ignore */ }
  }, []);

  useEffect(() => { load(); }, [load]);

  const update = (section: string, key: string, value: any) => {
    if (!settings) return;
    setSettings({ ...settings, [section]: { ...settings[section], [key]: value } });
    setDirty(true);
    setErrors([]);
  };

  const save = async () => {
    if (!settings) return;
    setSaving(true);
    setErrors([]);
    try {
      const r = await fetch(`${API}/settings`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(settings),
      });
      const data = await r.json();
      if (data.success) {
        setMsg("Saved ✓");
        setDirty(false);
        setSettings(data.settings);
      } else {
        setErrors(data.errors || ["Save failed"]);
      }
    } catch { setErrors(["Connection failed"]); }
    setSaving(false);
    setTimeout(() => setMsg(""), 3000);
  };

  const reset = async () => {
    if (!confirm("Reset all settings to defaults?")) return;
    const r = await fetch(`${API}/settings/reset`, { method: "POST" });
    const data = await r.json();
    if (data.success) { setSettings(data.settings); setDirty(false); setMsg("Reset ✓"); }
    setTimeout(() => setMsg(""), 3000);
  };

  if (!settings) return <p className="text-dark-500 text-sm p-4">Loading...</p>;

  const tabs: { id: Tab; label: string }[] = [
    { id: "general", label: "General" },
    { id: "models", label: "Models" },
    { id: "security", label: "Security" },
    { id: "sandbox", label: "Sandbox" },
    { id: "browser", label: "Browser" },
    { id: "memory", label: "Memory" },
    { id: "termux", label: "Termux" },
    { id: "about", label: "About" },
  ];

  const Switch = ({ section, field, label, disabled }: { section: string; field: string; label: string; disabled?: boolean }) => (
    <label className="flex items-center justify-between py-1">
      <span className="text-xs text-dark-300">{label}</span>
      <input type="checkbox" checked={settings[section]?.[field] ?? false} onChange={(e) => update(section, field, e.target.checked)} disabled={disabled}
        className="w-4 h-4 accent-primary" />
    </label>
  );

  const Select = ({ section, field, label, options }: { section: string; field: string; label: string; options: string[] }) => (
    <label className="flex items-center justify-between py-1">
      <span className="text-xs text-dark-300">{label}</span>
      <select value={settings[section]?.[field] ?? ""} onChange={(e) => update(section, field, e.target.value)}
        className="bg-dark-800 border border-dark-600 rounded px-2 py-0.5 text-xs text-dark-200">
        {options.map(o => <option key={o} value={o}>{o}</option>)}
      </select>
    </label>
  );

  const Input = ({ section, field, label, type = "text" }: { section: string; field: string; label: string; type?: string }) => (
    <label className="flex items-center justify-between py-1">
      <span className="text-xs text-dark-300">{label}</span>
      <input type={type} value={settings[section]?.[field] ?? ""} onChange={(e) => update(section, field, type === "number" ? Number(e.target.value) : e.target.value)}
        className="bg-dark-800 border border-dark-600 rounded px-2 py-0.5 text-xs text-dark-200 w-32 text-right" />
    </label>
  );

  const isTermux = settings.termux?.detected;

  return (
    <div className="flex flex-col h-full">
      {/* Tabs */}
      <div className="flex gap-1 px-3 pt-2 pb-1 overflow-x-auto border-b border-dark-700">
        {tabs.map(t => (
          <button key={t.id} onClick={() => setTab(t.id)}
            className={`px-2 py-1 rounded text-[10px] font-medium whitespace-nowrap ${tab === t.id ? "bg-primary/15 text-primary" : "text-dark-400 hover:text-dark-200"}`}>
            {t.label}
          </button>
        ))}
      </div>

      {/* Content */}
      <div className="flex-1 overflow-y-auto p-3 space-y-2">
        {tab === "general" && (
          <>
            <Select section="general" field="app_theme" label="Theme" options={["dark", "light"]} />
            <Select section="general" field="language" label="Language" options={["auto", "en", "ar"]} />
            <Switch section="general" field="auto_start_preview" label="Auto-start preview" />
          </>
        )}

        {tab === "models" && (
          <>
            <ModelManagerPanel />
            <ModelImportPanel />
          </>
        )}

        {tab === "security" && (
          <>
            <Select section="security" field="execution_mode" label="Execution Mode" options={["safe", "autonomous"]} />
            <Switch section="security" field="require_command_approval" label="Require command approval" />
            <Switch section="security" field="require_file_change_approval" label="Require file change approval" />
            <Switch section="security" field="allow_package_installs" label="Allow package installs" />
            <Switch section="security" field="allow_network_commands" label="Allow network commands" />
            {settings.security?.execution_mode === "autonomous" && (
              <p className="text-[10px] text-yellow-400 flex items-center gap-1"><AlertTriangle size={10} /> Autonomous mode skips approval dialogs</p>
            )}
          </>
        )}

        {tab === "sandbox" && (
          <>
            <Switch section="sandbox" field="enabled" label="Sandbox enabled" disabled={isTermux} />
            <Input section="sandbox" field="image" label="Docker image" />
            <Input section="sandbox" field="memory_limit" label="Memory limit" />
            <Input section="sandbox" field="cpu_limit" label="CPU limit" type="number" />
            <Input section="sandbox" field="command_timeout" label="Timeout (s)" type="number" />
            <Switch section="sandbox" field="network_enabled" label="Network enabled" />
            {isTermux && <p className="text-[10px] text-dark-500">Disabled in Termux (Docker not available)</p>}
          </>
        )}

        {tab === "browser" && (
          <>
            <Switch section="browser" field="enabled" label="Browser automation" disabled={isTermux} />
            <Switch section="browser" field="allow_external_urls" label="Allow external URLs" />
            <Switch section="browser" field="screenshot_enabled" label="Screenshots enabled" />
            <Input section="browser" field="default_viewport" label="Viewport" />
            {isTermux && <p className="text-[10px] text-dark-500">Disabled by default in Termux</p>}
          </>
        )}

        {tab === "memory" && (
          <>
            <Switch section="memory" field="enabled" label="Memory enabled" />
            <Switch section="memory" field="auto_index" label="Auto-index files" />
            <Switch section="memory" field="auto_summarize" label="Auto-summarize projects" />
            <Input section="memory" field="max_index_file_size" label="Max file size (bytes)" type="number" />
          </>
        )}

        {tab === "termux" && (
          <>
            <div className="text-xs text-dark-300 py-1">Detected: {isTermux ? "Yes" : "No"}</div>
            <Switch section="termux" field="force_safe_mode" label="Force Safe Mode" />
            <Select section="termux" field="browser_mode" label="Browser mode" options={["disabled", "chromium"]} />
            <Input section="termux" field="host" label="Host" />
          </>
        )}

        {tab === "about" && (
          <div className="space-y-2 text-xs text-dark-400">
            <p className="text-dark-200 font-medium">Local Manus Agent v1.0.0</p>
            <p>AI-powered local development agent</p>
            <p>Settings are saved in <code className="text-primary">backend/app/user_config.json</code></p>
            <p>System defaults are in <code className="text-primary">backend/config.py</code></p>
            <a href="https://github.com/amiraq1/local-manus-agent" target="_blank" className="text-primary hover:underline block">GitHub Repository</a>
            <a href="https://github.com/amiraq1/local-manus-agent/releases" target="_blank" className="text-primary hover:underline block">Releases</a>
          </div>
        )}
      </div>

      {/* Footer */}
      <div className="border-t border-dark-700 px-3 py-2 flex items-center gap-2">
        <button onClick={save} disabled={!dirty || saving}
          className="flex items-center gap-1 px-3 py-1 rounded bg-primary text-white text-xs font-medium disabled:opacity-40">
          <Save size={11} /> {saving ? "Saving..." : "Save"}
        </button>
        <button onClick={reset} className="flex items-center gap-1 px-2 py-1 rounded text-dark-400 hover:text-dark-200 text-xs">
          <RotateCcw size={11} /> Reset
        </button>
        {dirty && <span className="text-[10px] text-yellow-400 ml-auto">Unsaved changes</span>}
        {msg && <span className="text-[10px] text-green-400 ml-auto">{msg}</span>}
        {errors.length > 0 && <span className="text-[10px] text-red-400 ml-auto">{errors[0]}</span>}
      </div>
    </div>
  );
}
