import React, { useState, useEffect, useCallback } from 'react';
import {
  Activity,
  Calendar,
  Cpu,
  Layers,
  Palette,
  RefreshCw,
  Settings,
  Shield,
  Zap,
} from 'lucide-react';
import { api, ApiError } from './api';
import type {
  EngineMode,
  HealthResponse,
  HubConfig,
  ProjectInfo,
  Suggestion,
  TaskStatus,
  ToastMessage,
  WorktreeSessionInfo,
} from './types';
import { RepoSelector } from './components/RepoSelector';
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

export const App: React.FC = () => {
  // Native tab routing ('cockpit' | 'scheduler' | 'settings') without react-router-dom
  const [activeTab, setActiveTab] = useState<'cockpit' | 'scheduler' | 'settings'>('cockpit');

  // Global Hub State
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [projects, setProjects] = useState<ProjectInfo[]>([]);
  const [selectedRepo, setSelectedRepo] = useState<string>('jules');
  const [selectedPersona, setSelectedPersona] = useState<string>('all');
  const [selectedEngine, setSelectedEngine] = useState<EngineMode>('antigravity_flash');

  // Suggestions State
  const [suggestions, setSuggestions] = useState<Suggestion[]>([]);
  const [isLoadingSuggestions, setIsLoadingSuggestions] = useState<boolean>(true);

  // Worktrees State
  const [worktrees, setWorktrees] = useState<WorktreeSessionInfo[]>([]);
  const [isLoadingWorktrees, setIsLoadingWorktrees] = useState<boolean>(false);

  // Running & Active Task State
  const [activeTaskId, setActiveTaskId] = useState<string | null>(null);
  const [activeTaskStatus, setActiveTaskStatus] = useState<TaskStatus>('pending');
  const [activeTaskDiff, setActiveTaskDiff] = useState<string | null>(null);
  const [activeTaskBranch, setActiveTaskBranch] = useState<string>('');
  const [isDiffDrawerOpen, setIsDiffDrawerOpen] = useState<boolean>(false);
  const [executingSuggestionId, setExecutingSuggestionId] = useState<string | null>(null);
  const [escalatingSuggestionId, setEscalatingSuggestionId] = useState<string | null>(null);

  // Toasts
  const [toasts, setToasts] = useState<ToastMessage[]>([]);

  const addToast = useCallback(
    (type: ToastMessage['type'], title: string, message: string) => {
      const id = `${Date.now()}_${Math.random().toString(36).substring(2, 7)}`;
      setToasts((prev) => [...prev, { id, type, title, message }]);

      // Auto dismiss after 6 seconds
      setTimeout(() => {
        setToasts((prev) => prev.filter((t) => t.id !== id));
      }, 6000);
    },
    []
  );

  const removeToast = useCallback((id: string) => {
    setToasts((prev) => prev.filter((t) => t.id !== id));
  }, []);

  // Fetch Health & Registered Projects on Mount
  useEffect(() => {
    const fetchInitialData = async () => {
      try {
        const [h, p] = await Promise.allSettled([
          api.getHealth(),
          api.getProjects(),
        ]);

        if (h.status === 'fulfilled') {
          setHealth(h.value);
        }
        if (p.status === 'fulfilled' && p.value.length > 0) {
          setProjects(p.value);
          const hasJules = p.value.some((proj) => proj.name === 'jules');
          if (!hasJules) {
            setSelectedRepo(p.value[0].name);
          }
        }
      } catch (e) {
        console.error('Error fetching initial health/projects', e);
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
        selectedPersona,
        'all'
      );
      setSuggestions(data);
    } catch (err: unknown) {
      console.error('Error fetching suggestions', err);
      const msg = err instanceof ApiError ? err.detail : 'Impossibile caricare i suggerimenti dal backend.';
      addToast('error', 'Errore Scanner', msg);
      setSuggestions([]);
    } finally {
      setIsLoadingSuggestions(false);
    }
  }, [selectedRepo, selectedPersona, addToast]);

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

  // Trigger suggestions and worktrees when repo or persona changes
  useEffect(() => {
    fetchSuggestions();
    fetchWorktrees();
  }, [fetchSuggestions, fetchWorktrees]);

  // Handle Discard Suggestion (Ignored in future scans)
  const handleDiscardSuggestion = async (suggestionId: string) => {
    try {
      await api.discardSuggestion(suggestionId);
      setSuggestions((prev) => prev.filter((s) => s.id !== suggestionId));
      addToast('info', 'Suggerimento Scartato', 'Il suggerimento è stato ignorato e non ricomparirà nelle scansioni.');
    } catch (err: unknown) {
      const msg = err instanceof ApiError ? err.detail : 'Errore durante l\'operazione di scarto.';
      // Optimistically remove from state anyway
      setSuggestions((prev) => prev.filter((s) => s.id !== suggestionId));
      addToast('warning', 'Scartato Localmente', msg);
    }
  };

  // Handle Prune Worktree
  const handlePruneWorktree = async (path?: string) => {
    try {
      const resp = await api.pruneWorktrees({ worktree_path: path, force: true });
      if (resp.success) {
        addToast(
          'success',
          'Worktree Pruned',
          path ? 'Worktree rimosso con successo.' : 'Tutti i worktree sono stati rimossi.'
        );
        fetchWorktrees();
      } else {
        addToast('warning', 'Prune Incompleto', resp.message);
      }
    } catch (err) {
      addToast('error', 'Errore Pruning', 'Impossibile rimuovere il worktree selezionato.');
    }
  };

  // Run in Jules action
  const handleRunInJules = async (suggestion: Suggestion) => {
    setExecutingSuggestionId(suggestion.id);
    try {
      addToast('info', 'Task Avviato', `Creazione worktree per ${suggestion.title}...`);

      const resp = await api.runTask({
        repo: selectedRepo || 'jules',
        persona: suggestion.persona,
        target_file: suggestion.file,
        issue_context: `${suggestion.title}: ${suggestion.issue}`,
        mode: selectedEngine,
        dry_run: false,
      });

      setActiveTaskId(resp.task_id);
      setActiveTaskStatus(resp.status);
      setActiveTaskBranch(resp.branch || `curator/${suggestion.persona}-${resp.task_id.substring(0, 6)}`);
      setActiveTaskDiff(null);
      setIsDiffDrawerOpen(true);

      // Refresh worktrees monitor
      fetchWorktrees();

      if (resp.status === 'passed') {
        addToast('success', 'Test Superati', 'Patch applicata con successo nel worktree!');
      } else if (resp.status === 'needs_escalation') {
        addToast('warning', 'Review Senior Richiesta', 'I test sono falliti nel worktree; pronto per Antigravity.');
      }
    } catch (err: unknown) {
      console.error('Error executing run task', err);
      const msg = err instanceof ApiError ? err.detail : 'Errore imprevisto durante l\'esecuzione del task.';
      addToast('error', 'Esecuzione Fallita', msg);
    } finally {
      setExecutingSuggestionId(null);
    }
  };

  // Escalate to Antigravity action
  const handleEscalate = async (suggestion?: Suggestion) => {
    const sId = suggestion ? suggestion.id : 'drawer_action';
    setEscalatingSuggestionId(sId);

    try {
      const repoName = selectedRepo || 'jules';
      const branch = activeTaskBranch || `curator/audit-${Date.now().toString().slice(-4)}`;
      const worktreePath = `/home/federico/jules/worktrees/${repoName}-${branch.replace('/', '-')}`;

      const res = await api.escalateToAntigravity({
        repo: repoName,
        worktree_path: worktreePath,
        branch: branch,
        diff_summary: suggestion ? `${suggestion.title}: ${suggestion.issue}` : 'Senior Audit Request',
        test_status: activeTaskStatus === 'passed' ? 'PASSED' : 'NEEDS_ESCALATION',
        instruction: 'Esegui audit Senior. Se approvato, apri la PR su GitHub.',
      });

      if (res.success) {
        addToast(
          'success',
          'Escalation Inviata',
          res.message || 'Worktree inviato ad Antigravity Senior Review con successo!'
        );
      } else {
        addToast(
          'error',
          'CDP 9000 Offline',
          res.message || 'Impossibile connettersi ad Antigravity Desktop sulla porta 9000. Assicurati che il debugger CDP sia attivo.'
        );
      }
    } catch (err: unknown) {
      console.error('Escalation error', err);
      addToast(
        'error',
        'CDP 9000 Non Raggiungibile',
        'Impossibile connettersi ad Antigravity Desktop sulla porta 9000. Assicurati che Antigravity sia in esecuzione con porta CDP 9000 aperta.'
      );
    } finally {
      setEscalatingSuggestionId(null);
    }
  };

  return (
    <div className="min-h-screen bg-zinc-950 text-zinc-100 flex flex-col">
      {/* Top Navigation Bar with 3 Native Tabs */}
      <header className="border-b border-zinc-800 bg-zinc-900/90 backdrop-blur sticky top-0 z-20">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
          {/* Logo & System Title */}
          <div className="flex items-center gap-4">
            <div className="flex items-center gap-2.5">
              <div className="w-8 h-8 rounded-lg bg-zinc-800 border border-zinc-700 flex items-center justify-center font-bold text-base shadow-sm">
                ⚡
              </div>
              <div>
                <div className="flex items-center gap-2">
                  <h1 className="text-base font-bold tracking-tight text-zinc-100">
                    Jules Hub
                  </h1>
                  <span className="text-[11px] font-mono px-1.5 py-0.2 rounded bg-zinc-800 text-zinc-400 border border-zinc-700/60">
                    v2.0
                  </span>
                </div>
                <div className="text-[11px] text-zinc-400">
                  Autonomous Cockpit
                </div>
              </div>
            </div>

            {/* Health pill */}
            <div className="hidden sm:flex items-center gap-1.5 px-2 py-0.5 rounded-full text-xs bg-zinc-950 border border-zinc-800">
              <span className={`w-2 h-2 rounded-full ${health ? 'bg-emerald-500 animate-pulse' : 'bg-rose-500'}`} />
              <span className="text-[11px] font-medium text-zinc-300">
                {health ? 'Backend Connesso :4100' : 'Backend Non Raggiungibile'}
              </span>
            </div>
          </div>

          {/* Native Tab Selector (role="tablist", aria-selected) */}
          <nav
            role="tablist"
            aria-label="Navigazione Principale Jules Hub v2"
            className="flex items-center gap-1 bg-zinc-950 p-1 rounded-lg border border-zinc-800"
          >
            <button
              role="tab"
              id="tab-cockpit"
              aria-selected={activeTab === 'cockpit'}
              aria-controls="panel-cockpit"
              type="button"
              onClick={() => setActiveTab('cockpit')}
              className={`flex items-center gap-2 px-3.5 py-1.5 rounded-md text-xs font-semibold transition-colors ${
                activeTab === 'cockpit'
                  ? 'bg-zinc-800 text-zinc-100 shadow-sm'
                  : 'text-zinc-400 hover:text-zinc-200'
              }`}
            >
              <Layers className="w-3.5 h-3.5" />
              <span>Cockpit</span>
            </button>

            <button
              role="tab"
              id="tab-scheduler"
              aria-selected={activeTab === 'scheduler'}
              aria-controls="panel-scheduler"
              type="button"
              onClick={() => setActiveTab('scheduler')}
              className={`flex items-center gap-2 px-3.5 py-1.5 rounded-md text-xs font-semibold transition-colors ${
                activeTab === 'scheduler'
                  ? 'bg-zinc-800 text-zinc-100 shadow-sm'
                  : 'text-zinc-400 hover:text-zinc-200'
              }`}
            >
              <Calendar className="w-3.5 h-3.5" />
              <span>Scheduler</span>
            </button>

            <button
              role="tab"
              id="tab-settings"
              aria-selected={activeTab === 'settings'}
              aria-controls="panel-settings"
              type="button"
              onClick={() => setActiveTab('settings')}
              className={`flex items-center gap-2 px-3.5 py-1.5 rounded-md text-xs font-semibold transition-colors ${
                activeTab === 'settings'
                  ? 'bg-zinc-800 text-zinc-100 shadow-sm'
                  : 'text-zinc-400 hover:text-zinc-200'
              }`}
            >
              <Settings className="w-3.5 h-3.5" />
              <span>Settings</span>
            </button>
          </nav>

          {/* Engine Selector & CDP indicator */}
          <div className="flex items-center gap-3">
            <div className="flex items-center gap-1.5 bg-zinc-950 border border-zinc-800 rounded-md px-2 py-1 text-xs">
              <Cpu className="w-3.5 h-3.5 text-zinc-400" />
              <label htmlFor="engine-select" className="text-zinc-500 text-[11px]">
                Motore:
              </label>
              <select
                id="engine-select"
                value={selectedEngine}
                onChange={(e) => setSelectedEngine(e.target.value as EngineMode)}
                className="bg-transparent text-zinc-200 font-medium focus:outline-none cursor-pointer"
              >
                <option value="antigravity_flash" className="bg-zinc-900 text-zinc-100">
                  Antigravity Flash (default)
                </option>
                <option value="local" className="bg-zinc-900 text-zinc-100">
                  Local Ollama (:11434)
                </option>
                <option value="hybrid" className="bg-zinc-900 text-zinc-100">
                  Hybrid (AST + Flash)
                </option>
              </select>
            </div>

            <div className="flex items-center gap-1.5 text-xs text-zinc-400 bg-zinc-950 border border-zinc-800 rounded-md px-2 py-1">
              <Activity className="w-3.5 h-3.5 text-zinc-500" />
              <span>CDP :9000</span>
            </div>
          </div>
        </div>
      </header>

      {/* Main Tab Panels */}
      <main className="flex-1 w-full">
        {/* Cockpit Tab Panel */}
        {activeTab === 'cockpit' ? (
          <div id="panel-cockpit" role="tabpanel" aria-labelledby="tab-cockpit" className="flex flex-col">
            {/* Filter Bar */}
            <section className="border-b border-zinc-800/80 bg-zinc-900/40">
              <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-3 flex flex-wrap items-center justify-between gap-4">
                {/* Target Workspace Selector */}
                <RepoSelector
                  projects={projects}
                  selectedRepo={selectedRepo}
                  onSelectRepo={(repo) => setSelectedRepo(repo)}
                  isLoading={isLoadingSuggestions}
                />

                {/* Persona Filter Pills */}
                <div className="flex items-center gap-1.5 bg-zinc-950 p-1 rounded-lg border border-zinc-800">
                  <button
                    type="button"
                    onClick={() => setSelectedPersona('all')}
                    className={`flex items-center gap-1 px-3 py-1 rounded text-xs font-medium transition-colors ${
                      selectedPersona === 'all'
                        ? 'bg-zinc-800 text-zinc-100 shadow-sm'
                        : 'text-zinc-400 hover:text-zinc-200'
                    }`}
                  >
                    <Layers className="w-3.5 h-3.5" />
                    Tutti
                  </button>

                  <button
                    type="button"
                    onClick={() => setSelectedPersona('bolt')}
                    className={`flex items-center gap-1 px-3 py-1 rounded text-xs font-semibold transition-colors ${
                      selectedPersona === 'bolt'
                        ? 'bg-amber-950/80 text-amber-300 border border-amber-600/60 shadow-sm'
                        : 'text-zinc-400 hover:text-amber-300'
                    }`}
                  >
                    <Zap className="w-3.5 h-3.5 text-amber-400" />
                    Bolt ⚡
                  </button>

                  <button
                    type="button"
                    onClick={() => setSelectedPersona('palette')}
                    className={`flex items-center gap-1 px-3 py-1 rounded text-xs font-semibold transition-colors ${
                      selectedPersona === 'palette'
                        ? 'bg-emerald-950/80 text-emerald-300 border border-emerald-600/60 shadow-sm'
                        : 'text-zinc-400 hover:text-emerald-300'
                    }`}
                  >
                    <Palette className="w-3.5 h-3.5 text-emerald-400" />
                    Palette 🎨
                  </button>

                  <button
                    type="button"
                    onClick={() => setSelectedPersona('sentinel')}
                    className={`flex items-center gap-1 px-3 py-1 rounded text-xs font-semibold transition-colors ${
                      selectedPersona === 'sentinel'
                        ? 'bg-rose-950/80 text-rose-300 border border-rose-600/60 shadow-sm'
                        : 'text-zinc-400 hover:text-rose-300'
                    }`}
                  >
                    <Shield className="w-3.5 h-3.5 text-rose-400" />
                    Sentinel 🛡️
                  </button>
                </div>

                {/* Refresh Action */}
                <button
                  type="button"
                  onClick={fetchSuggestions}
                  disabled={isLoadingSuggestions}
                  className="flex items-center gap-1.5 px-3 py-1.5 rounded-md text-xs font-medium bg-zinc-900 border border-zinc-800 hover:bg-zinc-800 text-zinc-300 transition-colors disabled:opacity-50"
                  title="Ricarica suggerimenti per il workspace"
                >
                  <RefreshCw className={`w-3.5 h-3.5 ${isLoadingSuggestions ? 'animate-spin' : ''}`} />
                  <span>Riesegui Scansione</span>
                </button>
              </div>
            </section>

            {/* Dashboard Workspace */}
            <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6 space-y-6">
              {/* Suggestion Board Header */}
              <div className="flex items-center justify-between">
                <div>
                  <h2 className="text-lg font-semibold text-zinc-100 flex items-center gap-2">
                    <span>Bacheca Suggerimenti Micro-Patch (&lt; 50 righe)</span>
                    {!isLoadingSuggestions ? (
                      <span className="text-xs font-mono px-2 py-0.5 rounded-full bg-zinc-800 text-zinc-300">
                        {suggestions.length}
                      </span>
                    ) : null}
                  </h2>
                  <p className="text-xs text-zinc-400 mt-0.5">
                    Identificati autonomamente dai modelli Bolt, Palette e Sentinel nei repository del sistema.
                  </p>
                </div>
              </div>

              {/* Suggestions Grid */}
              {isLoadingSuggestions ? (
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
                  <SuggestionSkeleton />
                  <SuggestionSkeleton />
                  <SuggestionSkeleton />
                </div>
              ) : suggestions.length === 0 ? (
                <SuggestionEmptyState
                  repoName={selectedRepo}
                  onRefresh={fetchSuggestions}
                />
              ) : (
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
                  {suggestions.map((suggestion) => (
                    <SuggestionCard
                      key={suggestion.id}
                      suggestion={suggestion}
                      onRunInJules={handleRunInJules}
                      onEscalateToAntigravity={handleEscalate}
                      onDiscard={handleDiscardSuggestion}
                      isRunning={executingSuggestionId === suggestion.id}
                      isEscalating={escalatingSuggestionId === suggestion.id}
                    />
                  ))}
                </div>
              )}

              {/* Worktree Monitor Section */}
              <div className="pt-4">
                <WorktreeList
                  worktrees={worktrees}
                  onPrune={handlePruneWorktree}
                  onRefresh={fetchWorktrees}
                  isLoading={isLoadingWorktrees}
                />
              </div>
            </div>
          </div>
        ) : null}

        {/* Scheduler Tab Panel */}
        {activeTab === 'scheduler' ? (
          <div id="panel-scheduler" role="tabpanel" aria-labelledby="tab-scheduler" className="py-6">
            <SchedulerPanel
              onTriggerRepo={(repo) => {
                addToast('info', 'Trigger Schedulatore', `Ciclo di scansione per ${repo} avviato.`);
                fetchWorktrees();
              }}
            />
          </div>
        ) : null}

        {/* Settings Tab Panel */}
        {activeTab === 'settings' ? (
          <div id="panel-settings" role="tabpanel" aria-labelledby="tab-settings" className="py-6">
            <SettingsView
              onSaveConfig={(_cfg: HubConfig) => {
                addToast('success', 'Configurazione Aggiornata', 'Impostazioni hub salvate con successo.');
              }}
            />
          </div>
        ) : null}
      </main>

      {/* Diff & Live SSE Streaming Drawer with Senior Gate */}
      <DiffDrawer
        isOpen={isDiffDrawerOpen}
        onClose={() => setIsDiffDrawerOpen(false)}
        taskId={activeTaskId}
        diff={activeTaskDiff}
        taskStatus={activeTaskStatus}
        repoName={selectedRepo || 'jules'}
        branchName={activeTaskBranch}
        onEscalate={() => handleEscalate()}
        isEscalating={escalatingSuggestionId === 'drawer_action'}
        onPrCreated={(prUrl) => {
          addToast('success', 'Pull Request Aperta', `PR creata con successo: ${prUrl}`);
        }}
      />

      {/* Toast Notification Stack */}
      <ToastContainer toasts={toasts} onDismiss={removeToast} />

      {/* Footer */}
      <footer className="border-t border-zinc-800 bg-zinc-950 py-4 text-center text-xs text-zinc-500">
        Jules Hub v2 — Autonomous Cockpit &bull; Senior Review Gate &bull; Quota Shield Active
      </footer>
    </div>
  );
};

export default App;
