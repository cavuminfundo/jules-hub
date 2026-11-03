import React, { useState, useEffect, useCallback } from 'react';
import {
  Sliders,
  GitBranch,
  Cpu,
  Key,
  Save,
  CheckCircle2,
  AlertCircle,
  Plus,
  Trash2,
  ArrowLeft,
  RefreshCw,
  Lock,
} from 'lucide-react';
import type {
  CommunitySettings,
  GitAuthoringMode,
  HubConfig,
  OllamaInstance,
  OllamaProbeResult,
  SecretsUpdateRequest,
} from '../types';
import { api, ApiError } from '../api';

interface SettingsViewProps {
  onClose?: () => void;
  onSaveConfig?: (cfg: HubConfig) => void;
}

const DEFAULT_SETTINGS: CommunitySettings = {
  default_model: 'gemini-2.5-flash',
  auto_find_issues: true,
  export_as_pr: true,
  git_commit_authoring: 'co_authored',
  only_respond_to_mentions: true,
  open_pr_as_draft: false,
  cdp_url: 'http://127.0.0.1:9000',
  workspaces_root: '/workspaces',
  has_github_token: false,
  has_cloud_api_key: false,
  github_token_masked: null,
  cloud_api_key_masked: null,
};

const DEFAULT_CONFIG: HubConfig = {
  ollama_instances: [
    {
      id: 1,
      name: 'Local Ollama',
      url: 'http://localhost:11434',
      enabled: true,
      timeout_sec: 30,
    },
  ],
  junior_config: {
    provider: 'ollama',
    instance_id: 1,
    model_name: 'qwen2.5-coder',
    fallback_provider: 'cdp',
    fallback_instance_id: undefined,
    fallback_model: 'Gemini 2.5 Flash',
  },
  senior_config: {
    provider: 'cdp',
    instance_id: 1,
    model_name: 'Gemini 2.5 Pro',
    fallback_provider: undefined,
    fallback_instance_id: undefined,
    fallback_model: undefined,
  },
  senior_mode: 'cdp',
  cdp_host: '127.0.0.1',
  cdp_port: 9000,
  max_diff_lines: 50,
  repo_schedules: [],
  settings: DEFAULT_SETTINGS,
};

type SettingsSection = 'general' | 'integrations' | 'mcp' | 'api_key';

export const SettingsView: React.FC<SettingsViewProps> = ({ onClose, onSaveConfig }) => {
  const [activeSection, setActiveSection] = useState<SettingsSection>('general');
  const [config, setConfig] = useState<HubConfig | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);
  const [saveStatus, setSaveStatus] = useState<{ success: boolean; message: string } | null>(null);

  // Secret Inputs (write-only)
  const [githubTokenInput, setGithubTokenInput] = useState('');
  const [geminiApiKeyInput, setGeminiApiKeyInput] = useState('');
  const [openaiApiKeyInput, setOpenaiApiKeyInput] = useState('');
  const [isSavingSecrets, setIsSavingSecrets] = useState(false);
  const [secretsStatus, setSecretsStatus] = useState<{ success: boolean; message: string } | null>(null);

  // CDP models & Ollama testing
  const [cdpModels, setCdpModels] = useState<string[]>([]);
  const [testingId, setTestingId] = useState<number | null>(null);
  const [testResults, setTestResults] = useState<Record<number, OllamaProbeResult>>({});

  // Add Ollama instance form
  const [showAddForm, setShowAddForm] = useState(false);
  const [newName, setNewName] = useState('');
  const [newUrl, setNewUrl] = useState('http://localhost:11434');
  const [newTimeout, setNewTimeout] = useState(30);

  // Load config & models on mount
  useEffect(() => {
    let isMounted = true;

    async function loadData() {
      setIsLoading(true);
      try {
        const [loadedConfig, loadedCdp] = await Promise.allSettled([
          api.getConfig(),
          api.getCdpModels(),
        ]);

        if (!isMounted) return;

        if (loadedConfig.status === 'fulfilled') {
          const cfg = loadedConfig.value;
          // Ensure settings object exists
          if (!cfg.settings) {
            cfg.settings = DEFAULT_SETTINGS;
          }
          setConfig(cfg);
        } else {
          setConfig(DEFAULT_CONFIG);
        }

        if (loadedCdp.status === 'fulfilled' && loadedCdp.value.length > 0) {
          setCdpModels(loadedCdp.value);
        } else {
          setCdpModels([
            'Gemini 2.5 Flash',
            'Gemini 2.5 Pro',
            'Claude 3.7 Sonnet',
            'GPT-4o',
          ]);
        }
      } catch (e) {
        if (isMounted) setConfig(DEFAULT_CONFIG);
      } finally {
        if (isMounted) setIsLoading(false);
      }
    }

    loadData();
    return () => {
      isMounted = false;
    };
  }, []);

  // Update nested settings field
  const updateSettings = (key: keyof CommunitySettings, value: unknown) => {
    if (!config) return;
    const currentSettings = config.settings || DEFAULT_SETTINGS;
    setConfig({
      ...config,
      settings: {
        ...currentSettings,
        [key]: value,
      },
    });
  };

  // Save full configuration
  const handleSaveConfig = async () => {
    if (!config) return;
    setIsSaving(true);
    setSaveStatus(null);
    try {
      const updated = await api.updateConfig(config);
      setConfig(updated);
      setSaveStatus({ success: true, message: 'Settings saved successfully!' });
      if (onSaveConfig) {
        onSaveConfig(updated);
      }
      setTimeout(() => setSaveStatus(null), 4000);
    } catch (err: unknown) {
      const msg = err instanceof ApiError ? err.detail : 'Failed to save configuration';
      setSaveStatus({ success: false, message: msg });
    } finally {
      setIsSaving(false);
    }
  };

  // Save secrets via api.saveSecrets
  const handleSaveSecrets = async (type: 'github' | 'cloud') => {
    setIsSavingSecrets(true);
    setSecretsStatus(null);
    try {
      const req: SecretsUpdateRequest = {};
      if (type === 'github' && githubTokenInput.trim()) {
        req.github_token = githubTokenInput.trim();
      }
      if (type === 'cloud') {
        if (geminiApiKeyInput.trim()) req.gemini_api_key = geminiApiKeyInput.trim();
        if (openaiApiKeyInput.trim()) req.openai_api_key = openaiApiKeyInput.trim();
      }

      const updatedSettings = await api.saveSecrets(req);
      if (config) {
        setConfig({
          ...config,
          settings: updatedSettings,
        });
      }
      if (type === 'github') setGithubTokenInput('');
      if (type === 'cloud') {
        setGeminiApiKeyInput('');
        setOpenaiApiKeyInput('');
      }
      setSecretsStatus({ success: true, message: 'Secrets saved securely to server!' });
      setTimeout(() => setSecretsStatus(null), 4000);
    } catch (err: unknown) {
      const msg = err instanceof ApiError ? err.detail : 'Failed to save secrets';
      setSecretsStatus({ success: false, message: msg });
    } finally {
      setIsSavingSecrets(false);
    }
  };

  // Test Ollama Instance
  const handleTestOllama = useCallback(async (inst: OllamaInstance) => {
    setTestingId(inst.id);
    try {
      const res = await api.testOllamaInstance(inst);
      setTestResults((prev) => ({ ...prev, [inst.id]: res }));
    } catch (err: unknown) {
      const msg = err instanceof ApiError ? err.detail : 'Connection failed';
      setTestResults((prev) => ({
        ...prev,
        [inst.id]: {
          online_status: false,
          latency_ms: 0,
          models_list: [],
          error: msg,
        },
      }));
    } finally {
      setTestingId(null);
    }
  }, []);

  // Add Ollama instance
  const handleAddInstance = () => {
    if (!config || !newName.trim() || !newUrl.trim()) return;
    const nextId = config.ollama_instances.length > 0
      ? Math.max(...config.ollama_instances.map((i) => i.id)) + 1
      : 1;

    const newInst: OllamaInstance = {
      id: nextId,
      name: newName.trim(),
      url: newUrl.trim(),
      enabled: true,
      timeout_sec: Number(newTimeout) || 30,
    };

    setConfig({
      ...config,
      ollama_instances: [...config.ollama_instances, newInst],
    });

    setNewName('');
    setNewUrl('http://localhost:11434');
    setNewTimeout(30);
    setShowAddForm(false);
  };

  // Remove Ollama instance
  const handleRemoveInstance = (id: number) => {
    if (!config) return;
    setConfig({
      ...config,
      ollama_instances: config.ollama_instances.filter((i) => i.id !== id),
    });
  };

  if (isLoading || !config) {
    return (
      <div className="min-h-[500px] flex items-center justify-center text-zinc-400">
        <RefreshCw className="w-5 h-5 animate-spin mr-2" />
        <span className="text-sm font-medium">Loading settings...</span>
      </div>
    );
  }

  const s = config.settings || DEFAULT_SETTINGS;

  return (
    <div className="max-w-5xl mx-auto w-full px-4 py-8">
      {/* Settings Top Bar */}
      <div className="flex items-center justify-between pb-6 mb-8 border-b border-zinc-800/80">
        <div className="flex items-center gap-3">
          {onClose && (
            <button
              type="button"
              onClick={onClose}
              aria-label="Back to session"
              className="p-2 min-h-[44px] min-w-[44px] flex items-center justify-center rounded-lg text-zinc-400 hover:text-zinc-100 hover:bg-zinc-800/60 transition-colors"
            >
              <ArrowLeft className="w-5 h-5" />
            </button>
          )}
          <div>
            <h1 className="text-xl font-bold text-zinc-100 tracking-tight">
              Settings
            </h1>
            <p className="text-xs text-zinc-400">
              Configure models, GitHub credentials, integrations, and runtime providers
            </p>
          </div>
        </div>

        <button
          type="button"
          onClick={async () => {
            await handleSaveConfig();
            if (onClose) onClose();
          }}
          disabled={isSaving}
          className="inline-flex items-center gap-2 px-5 py-2.5 min-h-[44px] rounded-full bg-[#a78bfa] hover:bg-[#8b5cf6] text-zinc-950 font-semibold text-xs tracking-tight transition-all disabled:opacity-50 shadow-md"
        >
          <Save className="w-4 h-4" />
          <span>{isSaving ? 'Salvataggio...' : 'Salva e chiudi'}</span>
        </button>
      </div>

      {/* Notifications */}
      {saveStatus && (
        <div
          className={`mb-6 p-3 rounded-lg text-xs flex items-center gap-2.5 border ${
            saveStatus.success
              ? 'bg-emerald-950/40 text-emerald-300 border-emerald-800/60'
              : 'bg-rose-950/40 text-rose-300 border-rose-800/60'
          }`}
        >
          {saveStatus.success ? (
            <CheckCircle2 className="w-4 h-4 shrink-0" />
          ) : (
            <AlertCircle className="w-4 h-4 shrink-0" />
          )}
          <span>{saveStatus.message}</span>
        </div>
      )}

      {secretsStatus && (
        <div
          className={`mb-6 p-3 rounded-lg text-xs flex items-center gap-2.5 border ${
            secretsStatus.success
              ? 'bg-emerald-950/40 text-emerald-300 border-emerald-800/60'
              : 'bg-rose-950/40 text-rose-300 border-rose-800/60'
          }`}
        >
          {secretsStatus.success ? (
            <CheckCircle2 className="w-4 h-4 shrink-0" />
          ) : (
            <AlertCircle className="w-4 h-4 shrink-0" />
          )}
          <span>{secretsStatus.message}</span>
        </div>
      )}

      {/* Two-Column Layout */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-8">
        {/* Left Sub-Navigation Menu */}
        <nav className="space-y-1.5" aria-label="Settings navigation">
          <button
            type="button"
            onClick={() => setActiveSection('general')}
            className={`w-full flex items-center gap-3 px-3.5 py-3 rounded-xl text-xs font-medium min-h-[44px] transition-colors text-left ${
              activeSection === 'general'
                ? 'bg-[#2e2348] text-[#c4b5fd] font-semibold border border-[#8b5cf6]/40'
                : 'text-zinc-400 hover:text-zinc-200 hover:bg-zinc-800/50'
            }`}
          >
            <Sliders className="w-4 h-4 shrink-0" />
            <span>General</span>
          </button>

          <button
            type="button"
            onClick={() => setActiveSection('integrations')}
            className={`w-full flex items-center gap-3 px-3.5 py-3 rounded-xl text-xs font-medium min-h-[44px] transition-colors text-left ${
              activeSection === 'integrations'
                ? 'bg-[#2e2348] text-[#c4b5fd] font-semibold border border-[#8b5cf6]/40'
                : 'text-zinc-400 hover:text-zinc-200 hover:bg-zinc-800/50'
            }`}
          >
            <GitBranch className="w-4 h-4 shrink-0" />
            <span>Integrations</span>
          </button>

          <button
            type="button"
            onClick={() => setActiveSection('mcp')}
            className={`w-full flex items-center gap-3 px-3.5 py-3 rounded-xl text-xs font-medium min-h-[44px] transition-colors text-left ${
              activeSection === 'mcp'
                ? 'bg-[#2e2348] text-[#c4b5fd] font-semibold border border-[#8b5cf6]/40'
                : 'text-zinc-400 hover:text-zinc-200 hover:bg-zinc-800/50'
            }`}
          >
            <Cpu className="w-4 h-4 shrink-0" />
            <span>MCP</span>
          </button>

          <button
            type="button"
            onClick={() => setActiveSection('api_key')}
            className={`w-full flex items-center gap-3 px-3.5 py-3 rounded-xl text-xs font-medium min-h-[44px] transition-colors text-left ${
              activeSection === 'api_key'
                ? 'bg-[#2e2348] text-[#c4b5fd] font-semibold border border-[#8b5cf6]/40'
                : 'text-zinc-400 hover:text-zinc-200 hover:bg-zinc-800/50'
            }`}
          >
            <Key className="w-4 h-4 shrink-0" />
            <span>API Key</span>
          </button>
        </nav>

        {/* Right Content Panel */}
        <div className="md:col-span-3 bg-[#141419] border border-zinc-800/90 rounded-2xl p-6 shadow-xl space-y-6">
          {/* SECTION 1: GENERAL */}
          {activeSection === 'general' && (
            <div className="space-y-6">
              <div>
                <h2 className="text-base font-semibold text-zinc-100">
                  General Preferences
                </h2>
                <p className="text-xs text-zinc-400 mt-0.5">
                  Default AI models, git commit authoring, and Pull Request workflow.
                </p>
              </div>

              {/* Model settings */}
              <div className="space-y-2 pt-2">
                <label className="block text-xs font-medium text-zinc-300">
                  Default Model
                </label>
                <input
                  type="text"
                  value={s.default_model}
                  onChange={(e) => updateSettings('default_model', e.target.value)}
                  className="w-full bg-[#101014] border border-zinc-800 rounded-lg px-3 py-2 text-xs text-zinc-100 focus:outline-none focus:border-[#8b5cf6]"
                  placeholder="e.g. gemini-2.5-flash or qwen2.5-coder"
                />
              </div>

              {/* Junior & Senior Model Assignment */}
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 pt-2">
                <div className="space-y-2 p-3.5 rounded-xl bg-[#101014] border border-zinc-800/80">
                  <span className="text-xs font-semibold text-zinc-200 block">
                    Junior Persona Engine
                  </span>
                  <p className="text-[11px] text-zinc-400">
                    Runs fast local diff generation (Bolt, Palette, Sentinel).
                  </p>
                  <div className="pt-1">
                    <label className="text-[11px] text-zinc-400 block mb-1">
                      Provider & Model
                    </label>
                    <input
                      type="text"
                      value={config.junior_config.model_name}
                      onChange={(e) =>
                        setConfig({
                          ...config,
                          junior_config: { ...config.junior_config, model_name: e.target.value },
                        })
                      }
                      className="w-full bg-[#16161d] border border-zinc-800 rounded-md px-2.5 py-1.5 text-xs text-zinc-200 focus:outline-none focus:border-[#8b5cf6]"
                    />
                  </div>
                </div>

                <div className="space-y-2 p-3.5 rounded-xl bg-[#101014] border border-zinc-800/80">
                  <span className="text-xs font-semibold text-zinc-200 block">
                    Senior Reviewer Engine
                  </span>
                  <p className="text-[11px] text-zinc-400">
                    Validates diff quality and gates Pull Request creation.
                  </p>
                  <div className="pt-1">
                    <label className="text-[11px] text-zinc-400 block mb-1">
                      Model / CDP Reviewer
                    </label>
                    <input
                      type="text"
                      value={config.senior_config.model_name}
                      onChange={(e) =>
                        setConfig({
                          ...config,
                          senior_config: { ...config.senior_config, model_name: e.target.value },
                        })
                      }
                      className="w-full bg-[#16161d] border border-zinc-800 rounded-md px-2.5 py-1.5 text-xs text-zinc-200 focus:outline-none focus:border-[#8b5cf6]"
                    />
                  </div>
                </div>
              </div>

              {/* Export settings */}
              <div className="pt-4 border-t border-zinc-800/80 space-y-3">
                <h3 className="text-xs font-semibold text-zinc-200 uppercase tracking-wider">
                  Export Settings
                </h3>
                <label className="flex items-center gap-3 cursor-pointer group">
                  <input
                    type="checkbox"
                    checked={s.export_as_pr}
                    onChange={(e) => updateSettings('export_as_pr', e.target.checked)}
                    className="w-4 h-4 rounded bg-zinc-900 border-zinc-700 text-[#8b5cf6] focus:ring-[#8b5cf6] focus:ring-offset-0"
                  />
                  <div>
                    <span className="text-xs font-medium text-zinc-200 group-hover:text-white">
                      Export as pull request
                    </span>
                    <p className="text-[11px] text-zinc-400">
                      Push completed worktree branch to origin and initiate GitHub PR.
                    </p>
                  </div>
                </label>
              </div>

              {/* Git commit authoring */}
              <div className="pt-4 border-t border-zinc-800/80 space-y-2">
                <label className="block text-xs font-medium text-zinc-300">
                  Git commit authoring
                </label>
                <select
                  value={(s.git_commit_authoring as string) === 'jules_only' ? 'julius_only' : s.git_commit_authoring}
                  onChange={(e) =>
                    updateSettings('git_commit_authoring', e.target.value as GitAuthoringMode)
                  }
                  className="w-full bg-[#101014] border border-zinc-800 rounded-lg px-3 py-2 text-xs text-zinc-100 focus:outline-none focus:border-[#8b5cf6]"
                >
                  <option value="co_authored">Co-authored (Julius + User)</option>
                  <option value="julius_only">Julius only</option>
                  <option value="user_only">User only</option>
                </select>
                <p className="text-[11px] text-zinc-400">
                  Controls the `Co-authored-by:` metadata attached to automated commits.
                </p>
              </div>

              {/* Pull Request settings */}
              <div className="pt-4 border-t border-zinc-800/80 space-y-3">
                <h3 className="text-xs font-semibold text-zinc-200 uppercase tracking-wider">
                  Pull Request Settings
                </h3>

                <label className="flex items-center gap-3 cursor-pointer group">
                  <input
                    type="checkbox"
                    checked={s.only_respond_to_mentions}
                    onChange={(e) =>
                      updateSettings('only_respond_to_mentions', e.target.checked)
                    }
                    className="w-4 h-4 rounded bg-zinc-900 border-zinc-700 text-[#8b5cf6] focus:ring-[#8b5cf6] focus:ring-offset-0"
                  />
                  <div>
                    <span className="text-xs font-medium text-zinc-200 group-hover:text-white">
                      Only respond to comments that mention @julius
                    </span>
                    <p className="text-[11px] text-zinc-400">
                      Ignores general PR commentary unless explicitly addressed to Julius bot.
                    </p>
                  </div>
                </label>

                <label className="flex items-center gap-3 cursor-pointer group">
                  <input
                    type="checkbox"
                    checked={s.open_pr_as_draft}
                    onChange={(e) =>
                      updateSettings('open_pr_as_draft', e.target.checked)
                    }
                    className="w-4 h-4 rounded bg-zinc-900 border-zinc-700 text-[#8b5cf6] focus:ring-[#8b5cf6] focus:ring-offset-0"
                  />
                  <div>
                    <span className="text-xs font-medium text-zinc-200 group-hover:text-white">
                      Open pull requests as drafts by default
                    </span>
                    <p className="text-[11px] text-zinc-400">
                      Created PRs will require manual marking as ready for review before merge.
                    </p>
                  </div>
                </label>
              </div>
            </div>
          )}

          {/* SECTION 2: INTEGRATIONS */}
          {activeSection === 'integrations' && (
            <div className="space-y-6">
              <div>
                <h2 className="text-base font-semibold text-zinc-100">
                  Integrations
                </h2>
                <p className="text-xs text-zinc-400 mt-0.5">
                  Configure GitHub Personal Access Token and workspace directories.
                </p>
              </div>

              {/* GitHub Token Config */}
              <div className="p-4 rounded-xl bg-[#101014] border border-zinc-800/80 space-y-3">
                <div className="flex items-center justify-between">
                  <label className="text-xs font-semibold text-zinc-200 flex items-center gap-2">
                    <Lock className="w-3.5 h-3.5 text-zinc-400" />
                    <span>GitHub Personal Access Token</span>
                  </label>
                  {s.has_github_token ? (
                    <span className="inline-flex items-center gap-1.5 px-2 py-0.5 rounded-full text-[11px] font-medium bg-emerald-950/60 text-emerald-300 border border-emerald-800/60">
                      <CheckCircle2 className="w-3 h-3 text-emerald-400" />
                      Configured ({s.github_token_masked || '••••••••'})
                    </span>
                  ) : (
                    <span className="text-[11px] text-zinc-400">
                      Not configured (falling back to local gh CLI / env)
                    </span>
                  )}
                </div>

                <div className="flex items-center gap-2">
                  <input
                    type="password"
                    value={githubTokenInput}
                    onChange={(e) => setGithubTokenInput(e.target.value)}
                    placeholder="Enter new GitHub token (ghp_...)"
                    className="flex-1 bg-[#16161d] border border-zinc-800 rounded-lg px-3 py-2 text-xs text-zinc-100 placeholder-zinc-400 focus:outline-none focus:border-[#8b5cf6]"
                  />
                  <button
                    type="button"
                    onClick={() => handleSaveSecrets('github')}
                    disabled={isSavingSecrets || !githubTokenInput.trim()}
                    className="px-4 py-2 min-h-[44px] rounded-lg bg-zinc-800 hover:bg-zinc-700 text-zinc-100 text-xs font-medium transition-colors disabled:opacity-50"
                  >
                    Save Token
                  </button>
                </div>
                <p className="text-[11px] text-zinc-400">
                  Required for automated `gh pr create` and branch pushing when running outside a configured local git terminal.
                </p>
              </div>

              {/* Workspaces Root Directory */}
              <div className="space-y-2 pt-2">
                <label className="block text-xs font-medium text-zinc-300">
                  Workspaces Root Directory
                </label>
                <input
                  type="text"
                  value={s.workspaces_root}
                  onChange={(e) => updateSettings('workspaces_root', e.target.value)}
                  className="w-full bg-[#101014] border border-zinc-800 rounded-lg px-3 py-2 text-xs text-zinc-100 focus:outline-none focus:border-[#8b5cf6]"
                  placeholder="/workspaces or path to git repositories"
                />
                <p className="text-[11px] text-zinc-400">
                  Directory where Julius Hub searches for local git projects to curate.
                </p>
              </div>
            </div>
          )}

          {/* SECTION 3: MCP */}
          {activeSection === 'mcp' && (
            <div className="space-y-6">
              <div>
                <h2 className="text-base font-semibold text-zinc-100">
                  MCP & Chrome DevTools Protocol
                </h2>
                <p className="text-xs text-zinc-400 mt-0.5">
                  Configure browser debugging bridge and Antigravity CDP connector.
                </p>
              </div>

              {/* CDP Bridge URL */}
              <div className="p-4 rounded-xl bg-[#101014] border border-zinc-800/80 space-y-3">
                <label className="block text-xs font-semibold text-zinc-200">
                  CDP Bridge URL
                </label>
                <input
                  type="text"
                  value={s.cdp_url}
                  onChange={(e) => updateSettings('cdp_url', e.target.value)}
                  className="w-full bg-[#16161d] border border-zinc-800 rounded-lg px-3 py-2 text-xs text-zinc-100 focus:outline-none focus:border-[#8b5cf6]"
                  placeholder="http://127.0.0.1:9000"
                />
                <p className="text-[11px] text-zinc-400">
                  Port where Antigravity Desktop exposes the CDP remote debugging websocket.
                </p>
              </div>

              {/* Available CDP Models */}
              <div className="space-y-2">
                <label className="block text-xs font-medium text-zinc-300">
                  Discovered CDP Senior Models
                </label>
                <div className="flex flex-wrap gap-2">
                  {cdpModels.map((m) => (
                    <span
                      key={m}
                      className="px-2.5 py-1 rounded-md text-xs bg-[#101014] border border-zinc-800 text-zinc-300 font-mono"
                    >
                      {m}
                    </span>
                  ))}
                </div>
              </div>
            </div>
          )}

          {/* SECTION 4: API KEY */}
          {activeSection === 'api_key' && (
            <div className="space-y-6">
              <div>
                <h2 className="text-base font-semibold text-zinc-100">
                  API Keys & Inference Clusters
                </h2>
                <p className="text-xs text-zinc-400 mt-0.5">
                  Manage Cloud LLM keys and local Ollama cluster instances.
                </p>
              </div>

              {/* Gemini / OpenAI Cloud Keys */}
              <div className="p-4 rounded-xl bg-[#101014] border border-zinc-800/80 space-y-4">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-semibold text-zinc-200">
                    Cloud LLM API Keys
                  </span>
                  {s.has_cloud_api_key ? (
                    <span className="inline-flex items-center gap-1.5 px-2 py-0.5 rounded-full text-[11px] font-medium bg-emerald-950/60 text-emerald-300 border border-emerald-800/60">
                      <CheckCircle2 className="w-3 h-3 text-emerald-400" />
                      Cloud Key Configured ({s.cloud_api_key_masked || '••••••••'})
                    </span>
                  ) : (
                    <span className="text-[11px] text-zinc-400">
                      Not configured (Ollama fallback active)
                    </span>
                  )}
                </div>

                <div className="space-y-2">
                  <label className="text-[11px] text-zinc-400 block">
                    Gemini API Key
                  </label>
                  <input
                    type="password"
                    value={geminiApiKeyInput}
                    onChange={(e) => setGeminiApiKeyInput(e.target.value)}
                    placeholder="Enter new Gemini API Key"
                    className="w-full bg-[#16161d] border border-zinc-800 rounded-lg px-3 py-2 text-xs text-zinc-100 placeholder-zinc-400 focus:outline-none focus:border-[#8b5cf6]"
                  />
                </div>

                <div className="space-y-2">
                  <label className="text-[11px] text-zinc-400 block">
                    OpenAI / Compatible API Key
                  </label>
                  <input
                    type="password"
                    value={openaiApiKeyInput}
                    onChange={(e) => setOpenaiApiKeyInput(e.target.value)}
                    placeholder="Enter new OpenAI Compatible API Key"
                    className="w-full bg-[#16161d] border border-zinc-800 rounded-lg px-3 py-2 text-xs text-zinc-100 placeholder-zinc-400 focus:outline-none focus:border-[#8b5cf6]"
                  />
                </div>

                <div className="flex justify-end pt-2">
                  <button
                    type="button"
                    onClick={() => handleSaveSecrets('cloud')}
                    disabled={isSavingSecrets || (!geminiApiKeyInput.trim() && !openaiApiKeyInput.trim())}
                    className="px-4 py-2 min-h-[44px] rounded-lg bg-zinc-800 hover:bg-zinc-700 text-zinc-100 text-xs font-medium transition-colors disabled:opacity-50"
                  >
                    Save Cloud Keys
                  </button>
                </div>
              </div>

              {/* Ollama Instances Cluster */}
              <div className="space-y-3 pt-2">
                <div className="flex items-center justify-between">
                  <div>
                    <h3 className="text-xs font-semibold text-zinc-200 uppercase tracking-wider">
                      Ollama Cluster Instances
                    </h3>
                    <p className="text-[11px] text-zinc-400">
                      Multi-instance load balancer for local code intelligence.
                    </p>
                  </div>

                  <button
                    type="button"
                    onClick={() => setShowAddForm(!showAddForm)}
                    className="inline-flex items-center gap-1.5 px-3 py-1.5 min-h-[36px] rounded-lg bg-zinc-800 hover:bg-zinc-700 text-zinc-200 text-xs font-medium transition-colors"
                  >
                    <Plus className="w-3.5 h-3.5" />
                    <span>Add Instance</span>
                  </button>
                </div>

                {/* Add Instance Form */}
                {showAddForm && (
                  <div className="p-4 rounded-xl bg-[#101014] border border-zinc-800/80 space-y-3">
                    <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
                      <div>
                        <label className="text-[11px] text-zinc-400 block mb-1">
                          Instance Name
                        </label>
                        <input
                          type="text"
                          value={newName}
                          onChange={(e) => setNewName(e.target.value)}
                          placeholder="e.g. Local Ollama"
                          className="w-full bg-[#16161d] border border-zinc-800 rounded-md px-2.5 py-1.5 text-xs text-zinc-100"
                        />
                      </div>
                      <div>
                        <label className="text-[11px] text-zinc-400 block mb-1">
                          Server URL
                        </label>
                        <input
                          type="text"
                          value={newUrl}
                          onChange={(e) => setNewUrl(e.target.value)}
                          placeholder="http://localhost:11434"
                          className="w-full bg-[#16161d] border border-zinc-800 rounded-md px-2.5 py-1.5 text-xs text-zinc-100"
                        />
                      </div>
                      <div>
                        <label className="text-[11px] text-zinc-400 block mb-1">
                          Timeout (seconds)
                        </label>
                        <input
                          type="number"
                          value={newTimeout}
                          onChange={(e) => setNewTimeout(Number(e.target.value) || 30)}
                          className="w-full bg-[#16161d] border border-zinc-800 rounded-md px-2.5 py-1.5 text-xs text-zinc-100"
                        />
                      </div>
                    </div>
                    <div className="flex justify-end gap-2 pt-1">
                      <button
                        type="button"
                        onClick={() => setShowAddForm(false)}
                        className="px-3 py-1.5 text-xs text-zinc-400 hover:text-zinc-200"
                      >
                        Cancel
                      </button>
                      <button
                        type="button"
                        onClick={handleAddInstance}
                        className="px-3 py-1.5 rounded bg-[#8b5cf6] text-white text-xs font-medium hover:bg-[#7c3aed]"
                      >
                        Confirm Add
                      </button>
                    </div>
                  </div>
                )}

                {/* Instance List */}
                <div className="space-y-2">
                  {config.ollama_instances.map((inst) => {
                    const probe = testResults[inst.id];
                    const isTesting = testingId === inst.id;

                    return (
                      <div
                        key={inst.id}
                        className="flex items-center justify-between p-3.5 rounded-xl bg-[#101014] border border-zinc-800/80 gap-3"
                      >
                        <div className="min-w-0 flex-1">
                          <div className="flex items-center gap-2">
                            <span className="text-xs font-semibold text-zinc-200">
                              {inst.name}
                            </span>
                            <span className="text-[11px] font-mono text-zinc-400 truncate">
                              {inst.url}
                            </span>
                          </div>
                          {probe && (
                            <p
                              className={`text-[11px] mt-1 ${
                                probe.online_status
                                  ? 'text-emerald-400'
                                  : 'text-rose-400'
                              }`}
                            >
                              {probe.online_status
                                ? `Online (${probe.latency_ms.toFixed(0)}ms) • ${
                                    probe.models_list.length
                                  } models available`
                                : `Offline: ${probe.error || 'Connection failed'}`}
                            </p>
                          )}
                        </div>

                        <div className="flex items-center gap-2 shrink-0">
                          <button
                            type="button"
                            onClick={() => handleTestOllama(inst)}
                            disabled={isTesting}
                            className="px-3 py-1.5 min-h-[36px] rounded-lg bg-zinc-800 hover:bg-zinc-700 text-zinc-200 text-xs font-medium transition-colors disabled:opacity-50"
                          >
                            {isTesting ? 'Testing...' : 'Test'}
                          </button>
                          <button
                            type="button"
                            onClick={() => handleRemoveInstance(inst.id)}
                            aria-label={`Remove instance ${inst.name}`}
                            className="p-2 min-h-[44px] min-w-[44px] flex items-center justify-center rounded-lg text-zinc-400 hover:text-rose-400 hover:bg-zinc-800 transition-colors"
                          >
                            <Trash2 className="w-4 h-4" />
                          </button>
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
