import React, { useState, useEffect, useCallback } from 'react';
import {
  ArrowRight,
  ChevronDown,
  FolderGit2,
  PanelLeft,
  RefreshCw,
  Settings,
  Sliders,
  Sparkles,
} from 'lucide-react';
import { api, ApiError } from './api';
import type {
  EngineMode,
  HealthResponse,
  HubConfig,
  ProjectInfo,
  SessionRecord,
  Suggestion,
  TaskStatus,
  ToastMessage,
  WorktreeSessionInfo,
} from './types';
import { Sidebar } from './components/Sidebar';
import {
  SuggestionCard,
  SuggestionEmptyState,
  SuggestionSkeleton,
} from './components/SuggestionCard';
import { DiffDrawer } from './components/DiffDrawer';
import { WorktreeList } from './components/WorktreeList';
import { ToastContainer } from './components/Toast';
import { SettingsView } from './components/SettingsView';
import { SchedulerPanel } from './components/SchedulerPanel';

type MainView = 'session' | 'settings';
type CardTab = 'overview' | 'suggested' | 'scheduled';

const CATEGORY_TABS = [
  { id: 'all', label: 'All' },
  { id: 'cleanup', label: 'Cleanup' },
  { id: 'performance', label: 'Performance' },
  { id: 'security', label: 'Security' },
  { id: 'code_health', label: 'Code Health' },
  { id: 'testing', label: 'Testing' },
] as const;

export const App: React.FC = () => {
  // Main view router: 'session' | 'settings'
  const [view, setView] = useState<MainView>('session');

  // Sidebar toggle state (collapsible on desktop, off-canvas on mobile)
  const [sidebarOpen, setSidebarOpen] = useState<boolean>(true);

  // Global Hub Data
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [projects, setProjects] = useState<ProjectInfo[]>([]);
  const [config, setConfig] = useState<HubConfig | null>(null);
  const [sessions, setSessions] = useState<SessionRecord[]>([]);
  const [selectedRepo, setSelectedRepo] = useState<string>('jules');
  const [selectedEngine, setSelectedEngine] = useState<EngineMode>('antigravity_flash');

  // Central Card State
  const [promptInput, setPromptInput] = useState<string>('');
  const [isPromptRunning, setIsPromptRunning] = useState<boolean>(false);
  const [activeCardTab, setActiveCardTab] = useState<CardTab>('overview');
  const [selectedCategory, setSelectedCategory] = useState<string>('all');
  const [repoDropdownOpen, setRepoDropdownOpen] = useState<boolean>(false);

  // Suggestions & Worktrees
  const [suggestions, setSuggestions] = useState<Suggestion[]>([]);
  const [isLoadingSuggestions, setIsLoadingSuggestions] = useState<boolean>(true);
  const [worktrees, setWorktrees] = useState<WorktreeSessionInfo[]>([]);
  const [isLoadingWorktrees, setIsLoadingWorktrees] = useState<boolean>(false);

  // Active Task & Diff Drawer
  const [activeTaskId, setActiveTaskId] = useState<string | null>(null);
  const [activeTaskStatus, setActiveTaskStatus] = useState<TaskStatus>('pending');
  const [activeTaskDiff, setActiveTaskDiff] = useState<string | null>(null);
  const [activeTaskBranch, setActiveTaskBranch] = useState<string>('');
  const [activeTaskWorktreePath, setActiveTaskWorktreePath] = useState<string | null>(null);
  const [activeTaskPrUrl, setActiveTaskPrUrl] = useState<string | null>(null);
  const [isDiffDrawerOpen, setIsDiffDrawerOpen] = useState<boolean>(false);
  const [executingSuggestionId, setExecutingSuggestionId] = useState<string | null>(null);
  const [isEscalating, setIsEscalating] = useState<boolean>(false);

  // Toasts
  const [toasts, setToasts] = useState<ToastMessage[]>([]);

  const addToast = useCallback(
    (type: ToastMessage['type'], title: string, message: string) => {
      const id = `${Date.now()}_${Math.random().toString(36).substring(2, 7)}`;
      setToasts((prev) => [...prev, { id, type, title, message }]);
      setTimeout(() => {
        setToasts((prev) => prev.filter((t) => t.id !== id));
      }, 5000);
    },
    []
  );

  const removeToast = useCallback((id: string) => {
    setToasts((prev) => prev.filter((t) => t.id !== id));
  }, []);

  // Fetch Sessions
  const fetchSessions = useCallback(async () => {
    try {
      const data = await api.getSessions(selectedRepo || undefined);
      setSessions(data);
    } catch {
      // Sessions endpoint optional if backend state starts empty
    }
  }, [selectedRepo]);

  // Initial Load: Health, Projects, Config, Sessions
  useEffect(() => {
    const fetchInitialData = async () => {
      try {
        const [h, p, c] = await Promise.allSettled([
          api.getHealth(),
          api.getProjects(),
          api.getConfig(),
        ]);

        if (h.status === 'fulfilled') setHealth(h.value);
        if (c.status === 'fulfilled') setConfig(c.value);
        if (p.status === 'fulfilled' && p.value.length > 0) {
          setProjects(p.value);
          const preferred =
            p.value.find((pr) => pr.name === 'julius-hub') ??
            p.value.find((pr) => pr.name === 'jules') ??
            p.value[0];
          if (preferred) setSelectedRepo(preferred.name);
        }
      } catch (err) {
        console.error('Initial data load error', err);
      }
    };

    fetchInitialData();
  }, []);

  // Fetch Suggestions
  const fetchSuggestions = useCallback(async () => {
    setIsLoadingSuggestions(true);
    try {
      const data = await api.getSuggestions(
        selectedRepo || undefined,
        'all',
        selectedCategory !== 'all' ? selectedCategory : undefined
      );
      setSuggestions(data);
    } catch (err: unknown) {
      console.error('Error fetching suggestions', err);
      setSuggestions([]);
    } finally {
      setIsLoadingSuggestions(false);
    }
  }, [selectedRepo, selectedCategory]);

  // Fetch Worktrees
  const fetchWorktrees = useCallback(async () => {
    setIsLoadingWorktrees(true);
    try {
      const data = await api.getWorktrees();
      setWorktrees(data);
    } catch (err) {
      console.error('Error fetching worktrees', err);
    } finally {
      setIsLoadingWorktrees(false);
    }
  }, []);

  // Reload data on repo or category change
  useEffect(() => {
    fetchSuggestions();
    fetchWorktrees();
    fetchSessions();
  }, [fetchSuggestions, fetchWorktrees, fetchSessions]);

  // Discard suggestion
  const handleDiscardSuggestion = async (suggestionId: string) => {
    try {
      await api.discardSuggestion(suggestionId);
      setSuggestions((prev) => prev.filter((s) => s.id !== suggestionId));
      addToast('info', 'Suggestion Discarded', 'Item ignored and will not appear in future scans.');
    } catch {
      setSuggestions((prev) => prev.filter((s) => s.id !== suggestionId));
      addToast('info', 'Suggestion Discarded', 'Removed locally.');
    }
  };

  // Run Prompt Action
  const handleRunPrompt = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!promptInput.trim() || isPromptRunning) return;
    const text = promptInput.trim();
    setIsPromptRunning(true);
    try {
      addToast('info', 'Task Launched', `Executing prompt in worktree for ${selectedRepo}...`);
      const resp = await api.runTask({
        repo: selectedRepo,
        persona: 'bolt',
        prompt: text,
        mode: selectedEngine,
        dry_run: false,
      });

      setActiveTaskId(resp.task_id);
      setActiveTaskStatus(resp.status);
      setActiveTaskWorktreePath(resp.worktree_path || null);
      setActiveTaskBranch(resp.branch || `curator/prompt-${resp.task_id.substring(0, 6)}`);
      setActiveTaskDiff(resp.diff || null);
      setActiveTaskPrUrl(null);
      setIsDiffDrawerOpen(true);
      setPromptInput('');

      fetchSessions();
      fetchWorktrees();
    } catch (err: unknown) {
      const msg = err instanceof ApiError ? err.detail : 'Execution failed';
      addToast('error', 'Execution Error', msg);
    } finally {
      setIsPromptRunning(false);
    }
  };

  // Run Suggestion in Julius
  const handleRunInJulius = async (suggestion: Suggestion) => {
    setExecutingSuggestionId(suggestion.id);
    try {
      addToast('info', 'Task Launched', `Creating worktree for ${suggestion.title}...`);
      const resp = await api.runTask({
        repo: selectedRepo,
        persona: suggestion.persona,
        target_file: suggestion.file,
        issue_context: `${suggestion.title}: ${suggestion.issue}`,
        mode: selectedEngine,
        dry_run: false,
      });

      setActiveTaskId(resp.task_id);
      setActiveTaskStatus(resp.status);
      setActiveTaskWorktreePath(resp.worktree_path || null);
      setActiveTaskBranch(resp.branch || `curator/${suggestion.persona}-${resp.task_id.substring(0, 6)}`);
      setActiveTaskDiff(resp.diff || null);
      setActiveTaskPrUrl(null);
      setIsDiffDrawerOpen(true);

      fetchSessions();
      fetchWorktrees();
    } catch (err: unknown) {
      const msg = err instanceof ApiError ? err.detail : 'Execution failed';
      addToast('error', 'Execution Error', msg);
    } finally {
      setExecutingSuggestionId(null);
    }
  };

  // Select session from Sidebar
  const handleSelectSession = (session: SessionRecord) => {
    setActiveTaskId(session.task_id);
    setActiveTaskStatus(session.status);
    setActiveTaskWorktreePath(session.worktree_path || null);
    setActiveTaskBranch(session.branch || '');
    setActiveTaskDiff(session.diff || null);
    setActiveTaskPrUrl(session.pr_url || null);
    if (session.repo && session.repo !== selectedRepo) {
      setSelectedRepo(session.repo);
    }
    setView('session');
    setIsDiffDrawerOpen(true);
  };

  // Escalate to Antigravity
  const handleEscalate = async () => {
    setIsEscalating(true);
    try {
      const repoName = selectedRepo || 'jules';
      const branch = activeTaskBranch || `curator/audit-${Date.now().toString().slice(-4)}`;
      const worktreePath = activeTaskWorktreePath || '';

      const res = await api.escalateToAntigravity({
        repo: repoName,
        worktree_path: worktreePath,
        branch: branch,
        diff_summary: 'Senior Audit Request',
        test_status: activeTaskStatus === 'passed' ? 'PASSED' : 'NEEDS_ESCALATION',
        instruction: 'Esegui audit Senior. Se approvato, apri la PR su GitHub.',
      });

      if (res.success) {
        addToast('success', 'Escalation Sent', res.message || 'Task sent to Antigravity Senior Review!');
      } else {
        addToast('error', 'CDP Offline', res.message || 'Antigravity CDP on port 9000 is not reachable.');
      }
    } catch {
      addToast('error', 'CDP Error', 'Could not connect to Antigravity CDP port 9000.');
    } finally {
      setIsEscalating(false);
    }
  };

  // Toggle Auto Find Issues
  const handleToggleAutoFind = async () => {
    if (!config || !config.settings) return;
    const updated = {
      ...config,
      settings: {
        ...config.settings,
        auto_find_issues: !config.settings.auto_find_issues,
      },
    };
    setConfig(updated);
    try {
      await api.updateConfig(updated);
    } catch {
      // Revert if failed
    }
  };

  return (
    <div className="min-h-screen bg-[#0a0a0c] text-zinc-100 flex flex-col font-sans selection:bg-[#8b5cf6]/30">
      {/* Official Julius Header */}
      <header className="h-14 border-b border-zinc-800/80 bg-[#0a0a0c] px-4 flex items-center justify-between sticky top-0 z-20">
        {/* Left: Sidebar toggle + Logo */}
        <div className="flex items-center gap-3">
          <button
            type="button"
            onClick={() => setSidebarOpen(!sidebarOpen)}
            aria-label="Toggle sidebar"
            className="p-2 min-h-[44px] min-w-[44px] flex items-center justify-center rounded-lg text-zinc-400 hover:text-zinc-100 hover:bg-zinc-800/60 transition-colors"
          >
            <PanelLeft className="w-5 h-5" />
          </button>

          <div
            onClick={() => setView('session')}
            className="flex items-center gap-2 cursor-pointer select-none group"
          >
            {/* Clean logo glyph */}
            <div className="w-7 h-7 rounded-lg bg-[#2e2348] border border-[#8b5cf6]/40 flex items-center justify-center text-[#c4b5fd]">
              <Sparkles className="w-4 h-4 text-[#a78bfa]" />
            </div>
            <span className="font-semibold text-base text-zinc-100 tracking-tight group-hover:text-white">
              julius
            </span>
          </div>
        </div>

        {/* Right: Engine selector pill + Community status + Settings button */}
        <div className="flex items-center gap-3">
          {/* Model Engine Selector Pill */}
          <div className="relative">
            <select
              value={selectedEngine}
              onChange={(e) => setSelectedEngine(e.target.value as EngineMode)}
              className="appearance-none bg-[#241b35] text-[#c4b5fd] border border-[#4c1d95]/60 pl-3 pr-7 py-1.5 rounded-full text-xs font-medium focus:outline-none focus:border-[#8b5cf6] cursor-pointer"
            >
              <option value="antigravity_flash" className="bg-[#141419] text-zinc-200">
                Gemini 2.5 Flash
              </option>
              <option value="hybrid" className="bg-[#141419] text-zinc-200">
                Hybrid (Local + Cloud)
              </option>
              <option value="local" className="bg-[#141419] text-zinc-200">
                Local Ollama
              </option>
            </select>
            <ChevronDown className="w-3 h-3 text-[#c4b5fd] absolute right-2.5 top-1/2 -translate-y-1/2 pointer-events-none" />
          </div>

          {/* Backend Status indicator */}
          <div
            className="hidden sm:flex items-center gap-1.5 px-2.5 py-1 rounded-full text-[11px] bg-[#16161d] border border-zinc-800 text-zinc-400"
            title={health ? 'Backend online on port 4100' : 'Backend offline'}
          >
            <span
              className={`w-2 h-2 rounded-full ${
                health ? 'bg-emerald-400' : 'bg-rose-400'
              }`}
            />
            <span className="font-mono text-zinc-300">COMMUNITY</span>
          </div>

          {/* Settings button */}
          <button
            type="button"
            onClick={() => setView(view === 'settings' ? 'session' : 'settings')}
            aria-label="Open settings"
            className={`p-2 min-h-[44px] min-w-[44px] flex items-center justify-center rounded-lg transition-colors ${
              view === 'settings'
                ? 'bg-[#2e2348] text-[#c4b5fd]'
                : 'text-zinc-400 hover:text-zinc-100 hover:bg-zinc-800/60'
            }`}
          >
            <Settings className="w-5 h-5" />
          </button>
        </div>
      </header>

      {/* Main Container with Sidebar + Content */}
      <div className="flex-1 flex overflow-hidden">
        {/* Left Sidebar */}
        <Sidebar
          isOpen={sidebarOpen}
          onClose={() => setSidebarOpen(false)}
          sessions={sessions}
          projects={projects}
          selectedRepo={selectedRepo}
          onSelectRepo={(r) => {
            setSelectedRepo(r);
            setView('session');
          }}
          onSelectSession={handleSelectSession}
          activeTaskId={activeTaskId}
        />

        {/* Center Canvas */}
        <main className="flex-1 overflow-y-auto">
          {view === 'settings' ? (
            <SettingsView
              onClose={() => setView('session')}
              onSaveConfig={(cfg) => setConfig(cfg)}
            />
          ) : (
            <div className="max-w-3xl w-full mx-auto px-4 py-8 space-y-4">
              {/* Top Bar Above Central Card: Repo Dropdown & Configure repo */}
              <div className="flex items-center justify-between">
                {/* Repo Dropdown */}
                <div className="relative">
                  <button
                    type="button"
                    onClick={() => setRepoDropdownOpen(!repoDropdownOpen)}
                    className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-[#141419] border border-zinc-800/90 text-zinc-100 text-xs font-medium hover:border-zinc-700 transition-colors min-h-[36px]"
                    aria-expanded={repoDropdownOpen}
                  >
                    <FolderGit2 className="w-4 h-4 text-zinc-400" />
                    <span>{selectedRepo}</span>
                    <ChevronDown className="w-3.5 h-3.5 text-zinc-400" />
                  </button>

                  {repoDropdownOpen && (
                    <div className="absolute left-0 top-full mt-1.5 w-56 bg-[#16161d] border border-zinc-800 rounded-xl shadow-2xl py-1 z-30">
                      {projects.map((p) => (
                        <button
                          key={p.name}
                          type="button"
                          onClick={() => {
                            setSelectedRepo(p.name);
                            setRepoDropdownOpen(false);
                          }}
                          className={`w-full text-left px-3 py-2 text-xs flex items-center justify-between hover:bg-zinc-800/60 transition-colors ${
                            selectedRepo === p.name
                              ? 'text-[#a78bfa] font-medium'
                              : 'text-zinc-300'
                          }`}
                        >
                          <span className="truncate">{p.name}</span>
                          {selectedRepo === p.name && (
                            <span className="w-1.5 h-1.5 rounded-full bg-[#8b5cf6]" />
                          )}
                        </button>
                      ))}
                    </div>
                  )}
                </div>

                {/* Configure Repo button */}
                <button
                  type="button"
                  onClick={() => setView('settings')}
                  className="text-xs text-zinc-400 hover:text-zinc-200 flex items-center gap-1.5 transition-colors p-2 min-h-[44px]"
                >
                  <Sliders className="w-3.5 h-3.5 text-zinc-400" />
                  <span>Configure repo</span>
                </button>
              </div>

              {/* Central Minimalist Card */}
              <div className="bg-[#141419] border border-zinc-800/90 rounded-2xl p-4 shadow-xl space-y-4">
                {/* 1. Free-form Prompt Input Box */}
                <form onSubmit={handleRunPrompt} className="relative">
                  <textarea
                    rows={2}
                    value={promptInput}
                    onChange={(e) => setPromptInput(e.target.value)}
                    onKeyDown={(e) => {
                      if (e.key === 'Enter' && !e.shiftKey) {
                        e.preventDefault();
                        handleRunPrompt(e);
                      }
                    }}
                    placeholder="Help me fix this error ... or Write a test that mocks fetch ..."
                    className="w-full bg-[#101014] border border-zinc-800/90 rounded-xl px-4 py-3 pr-14 text-sm text-zinc-100 placeholder-zinc-400 focus:outline-none focus:border-[#8b5cf6] transition-colors resize-none leading-relaxed"
                  />
                  <button
                    type="submit"
                    disabled={!promptInput.trim() || isPromptRunning}
                    aria-label="Run prompt"
                    className="absolute right-3 top-1/2 -translate-y-1/2 w-8 h-8 rounded-lg bg-[#8b5cf6] hover:bg-[#7c3aed] text-white flex items-center justify-center transition-colors disabled:opacity-40 disabled:hover:bg-[#8b5cf6]"
                  >
                    {isPromptRunning ? (
                      <RefreshCw className="w-4 h-4 animate-spin text-white" />
                    ) : (
                      <ArrowRight className="w-4 h-4 text-white" />
                    )}
                  </button>
                </form>

                {/* 2. 3 Tab Pills */}
                <div
                  role="tablist"
                  className="flex items-center gap-1 p-1 bg-[#101014] rounded-xl border border-zinc-800/80"
                >
                  <button
                    type="button"
                    role="tab"
                    aria-selected={activeCardTab === 'overview'}
                    onClick={() => setActiveCardTab('overview')}
                    className={`flex-1 py-1.5 px-3 rounded-lg text-xs font-medium transition-colors text-center ${
                      activeCardTab === 'overview'
                        ? 'bg-zinc-800 text-zinc-100 shadow-xs'
                        : 'text-zinc-400 hover:text-zinc-200'
                    }`}
                  >
                    Codebase overview
                  </button>

                  <button
                    type="button"
                    role="tab"
                    aria-selected={activeCardTab === 'suggested'}
                    onClick={() => setActiveCardTab('suggested')}
                    className={`flex-1 py-1.5 px-3 rounded-lg text-xs font-medium transition-colors text-center ${
                      activeCardTab === 'suggested'
                        ? 'bg-zinc-800 text-zinc-100 shadow-xs'
                        : 'text-zinc-400 hover:text-zinc-200'
                    }`}
                  >
                    Suggested
                  </button>

                  <button
                    type="button"
                    role="tab"
                    aria-selected={activeCardTab === 'scheduled'}
                    onClick={() => setActiveCardTab('scheduled')}
                    className={`flex-1 py-1.5 px-3 rounded-lg text-xs font-medium transition-colors text-center ${
                      activeCardTab === 'scheduled'
                        ? 'bg-zinc-800 text-zinc-100 shadow-xs'
                        : 'text-zinc-400 hover:text-zinc-200'
                    }`}
                  >
                    Scheduled
                  </button>
                </div>

                {/* TAB CONTENT */}

                {/* Tab 1: Codebase overview */}
                {activeCardTab === 'overview' && (
                  <div className="space-y-4 pt-1">
                    {/* Toggle: Automatically find issues */}
                    <div className="flex items-center justify-between p-3.5 rounded-xl bg-[#101014] border border-zinc-800/80">
                      <div>
                        <span className="text-xs font-semibold text-zinc-200 block">
                          Automatically find issues in your codebase
                        </span>
                        <p className="text-[11px] text-zinc-400 mt-0.5">
                          Runs lightweight background scanners to detect micro-optimizations.
                        </p>
                      </div>

                      <label className="relative inline-flex items-center cursor-pointer min-h-[44px]">
                        <input
                          type="checkbox"
                          checked={config?.settings?.auto_find_issues ?? true}
                          onChange={handleToggleAutoFind}
                          className="sr-only peer"
                        />
                        <div className="w-10 h-5 bg-zinc-800 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[14px] after:left-[2px] after:bg-white after:rounded-full after:h-4 after:w-4 after:transition-all peer-checked:bg-[#8b5cf6]" />
                      </label>
                    </div>

                    {/* Active Worktrees if any */}
                    {worktrees.length > 0 && (
                      <div className="pt-2">
                        <WorktreeList
                          worktrees={worktrees}
                          onPrune={async (path) => {
                            await api.pruneWorktrees({ worktree_path: path, force: true });
                            fetchWorktrees();
                          }}
                          onRefresh={fetchWorktrees}
                          isLoading={isLoadingWorktrees}
                        />
                      </div>
                    )}
                  </div>
                )}

                {/* Tab 2: Suggested */}
                {activeCardTab === 'suggested' && (
                  <div className="space-y-3 pt-1">
                    {/* Filter Pills Bar */}
                    <div className="flex items-center justify-between gap-2 overflow-x-auto pb-1">
                      <div className="flex items-center gap-1.5 flex-wrap">
                        {CATEGORY_TABS.map((tab) => {
                          const isSelected = selectedCategory === tab.id;
                          return (
                            <button
                              key={tab.id}
                              type="button"
                              onClick={() => setSelectedCategory(tab.id)}
                              className={`px-3 py-1 rounded-full text-xs font-medium transition-colors ${
                                isSelected
                                  ? 'bg-[#2e2348] text-[#c4b5fd] border border-[#8b5cf6]/60'
                                  : 'bg-zinc-900 text-zinc-400 hover:text-zinc-200 border border-zinc-800'
                              }`}
                            >
                              {tab.label}
                            </button>
                          );
                        })}
                      </div>

                      <button
                        type="button"
                        onClick={fetchSuggestions}
                        disabled={isLoadingSuggestions}
                        aria-label="Refresh suggestions"
                        className="p-2 min-h-[36px] min-w-[36px] flex items-center justify-center rounded-lg text-zinc-400 hover:text-zinc-100 hover:bg-zinc-800/60 transition-colors shrink-0"
                      >
                        <RefreshCw
                          className={`w-3.5 h-3.5 ${
                            isLoadingSuggestions ? 'animate-spin' : ''
                          }`}
                        />
                      </button>
                    </div>

                    {/* Suggestions Compact List */}
                    <div className="divide-y divide-zinc-800/50 pt-1">
                      {isLoadingSuggestions ? (
                        <>
                          <SuggestionSkeleton />
                          <SuggestionSkeleton />
                          <SuggestionSkeleton />
                        </>
                      ) : suggestions.length === 0 ? (
                        <SuggestionEmptyState
                          repoName={selectedRepo}
                          onRefresh={fetchSuggestions}
                        />
                      ) : (
                        suggestions.map((suggestion) => (
                          <SuggestionCard
                            key={suggestion.id}
                            suggestion={suggestion}
                            onRunInJulius={handleRunInJulius}
                            onDiscard={handleDiscardSuggestion}
                            isRunning={executingSuggestionId === suggestion.id}
                          />
                        ))
                      )}
                    </div>

                    {/* Footer link: Configure suggestions */}
                    <div className="pt-2 text-right">
                      <button
                        type="button"
                        onClick={() => setView('settings')}
                        className="text-xs text-zinc-400 hover:text-zinc-200 transition-colors"
                      >
                        Configure suggestions
                      </button>
                    </div>
                  </div>
                )}

                {/* Tab 3: Scheduled */}
                {activeCardTab === 'scheduled' && (
                  <div className="pt-1">
                    <SchedulerPanel
                      compact={true}
                      selectedRepo={selectedRepo}
                      onTriggerRepo={() => fetchSessions()}
                    />
                  </div>
                )}

                {/* 6. Bottom bar of Central Card (always visible in Overview & Scheduled) */}
                {activeCardTab !== 'suggested' && (
                  <div className="pt-3 border-t border-zinc-800/80 flex flex-wrap items-center justify-between gap-2.5">
                    <span className="text-xs font-semibold text-zinc-400">
                      Schedule skill-based agents
                    </span>

                    <div className="flex items-center gap-2">
                      <button
                        type="button"
                        onClick={() => {
                          setSelectedCategory('performance');
                          setActiveCardTab('suggested');
                        }}
                        className="px-3 py-1 rounded-full text-xs font-medium bg-[#101014] hover:bg-zinc-800 border border-zinc-800 text-zinc-300 transition-colors"
                      >
                        Performance
                      </button>

                      <button
                        type="button"
                        onClick={() => {
                          setSelectedCategory('cleanup');
                          setActiveCardTab('suggested');
                        }}
                        className="px-3 py-1 rounded-full text-xs font-medium bg-[#101014] hover:bg-zinc-800 border border-zinc-800 text-zinc-300 transition-colors"
                      >
                        Design
                      </button>

                      <button
                        type="button"
                        onClick={() => {
                          setSelectedCategory('security');
                          setActiveCardTab('suggested');
                        }}
                        className="px-3 py-1 rounded-full text-xs font-medium bg-[#101014] hover:bg-zinc-800 border border-zinc-800 text-zinc-300 transition-colors"
                      >
                        Security
                      </button>
                    </div>
                  </div>
                )}
              </div>
            </div>
          )}
        </main>
      </div>

      {/* Diff and Logs Drawer */}
      <DiffDrawer
        isOpen={isDiffDrawerOpen}
        onClose={() => setIsDiffDrawerOpen(false)}
        taskId={activeTaskId}
        diff={activeTaskDiff}
        taskStatus={activeTaskStatus}
        repoName={selectedRepo}
        branchName={activeTaskBranch}
        onEscalate={handleEscalate}
        isEscalating={isEscalating}
        initialPrUrl={activeTaskPrUrl}
      />

      {/* Global Toast Container */}
      <ToastContainer toasts={toasts} onDismiss={removeToast} />
    </div>
  );
};

export default App;
